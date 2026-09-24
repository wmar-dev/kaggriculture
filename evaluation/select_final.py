"""Deliberate final-submission selection (User Story 3, spec FR-006).

Reads experiments/log.jsonl and ranks candidate agent versions so the
competitor can choose a final submission backed by recorded evidence,
rather than whichever version happened to run last (constitution
Principle I / Workflow & Submission Discipline).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from functools import cmp_to_key
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "experiments" / "log.jsonl"
SUBMISSIONS_DIR = REPO_ROOT / "submissions"

sys.path.insert(0, str(REPO_ROOT / "evaluation"))
from run_batch import _commit_sha, average_win_rate  # noqa: E402


def load_entries(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    with log_path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def _is_submittable(version: str) -> bool:
    """True only if `submissions/<version>/main.py` actually exists.

    Development-phase evaluation runs are sometimes logged under a
    throwaway label (e.g. "v7-dev") before the real bundle is built and
    evaluated under its real version name -- without this check, such a
    label could still win the ranking on a lucky batch (confirmed
    happening: "v7-dev" outranked "v7" by tiebreak noise between two
    separate batch runs) and `make submit`/`mark_final` would then point
    at a version with no bundle to actually submit.
    """
    return (SUBMISSIONS_DIR / version / "main.py").exists()


def _merge_results(results: list[dict]) -> list[dict]:
    """Pool per-opponent results, summing the underlying game counts."""
    by_opponent: dict[str, dict] = {}
    for r in results:
        acc = by_opponent.setdefault(
            r["opponent"],
            {"opponent": r["opponent"], "seasons": 0, "wins": 0, "losses": 0, "ties": 0,
             "_money": 0.0, "_opp_money": 0.0},
        )
        # Older records predate the `seasons` field; the game counts are
        # the source of truth either way.
        seasons = r.get("seasons") or (r.get("wins", 0) + r.get("losses", 0) + r.get("ties", 0))
        acc["seasons"] += seasons
        acc["wins"] += r.get("wins", 0)
        acc["losses"] += r.get("losses", 0)
        acc["ties"] += r.get("ties", 0)
        acc["_money"] += r.get("mean_money", 0.0) * seasons
        acc["_opp_money"] += r.get("opponent_mean_money", 0.0) * seasons
    merged = []
    for acc in by_opponent.values():
        seasons = acc["seasons"] or 1
        merged.append({
            "opponent": acc["opponent"],
            "seasons": acc["seasons"],
            "wins": acc["wins"],
            "losses": acc["losses"],
            "ties": acc["ties"],
            "win_rate": acc["wins"] / seasons,
            "mean_money": acc["_money"] / seasons,
            "opponent_mean_money": acc["_opp_money"] / seasons,
        })
    return merged


def _latest_per_version(entries: list[dict]) -> list[dict]:
    """One merged record per candidate version.

    A version's bundle is FROZEN once written, so every run logged
    against it tests the same agent and the runs are independent samples
    of one quantity. They are therefore POOLED, not superseded.

    Superseding was a real bug: v14 was evaluated 100% against the fixed
    bench in one run and head-to-head against v13 in later runs, and
    because the last entry won, the bench evidence was discarded and
    `_reference_win_rate` fell back to reading the head-to-head as if it
    were the reference bench. v14 then ranked below v13 on evidence that
    actually favoured it. Pooling also makes the sample sizes honest:
    v14's 340 head-to-head seasons are worth more than any single batch,
    and 20-season batches are individually noise (see research.md).

    Versions with no actual bundled submission are excluded (see
    `_is_submittable`).
    """
    by_version: dict[str, dict] = {}
    for entry in entries:
        version = entry["agent_version"]
        if not _is_submittable(version):
            continue
        acc = by_version.get(version)
        if acc is None:
            acc = {**entry, "evaluation_results": list(entry.get("evaluation_results") or [])}
            by_version[version] = acc
            continue
        if entry.get("evaluation_results"):
            acc["evaluation_results"] = _merge_results(
                acc["evaluation_results"] + list(entry["evaluation_results"])
            )
            acc["commit_sha"] = entry.get("commit_sha", acc.get("commit_sha"))
        if entry.get("kaggle_result"):
            acc["kaggle_result"] = entry["kaggle_result"]
    return list(by_version.values())


def _reference_win_rate(entry: dict) -> float:
    """Like `average_win_rate`, but only over FIXED reference opponents
    (random/starter/greedy/pass -- anything not a file path), excluding
    self-play against another submission bundle.

    Self-play win-rate is relative to whichever specific predecessor
    happened to be logged as the opponent, not an absolute quality
    signal, and different versions get compared against different
    predecessors (v3 was evaluated partly against v2, which it dominates;
    v4 against v3, its own harder, more-similar direct predecessor). That
    asymmetry otherwise drags a genuinely-improved newer version's
    average below an older one's, purely because it happened to be
    tested against a tougher self-play opponent -- confirmed happening
    for v3 vs v4 (v4 fixes a real bug and is never worse than v3, but
    ranked below it before this exclusion).
    """
    results = [r for r in (entry.get("evaluation_results") or []) if "/" not in r["opponent"] and not r["opponent"].endswith(".py")]
    if not results:
        return average_win_rate(entry)  # nothing but self-play logged -- fall back rather than return 0
    return sum(r["win_rate"] for r in results) / len(results)


def _avg_money_margin(entry: dict) -> float:
    """Mean (our final money - opponent's) across FIXED reference
    opponents (see _reference_win_rate for why self-play is excluded) --
    a tiebreaker for when two candidates both show a 100% reference
    win-rate but by very different margins (exactly what happened
    comparing v2 and v3)."""
    results = [r for r in (entry.get("evaluation_results") or []) if "/" not in r["opponent"] and not r["opponent"].endswith(".py")]
    if not results:
        results = entry.get("evaluation_results") or []
    if not results:
        return 0.0
    margins = [r.get("mean_money", 0) - r.get("opponent_mean_money", 0) for r in results]
    return sum(margins) / len(margins)


def _self_play_win_rate(entry: dict) -> float | None:
    """Win rate against another submission bundle (a path-shaped opponent
    name), or None when the version was never tested head-to-head."""
    results = [
        r for r in (entry.get("evaluation_results") or [])
        if "/" in r["opponent"] or r["opponent"].endswith(".py")
    ]
    if not results:
        return None
    return sum(r["win_rate"] for r in results) / len(results)


def _earned_promotion(entry: dict) -> int:
    """1 unless the version was measured head-to-head and LOST.

    Raw self-play rates aren't comparable across versions -- each faces a
    different predecessor, so v8 beating the weaker v7 100% scores higher
    than v9 beating the stronger v8 at 57%, even though v9 is the better
    agent. What *is* comparable is the binary: did this version beat the
    thing it was built to replace? A version that failed that test
    shouldn't outrank its own predecessor.
    """
    rate = _self_play_win_rate(entry)
    return 1 if rate is None or rate >= 0.5 else 0


def _version_number(entry: dict) -> int:
    name = entry.get("agent_version", "")
    digits = name[1:] if name.startswith("v") else name
    return int(digits) if digits.isdigit() else -1


def _sort_key(entry: dict) -> tuple:
    # Reference win-rate first. Then "did it earn its promotion
    # head-to-head", then version number -- because once every candidate
    # beats the weak bench 100%, that bench has stopped discriminating,
    # and money margin against those same saturated opponents is noise
    # (it ranked v8 above v9 despite v9 beating v8 directly across three
    # batches). Money margin stays as a last resort for candidates that
    # are otherwise indistinguishable.
    return (
        _reference_win_rate(entry),
        _earned_promotion(entry),
        _version_number(entry),
        _avg_money_margin(entry),
    )


def _compare_candidates(a: dict, b: dict) -> int:
    """Order two candidates, newest-best first.

    When BOTH have a real Kaggle `public_score`, that head-to-head on the
    actual leaderboard outranks every local signal -- local evaluation is
    a proxy, and two real scores are a direct comparison of the thing we
    actually care about. (This is narrower than an earlier version of
    this ranking, which let ANY stale real score outrank an untested but
    locally-dominant newer version; that was wrong, and it kept
    recommending a known-weak v2 over v3. Requiring *both* sides to have
    real evidence keeps the useful case without the broken one.)

    It matters here: v9 beat v8 57-65% in local self-play but scored
    363.3 against v8's 430.5 on the real leaderboard, because v9's
    feed-growing shrinks the herd -- and across 43 real episodes our herd
    size tracks results hard (herd 7-8: 24% win rate; 9-10: 57%; 11+:
    71%). Local self-play against our own previous version couldn't see
    that, because both sides were the same scale.
    """
    a_real = (a.get("kaggle_result") or {}).get("public_score")
    b_real = (b.get("kaggle_result") or {}).get("public_score")
    if a_real is not None and b_real is not None and a_real != b_real:
        return 1 if a_real > b_real else -1
    ka, kb = _sort_key(a), _sort_key(b)
    return (ka > kb) - (ka < kb)


def rank_candidates(entries: list[dict]) -> list[dict]:
    """Best candidate first, ranked by local win-rate then by average
    money margin.

    Earlier versions of this ranking put ANY candidate with a real
    Kaggle `kaggle_result` ahead of every local-only candidate, no matter
    how much better the local-only one looked. That is wrong whenever a
    newer version was built specifically in response to an older
    version's weak leaderboard result (exactly what happened between v2,
    which scored a real public_score of 389.9, and v3, which was written
    to fix the gap that exposed) -- it kept recommending re-submitting
    the known-weak v2 instead of the untried, locally-dominant v3. Local
    evidence is meant to be trustworthy (constitution Principle II); a
    stale real number for an OLDER, superseded candidate shouldn't
    override that. `format_recommendation` still surfaces each
    candidate's `kaggle_result` when one exists, as context for the
    competitor's own judgment.
    """
    candidates = _latest_per_version(entries)
    return sorted(candidates, key=cmp_to_key(_compare_candidates), reverse=True)


def format_recommendation(entry: dict) -> str:
    has_leaderboard = entry.get("kaggle_result") is not None
    ref_rate = _reference_win_rate(entry)
    overall_rate = average_win_rate(entry)
    lines = [f"Recommended final: {entry['agent_version']} (commit {entry.get('commit_sha', '?')[:8]})"]
    lines.append(f"  Win-rate vs fixed reference opponents (the ranking signal): {ref_rate:.0%}")
    if abs(overall_rate - ref_rate) > 1e-9:
        lines.append(f"  Overall avg win-rate incl. self-play vs another version: {overall_rate:.0%} (excluded from ranking -- see rank_candidates docstring)")
    for r in entry.get("evaluation_results") or []:
        lines.append(f"    vs {r['opponent']}: {r['wins']}W/{r['losses']}L/{r['ties']}T (win_rate={r['win_rate']:.0%})")
    if has_leaderboard:
        lines.append(f"  This version's own recorded leaderboard public_score: {entry['kaggle_result']['public_score']}")
    else:
        lines.append("  NOTE: this version has not been submitted to Kaggle yet -- this recommendation is local-evidence only.")
    return "\n".join(lines)


def mark_final(agent_version: str, rationale: str, log_path: Path = LOG_PATH) -> None:
    """Append (never overwrite) a record marking `agent_version` as the
    chosen final submission, per constitution Principle III."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_version": agent_version,
        "commit_sha": _commit_sha(),
        "hypothesis": f"FINAL SELECTION: {rationale}",
        "evaluation_results": [],
        "kaggle_result": None,
        "decision": "adopt",
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mark-final", metavar="VERSION", help="Append a final-selection record for this agent_version (requires --rationale)")
    parser.add_argument("--rationale", default="", help="Why this version was chosen (used with --mark-final)")
    args = parser.parse_args(argv)

    entries = load_entries()
    ranked = rank_candidates(entries)
    if not ranked:
        print("No evaluated agent versions found in experiments/log.jsonl")
        return 1

    print(format_recommendation(ranked[0]))
    if len(ranked) > 1:
        print(f"\n({len(ranked) - 1} other candidate(s) ranked below this one.)")

    if args.mark_final:
        if not args.rationale:
            print("\n--mark-final requires --rationale", file=sys.stderr)
            return 2
        mark_final(args.mark_final, args.rationale)
        print(f"\nMarked {args.mark_final} as final selection in {LOG_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
