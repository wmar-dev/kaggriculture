"""Unit tests for evaluation/run_batch.py's aggregation and opponent
resolution logic (spec FR-002/FR-003, User Story 2)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evaluation"))
import run_batch  # noqa: E402


def test_outcome_win_loss_tie():
    assert run_batch._outcome(100, 50, "DONE") == "win"
    assert run_batch._outcome(50, 100, "DONE") == "loss"
    assert run_batch._outcome(50, 50, "DONE") == "tie"


def test_outcome_forfeits_on_bad_status():
    # Even a money lead doesn't count as a win if our own agent crashed/timed out.
    assert run_batch._outcome(999, 0, "ERROR") == "loss"
    assert run_batch._outcome(999, 0, "INVALID") == "loss"
    assert run_batch._outcome(999, 0, "TIMEOUT") == "loss"


def test_resolve_opponent_builtins_passthrough():
    assert run_batch.resolve_opponent("random") == "random"
    assert run_batch.resolve_opponent("starter") == "starter"
    assert run_batch.resolve_opponent("pass") == "pass"


def test_resolve_opponent_greedy_maps_to_file():
    resolved = run_batch.resolve_opponent("greedy")
    assert resolved.endswith("evaluation/opponents/greedy_agent.py")


def test_resolve_opponent_explicit_path_passthrough():
    assert run_batch.resolve_opponent("some/custom/path.py") == "some/custom/path.py"


def test_resolve_opponent_previous_picks_highest_version(tmp_path):
    submissions = tmp_path / "submissions"
    (submissions / "v1").mkdir(parents=True)
    (submissions / "v1" / "main.py").write_text("def agent(obs): return {'farmer': ['PASS']}")
    (submissions / "v2").mkdir(parents=True)
    (submissions / "v2" / "main.py").write_text("def agent(obs): return {'farmer': ['PASS']}")
    (submissions / "v10").mkdir(parents=True)
    (submissions / "v10" / "main.py").write_text("def agent(obs): return {'farmer': ['PASS']}")

    with patch.object(run_batch, "SUBMISSIONS_DIR", submissions):
        resolved = run_batch.resolve_opponent("previous")
    assert resolved == str(submissions / "v10" / "main.py")


def test_resolve_opponent_previous_raises_when_no_submissions(tmp_path):
    with patch.object(run_batch, "SUBMISSIONS_DIR", tmp_path / "submissions"):
        try:
            run_batch.resolve_opponent("previous")
            assert False, "expected FileNotFoundError"
        except FileNotFoundError:
            pass


def _entry(version, win_rate, public_score=None):
    entry = {
        "agent_version": version,
        "evaluation_results": [{"opponent": "starter", "win_rate": win_rate}],
        "kaggle_result": None,
    }
    if public_score is not None:
        entry["kaggle_result"] = {"public_score": public_score}
    return entry


def test_average_win_rate():
    assert run_batch.average_win_rate(_entry("v1", 0.6)) == 0.6
    assert run_batch.average_win_rate({"evaluation_results": []}) == 0.0


def test_check_divergence_ignores_unsubmitted_entries():
    entries = [_entry("v1", 0.5), _entry("v2", 0.9)]  # neither has a kaggle_result
    assert run_batch.check_divergence(entries) == []


def test_check_divergence_flags_disagreement():
    entries = [
        _entry("v1", 0.5, public_score=100),
        _entry("v2", 0.8, public_score=80),  # local improved, leaderboard got worse
    ]
    warnings = run_batch.check_divergence(entries)
    assert len(warnings) == 1
    assert "v1" in warnings[0] and "v2" in warnings[0]


def test_check_divergence_silent_when_trends_agree():
    entries = [
        _entry("v1", 0.5, public_score=100),
        _entry("v2", 0.8, public_score=150),
    ]
    assert run_batch.check_divergence(entries) == []


def test_run_batch_alternates_seats():
    """Regression test: the two player slots are NOT symmetric -- running
    v8 against a byte-identical copy of itself, player 0 won only 3 of 14
    despite near-identical mean money, and a by-seat breakdown showed
    3W-4L as player 0 vs 6W-2L as player 1. Measuring every season from
    the same seat biased self-play win rates by roughly 30 points, more
    than most real effects this harness is used to detect."""
    seatings = []

    class _FakeState:
        def __init__(self, reward):
            self.reward = reward
            self.status = "DONE"

    class _FakeEnv:
        def run(self, agents):
            seatings.append(list(agents))
            # Constant rewards; we only care which slot the agent landed in.
            self.steps = [[_FakeState(100.0), _FakeState(50.0)]]

    with patch("kaggle_environments.make", lambda *a, **k: _FakeEnv()):
        run_batch.run_batch("AGENT.py", "OPPONENT.py", seasons=4)

    assert seatings[0] == ["AGENT.py", "OPPONENT.py"]
    assert seatings[1] == ["OPPONENT.py", "AGENT.py"]
    assert seatings[2] == ["AGENT.py", "OPPONENT.py"]
    assert seatings[3] == ["OPPONENT.py", "AGENT.py"]


def test_run_batch_scores_from_the_correct_seat_when_playing_as_player_1():
    """When the agent is seated as player 1, the win/loss accounting must
    read ITS reward, not player 0's."""

    class _FakeState:
        def __init__(self, reward):
            self.reward = reward
            self.status = "DONE"

    class _FakeEnv:
        def run(self, agents):
            # player0 always scores 10, player1 always scores 999
            self.steps = [[_FakeState(10.0), _FakeState(999.0)]]

    with patch("kaggle_environments.make", lambda *a, **k: _FakeEnv()):
        result = run_batch.run_batch("AGENT.py", "OPPONENT.py", seasons=2)

    # Season 0: agent is player0 (scores 10) -> loss.
    # Season 1: agent is player1 (scores 999) -> win.
    assert result["wins"] == 1
    assert result["losses"] == 1
