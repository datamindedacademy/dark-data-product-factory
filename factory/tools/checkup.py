"""Mechanical checks of the Fernhill data product standards, run through checkup.

``check()`` is the rule logic: it reads ``target/manifest.json`` and returns
violations of the rules in ``standards/data-product-standards.md`` that can be
verified mechanically. It is exposed to checkup as metrics in
``factory/checkup_plugin.py`` and configured in ``warehouse/checkup.yaml``, so
the governance agent (and you) run the real thing::

    cd warehouse && dbt parse && checkup run --tag data_product=category_performance

GOV-006, 008 and 010 are also checked here, as heuristics (``JUDGEMENT_RULES``): by column
name, by test and by the board's ``ref()``s. They are
*not* in ``warehouse/checkup.yaml``, so the governance agent does not get them for free: finding
PII, unit and dashboard problems is still the governance track (enabling these metrics is one
of its levers). GOV-011 (business rules) stays judgement; the final's oracle checks it as SQL.
``run()`` returns the findings as structured JSON; by default only the mechanical rules, like the
agents' checkup.yaml. The final's grader (``factory/competition.py``) asks for all of them.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

MECHANICAL_RULES = ["GOV-001", "GOV-002", "GOV-003", "GOV-004", "GOV-005", "GOV-007", "GOV-009"]
JUDGEMENT_RULES = ["GOV-006", "GOV-008", "GOV-010"]

# ponytail: name heuristics. A PII column called `contact` or a money column called `total` slips through.
_PII = re.compile(r"(^|_)(e_?mail|first_name|last_name|full_name|customer_name|phone|street|address|ip_address)($|_)")
_MONEY = re.compile(r"(^|_)(revenue|amount|price|cost|spend|refund|refunds|margin|sales|fee)$")
_RATIO = re.compile(r"_(rate|pct)$")
_REF = re.compile(r"""ref\(\s*['"]([A-Za-z0-9_]+)['"]\s*\)""")


@dataclass
class Finding:
    rule_id: str
    model: str
    column: str | None
    message: str


def _mart_models(manifest: dict, product: str | None) -> list[dict]:
    out = []
    for node in manifest["nodes"].values():
        if node["resource_type"] != "model":
            continue
        fqn = node["fqn"]
        if len(fqn) < 3 or fqn[1] != "marts":
            continue
        meta = node.get("config", {}).get("meta", {}) or node.get("meta", {})
        folder = fqn[2]
        if product and folder != product and meta.get("data_product") != product:
            continue
        out.append(node)
    return out


def _tests_by_model(manifest: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for node in manifest["nodes"].values():
        if node["resource_type"] != "test":
            continue
        attached = node.get("attached_node") or (node.get("depends_on", {}).get("nodes") or [None])[0]
        if attached:
            out.setdefault(attached, []).append(node)
    return out


def _ratio_tested(tests: list[dict], column: str) -> bool:
    for t in tests:
        tm = t.get("test_metadata") or {}
        kw = tm.get("kwargs") or {}
        if tm.get("name") == "accepted_range" and kw.get("column_name") == column and \
                kw.get("min_value") is not None and kw.get("max_value") is not None and \
                0 <= float(kw["min_value"]) and float(kw["max_value"]) <= 1:
            return True
    return False


def _check_board(charts_dir: Path, product: str, models: set[str]) -> list[Finding]:
    import yaml

    path = charts_dir / f"{product}.yml"
    try:
        board = yaml.safe_load(path.read_text()) or {}
    except (OSError, yaml.YAMLError) as exc:
        return [Finding("GOV-010", product, None, f"no readable board {path.name}: {type(exc).__name__}")]
    queries = board.get("queries") if isinstance(board, dict) else None
    if not isinstance(queries, dict) or not queries:
        return [Finding("GOV-010", product, None, "board has no queries")]
    return [Finding("GOV-010", product, None, f"board query {q} does not read the product's own models")
            for q, d in queries.items()
            if not (isinstance(d, dict) and set(_REF.findall(str(d.get("sql", "")))) & models)]


def check(manifest: dict, product: str | None = None, charts_dir: Path | None = None) -> list[Finding]:
    """Violations in the product's mart models. ``charts_dir`` (with ``product``) also checks GOV-010."""
    findings: list[Finding] = []
    tests = _tests_by_model(manifest)
    marts = _mart_models(manifest, product)
    for node in marts:
        name = node["name"]
        cfg = node.get("config", {})
        meta = cfg.get("meta", {}) or node.get("meta", {})
        cols: dict[str, Any] = node.get("columns", {})

        if not (name.startswith("fct_") or name.startswith("dim_")):
            findings.append(Finding("GOV-001", name, None, "mart model name must start with fct_ or dim_"))
        if len((node.get("description") or "").strip()) < 30:
            findings.append(Finding("GOV-002", name, None, "model description missing or shorter than 30 characters"))
        for cname, c in cols.items():
            if not (c.get("description") or "").strip():
                findings.append(Finding("GOV-003", name, cname, "column has no description"))

        grain = meta.get("grain")
        model_tests = tests.get(node["unique_id"], [])
        if not grain:
            findings.append(Finding("GOV-004", name, None, "meta.grain is not declared"))
        else:
            grain = [grain] if isinstance(grain, str) else list(grain)
            enforced = False
            for t in model_tests:
                tm = t.get("test_metadata") or {}
                kwargs = tm.get("kwargs", {})
                if tm.get("name") == "unique" and len(grain) == 1 and kwargs.get("column_name") == grain[0]:
                    enforced = True
                if tm.get("name") == "unique_combination_of_columns" and \
                        sorted(kwargs.get("combination_of_columns") or []) == sorted(grain):
                    enforced = True
            if not enforced:
                findings.append(Finding("GOV-004", name, None, f"no unique / unique_combination_of_columns test enforces grain {grain}"))

        for key in ("owner", "data_product"):
            if not meta.get(key):
                findings.append(Finding("GOV-005", name, None, f"meta.{key} is missing"))

        if not (cfg.get("contract") or {}).get("enforced"):
            findings.append(Finding("GOV-007", name, None, "contract is not enforced"))
        else:
            for cname, c in cols.items():
                if not c.get("data_type"):
                    findings.append(Finding("GOV-007", name, cname, "column has no data_type"))

        for dep in node.get("depends_on", {}).get("nodes", []):
            if dep.startswith("source."):
                findings.append(Finding("GOV-009", name, None, f"selects directly from {dep}"))

        if node["fqn"][2] != "core":  # only `core` may expose personal data
            for cname, c in cols.items():
                if _PII.search(cname.lower()) or (c.get("meta") or {}).get("pii"):
                    findings.append(Finding("GOV-006", name, cname, "data product exposes a personal data column"))
        for cname in cols:
            if _RATIO.search(cname) and not _ratio_tested(model_tests, cname):
                findings.append(Finding("GOV-008", name, cname, "ratio without an accepted_range test within 0..1"))
            elif not _RATIO.search(cname) and _ratio_tested(model_tests, cname):
                findings.append(Finding("GOV-008", name, cname, "ratio (range 0..1) without _rate or _pct suffix"))
            elif _MONEY.search(cname):
                findings.append(Finding("GOV-008", name, cname, "monetary column without currency suffix (_eur)"))
    if charts_dir is not None and product and product != "core":
        findings += _check_board(charts_dir, product, {n["name"] for n in marts})
    return findings


def run(project_dir: Path, product: str | None = None, rules: list[str] = MECHANICAL_RULES) -> dict:
    """Findings for ``rules``. The default is what the agents' checkup.yaml checks; the final's grader passes
    ``MECHANICAL_RULES + JUDGEMENT_RULES`` (GOV-010 also needs ``charts/<product>.yml``, so not before bi ran)."""
    manifest_path = project_dir / "target" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} not found - run `dbt parse` in {project_dir} first")
    charts = project_dir / "charts" if "GOV-010" in rules else None
    findings = [f for f in check(json.loads(manifest_path.read_text()), product, charts) if f.rule_id in rules]
    return {
        "product": product,
        "checked_rules": list(rules),
        "not_checked": [r for r in MECHANICAL_RULES + JUDGEMENT_RULES + ["GOV-011"] if r not in rules],
        "violations": [asdict(f) for f in findings],
    }


def checkup_cli(project_dir: Path, product: str | None = None, materializer: str = "markdown"):
    """Run ``checkup run`` in the dbt project (uses ``checkup.yaml`` there)."""
    from factory import paths
    from factory.workspace import sh

    cmd = [paths.tool("checkup"), "run", "-q", "--no-multiprocessing", "--materializer", materializer]
    if product:
        cmd += ["--tag", f"data_product={product}"]
    return sh(cmd, project_dir, check=False)


def build_server(project_dir: Path):
    """MCP server exposing checkup to agents."""
    from factory.workspace import dbt  # local import to avoid a cycle

    @tool("checkup",
          "Run checkup (computational governance) on the dbt project with warehouse/checkup.yaml: "
          "project health metrics from checkup-dbt plus one metric per mechanical Fernhill rule "
          "(GOV-001..005, 007, 009; value = number of violations, diagnostics list model or model.column). "
          "Re-parses the project first. Pass `product` to scope the Fernhill rules to one data product. "
          "GOV-006, 008, 010 and 011 are not covered.",
          {"product": str})
    async def checkup(args: dict[str, Any]) -> dict[str, Any]:
        parsed = dbt(project_dir.parent, "parse", "--quiet")
        if parsed.returncode != 0:
            return {"content": [{"type": "text", "text": "dbt parse failed:\n" + parsed.stdout[-3000:]}], "is_error": True}
        res = checkup_cli(project_dir, args.get("product") or None)
        if res.returncode != 0 or not res.stdout.strip():
            return {"content": [{"type": "text", "text": "checkup failed:\n" + (res.stdout + res.stderr)[-3000:]}],
                    "is_error": True}
        return {"content": [{"type": "text", "text": res.stdout}]}

    return create_sdk_mcp_server("governance", tools=[checkup])
