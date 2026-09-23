"""Unit tests for evaluation/select_final.py's ranking logic (User Story 3,
spec FR-006)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evaluation"))
import select_final  # noqa: E402


@pytest.fixture(autouse=True)
def _fake_submissions(tmp_path, monkeypatch):
    """rank_candidates only considers versions with a real bundled
    submissions/<version>/main.py (see select_final._is_submittable) --
    fake one for every version name these tests use, in an isolated
    tmp_path rather than the real repo's submissions/ directory."""
    submissions_dir = tmp_path / "submissions"
    for version in ("v1", "v2", "v3", "v4"):
        version_dir = submissions_dir / version
        version_dir.mkdir(parents=True)
        (version_dir / "main.py").write_text("def agent(obs): return {'farmer': ['PASS']}")
    monkeypatch.setattr(select_final, "SUBMISSIONS_DIR", submissions_dir)


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


def _entry_with_opponents(version, opponent_results):
    return {
        "agent_version": version,
        "commit_sha": f"sha-{version}",
        "evaluation_results": opponent_results,
        "kaggle_result": None,
        "decision": "investigate",
    }


def test_rank_candidates_excludes_self_play_from_the_ranking_signal():
    """Regression test: v3's logged self-play opponent was v2 (which it
    dominated, 100% win-rate), while v4's was v3 itself (a harder, more
    similar direct predecessor, ~33% win-rate) -- purely an artifact of
    which predecessor each happened to be evaluated against, not a sign
    v4 (which fixes a real bug and is never worse than v3) is actually
    worse. Self-play results must not drag the ranking down for this."""
    fixed_100 = [{"opponent": name, "win_rate": 1.0, "mean_money": 18000, "opponent_mean_money": 3000} for name in ("random", "starter", "greedy")]
    v3 = _entry_with_opponents(
        "v3",
        fixed_100 + [{"opponent": "submissions/v2/main.py", "win_rate": 1.0, "mean_money": 17000, "opponent_mean_money": 6000}],
    )
    v4 = _entry_with_opponents(
        "v4",
        fixed_100 + [{"opponent": "submissions/v3/main.py", "win_rate": 0.33, "mean_money": 18000, "opponent_mean_money": 18000}],
    )
    ranked = select_final.rank_candidates([v3, v4])
    assert ranked[0]["agent_version"] in ("v3", "v4")  # tied on the reference-only signal, either order is fine
    assert select_final._reference_win_rate(v4) == 1.0  # the point: v4 isn't penalized for a hard self-play opponent


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


def test_rank_candidates_excludes_versions_with_no_bundled_submission(tmp_path):
    """Regression test: a dev-phase evaluation run logged under a
    throwaway label like "v7-dev" (before the real v7 bundle existed)
    once outranked the real "v7" by tiebreak noise between two separate
    batch runs -- and `make submit`/`mark_final` would then point at a
    version with no submissions/<version>/main.py to actually submit."""
    entries = [
        _entry("v7-dev", win_rate=1.0, mean_money=99999, opponent_mean_money=0),  # would win on paper
        _entry("v1", win_rate=0.9, mean_money=5000, opponent_mean_money=1000),
    ]
    ranked = select_final.rank_candidates(entries)
    assert [e["agent_version"] for e in ranked] == ["v1"]  # v7-dev excluded: no submissions/v7-dev/main.py


def test_mark_final_appends_a_decision_record(tmp_path):
    log_path = tmp_path / "log.jsonl"
    log_path.write_text(json.dumps(_entry("v1", 0.5)) + "\n")
    select_final.mark_final("v1", "best local win-rate", log_path=log_path)
    entries = select_final.load_entries(log_path)
    assert len(entries) == 2  # appended, not overwritten
    assert entries[-1]["decision"] == "adopt"
    assert entries[-1]["agent_version"] == "v1"
    assert "best local win-rate" in entries[-1]["hypothesis"]


