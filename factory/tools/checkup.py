"""Mechanical checks of the Fernhill data product standards, run through checkup.

``check()`` is the rule logic: it reads ``target/manifest.json`` and returns
violations of the rules in ``standards/data-product-standards.md`` that can be
verified mechanically. It is exposed to checkup as metrics in
``factory/checkup_plugin.py`` and configured in ``warehouse/checkup.yaml``, so
the governance agent (and you) run the real thing::

    cd warehouse && dbt parse && checkup run --tag data_product=category_performance

Rules that need judgement (PII, naming of measures, business rules, dashboards)
are left to the governance agent - that is the point of the governance track.
``run()`` returns the same findings as structured JSON for tests and graders.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

MECHANICAL_RULES = ["GOV-001", "GOV-002", "GOV-003", "GOV-004", "GOV-005", "GOV-007", "GOV-009"]


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


def check(manifest: dict, product: str | None = None) -> list[Finding]:
    findings: list[Finding] = []
    tests = _tests_by_model(manifest)
    for node in _mart_models(manifest, product):
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
    return findings


def run(project_dir: Path, product: str | None = None) -> dict:
    manifest_path = project_dir / "target" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} not found - run `dbt parse` in {project_dir} first")
    findings = check(json.loads(manifest_path.read_text()), product)
    return {
        "product": product,
        "checked_rules": MECHANICAL_RULES,
        "not_checked": ["GOV-006", "GOV-008", "GOV-010", "GOV-011"],
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
