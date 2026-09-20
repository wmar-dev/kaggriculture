"""Unit tests for evaluation/bundle_submission.py's import-stripping and
last-callable safety check.

Regression coverage for a real bug hit during v3 development: the
stripper only handled single-line `from kaggriculture_agent.X import Y`
statements, so strategy.py's multi-line parenthesized import left
orphaned continuation lines and produced a bundle with a SyntaxError.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evaluation"))
import bundle_submission  # noqa: E402


def test_strip_module_removes_future_import():
    source = "from __future__ import annotations\n\nx = 1\n"
    assert "from __future__" not in bundle_submission._strip_module(source)


def test_strip_module_removes_single_line_local_import():
    source = "from kaggriculture_agent.constants import CROPS\n\nx = CROPS\n"
    stripped = bundle_submission._strip_module(source)
    assert "from kaggriculture_agent" not in stripped
    assert "x = CROPS" in stripped


def test_strip_module_removes_multiline_parenthesized_local_import():
    source = (
        "from kaggriculture_agent.constants import (\n"
        "    ANIMALS,\n"
        "    CROPS,\n"
        "    yield_per_tile_per_day,\n"
        ")\n"
        "\n"
        "x = CROPS\n"
    )
    stripped = bundle_submission._strip_module(source)
    assert "from kaggriculture_agent" not in stripped
    assert "ANIMALS," not in stripped  # the orphaned-continuation-line bug
    import ast

    ast.parse(stripped)  # must be valid Python on its own
    assert "x = CROPS" in stripped


def test_build_bundle_produces_valid_python_with_agent_last():
    import ast

    source = bundle_submission.build_bundle()
    ast.parse(source)
    assert bundle_submission._last_callable_name(source) == "agent"
