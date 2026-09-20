"""Integration test for self-play comparison (User Story 2, FR-002): a
candidate agent evaluated against the previously submitted version, using
the real submissions/v1/main.py bundle produced by User Story 1 as the
'previous' opponent.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "evaluation"))
import run_batch  # noqa: E402

AGENT_PATH = str(REPO_ROOT / "src" / "kaggriculture_agent" / "agent.py")


def test_previous_opponent_resolves_to_a_real_submitted_bundle():
    resolved = run_batch.resolve_opponent("previous")
    assert Path(resolved).exists(), "expected a real submissions/v*/main.py from User Story 1"
    assert Path(resolved).name == "main.py"


def test_self_play_batch_runs_and_reports_a_result():
    result = run_batch.run_batch(AGENT_PATH, "previous", seasons=2)
    assert result["seasons"] == 2
    assert result["wins"] + result["losses"] + result["ties"] == 2
    assert 0.0 <= result["win_rate"] <= 1.0
