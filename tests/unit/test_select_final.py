"""Unit tests for evaluation/select_final.py's ranking logic (User Story 3,
spec FR-006)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evaluation"))
import select_final  # noqa: E402


def _entry(version, win_rate, public_score=None, evaluation_results=True, mean_money=0, opponent_mean_money=0):
    entry = {
        "agent_version": version,
        "commit_sha": f"sha-{version}",
        "evaluation_results": [
            {
                "opponent": "starter",
                "wins": 1,
                "losses": 0,
                "ties": 0,
                "win_rate": win_rate,
                "mean_money": mean_money,
                "opponent_mean_money": opponent_mean_money,
            }
        ]
        if evaluation_results
        else [],
        "kaggle_result": {"public_score": public_score} if public_score is not None else None,
        "decision": "investigate",
    }
    return entry


def test_rank_candidates_prefers_higher_local_win_rate_even_over_leaderboard_evidence():
    """Regression test: an earlier version of this ranking put ANY
    candidate with a real kaggle_result ahead of every local-only
    candidate regardless of local win-rate. That's exactly the bug that
    made `make submit` keep recommending a known-weak, already-submitted
    v2 (public_score=389.9) over a locally-dominant, unsubmitted v3."""
    entries = [
        _entry("v1", win_rate=0.5, public_score=1000),
        _entry("v2", win_rate=0.95, public_score=None),  # better local, never actually submitted
    ]
    ranked = select_final.rank_candidates(entries)
    assert ranked[0]["agent_version"] == "v2"


def test_rank_candidates_breaks_win_rate_ties_by_average_money_margin():
    entries = [
        _entry("v1", win_rate=1.0, mean_money=6000, opponent_mean_money=3000),  # margin 3000
        _entry("v2", win_rate=1.0, mean_money=18000, opponent_mean_money=3000),  # margin 15000
    ]
    ranked = select_final.rank_candidates(entries)
    assert [e["agent_version"] for e in ranked] == ["v2", "v1"]


def test_rank_candidates_falls_back_to_local_win_rate_when_no_leaderboard_data():
    entries = [_entry("v1", win_rate=0.6), _entry("v2", win_rate=0.9)]
    ranked = select_final.rank_candidates(entries)
    assert [e["agent_version"] for e in ranked] == ["v2", "v1"]


def test_rank_candidates_uses_latest_entry_per_version():
    entries = [_entry("v1", win_rate=0.3), _entry("v1", win_rate=0.8)]
    ranked = select_final.rank_candidates(entries)
    assert len(ranked) == 1
    assert select_final.average_win_rate(ranked[0]) == 0.8


def test_rank_candidates_handles_empty_log():
    assert select_final.rank_candidates([]) == []


def test_load_entries_reads_jsonl(tmp_path):
    log_path = tmp_path / "log.jsonl"
    log_path.write_text(json.dumps(_entry("v1", 0.5)) + "\n" + json.dumps(_entry("v2", 0.6)) + "\n")
    entries = select_final.load_entries(log_path)
    assert [e["agent_version"] for e in entries] == ["v1", "v2"]


def test_load_entries_missing_file_returns_empty_list(tmp_path):
    assert select_final.load_entries(tmp_path / "nope.jsonl") == []


def test_mark_final_appends_a_decision_record(tmp_path):
    log_path = tmp_path / "log.jsonl"
    log_path.write_text(json.dumps(_entry("v1", 0.5)) + "\n")
    select_final.mark_final("v1", "best local win-rate", log_path=log_path)
    entries = select_final.load_entries(log_path)
    assert len(entries) == 2  # appended, not overwritten
    assert entries[-1]["decision"] == "adopt"
    assert entries[-1]["agent_version"] == "v1"
    assert "best local win-rate" in entries[-1]["hypothesis"]