def test_rank_prefers_newer_version_when_reference_bench_is_saturated():
    """Regression test: once every candidate beats the fixed bench 100%,
    that bench has stopped discriminating. Ranking then fell through to
    money margin against those same saturated opponents and put v8 above
    v9 -- even though v9 beat v8 directly across three batches."""
    fixed = [{"opponent": n, "win_rate": 1.0, "mean_money": m, "opponent_mean_money": 3000}
             for n, m in (("random", 49000), ("starter", 39000), ("greedy", 43000))]
    older = _entry_with_opponents("v3", fixed + [
        {"opponent": "submissions/v2/main.py", "win_rate": 1.0, "mean_money": 27000, "opponent_mean_money": 16000}])
    # Newer wins its head-to-head, but by a slimmer margin against a much
    # stronger predecessor, and with lower money vs the weak bench.
    newer_fixed = [{"opponent": n, "win_rate": 1.0, "mean_money": m, "opponent_mean_money": 3000}
                   for n, m in (("random", 35000), ("starter", 41000), ("greedy", 40000))]
    newer = _entry_with_opponents("v4", newer_fixed + [
        {"opponent": "submissions/v3/main.py", "win_rate": 0.57, "mean_money": 26000, "opponent_mean_money": 23000}])
    ranked = select_final.rank_candidates([older, newer])
    assert ranked[0]["agent_version"] == "v4"


def test_rank_does_not_promote_a_version_that_lost_its_head_to_head():
    """A version measured head-to-head and beaten should not outrank the
    predecessor it failed against, however new it is."""
    fixed = [{"opponent": n, "win_rate": 1.0, "mean_money": 40000, "opponent_mean_money": 3000}
             for n in ("random", "starter", "greedy")]
    incumbent = _entry_with_opponents("v3", list(fixed))
    challenger = _entry_with_opponents("v4", fixed + [
        {"opponent": "submissions/v3/main.py", "win_rate": 0.25, "mean_money": 9000, "opponent_mean_money": 30000}])
    ranked = select_final.rank_candidates([incumbent, challenger])
    assert ranked[0]["agent_version"] == "v3"


def test_real_leaderboard_scores_decide_when_both_versions_have_them():
    """v9 beat v8 57-65% in local self-play but scored 363.3 against v8's
    430.5 on the real leaderboard (v9's feed-growing shrinks the herd,
    and herd size drives real results). When BOTH candidates have real
    scores, that direct comparison must outrank the local proxy."""
    fixed = [{"opponent": n, "win_rate": 1.0, "mean_money": 40000, "opponent_mean_money": 3000}
             for n in ("random", "starter", "greedy")]
    older = _entry_with_opponents("v3", list(fixed))
    older["kaggle_result"] = {"public_score": 430.5}
    newer = _entry_with_opponents("v4", fixed + [
        {"opponent": "submissions/v3/main.py", "win_rate": 0.65, "mean_money": 27000, "opponent_mean_money": 24000}])
    newer["kaggle_result"] = {"public_score": 363.3}
    ranked = select_final.rank_candidates([older, newer])
    assert ranked[0]["agent_version"] == "v3"


def test_local_evidence_still_wins_when_the_newer_version_is_untested():
    """The narrower rule must not resurrect the old bug where any stale
    real score outranked an untested but locally-dominant newer version."""
    fixed = [{"opponent": n, "win_rate": 1.0, "mean_money": 40000, "opponent_mean_money": 3000}
             for n in ("random", "starter", "greedy")]
    older = _entry_with_opponents("v3", list(fixed))
    older["kaggle_result"] = {"public_score": 430.5}
    newer = _entry_with_opponents("v4", fixed + [
        {"opponent": "submissions/v3/main.py", "win_rate": 0.8, "mean_money": 30000, "opponent_mean_money": 20000}])
    ranked = select_final.rank_candidates([older, newer])  # newer has no real score yet
    assert ranked[0]["agent_version"] == "v4"
