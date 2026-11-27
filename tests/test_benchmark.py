"""Every benchmark case is valid: doing nothing scores 0, the right answer scores 1."""

import pytest

from factory import paths
from factory.competition import valid_case


@pytest.mark.parametrize("case", sorted(paths.CASES.glob("*/*.yaml")), ids=lambda p: p.stem)
def test_case_is_valid(case):
    ok, why = valid_case(case)
    assert ok, why

