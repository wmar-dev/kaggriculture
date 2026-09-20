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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "experiments" / "log.jsonl"

sys.path.insert(0, str(REPO_ROOT / "evaluation"))
from run_batch import _commit_sha, average_win_rate  # noqa: E402


def load_entries(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    with log_path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def _latest_per_version(entries: list[dict]) -> list[dict]:
    """Only entries that report evaluation_results represent a candidate
    version's evidence; later entries for the same version (e.g. a
    re-evaluation, or a `mark_final` record) supersede earlier ones."""
    latest: dict[str, dict] = {}
    for entry in entries:
        if entry.get("evaluation_results"):
            latest[entry["agent_version"]] = entry
        elif entry["agent_version"] in latest and entry.get("kaggle_result"):
            # A later entry may only carry a fresh kaggle_result -- merge it in.
            latest[entry["agent_version"]] = {**latest[entry["agent_version"]], "kaggle_result": entry["kaggle_result"]}
    return list(latest.values())


def _avg_money_margin(entry: dict) -> float:
    """Mean (our final money - opponent's) across this version's
    evaluation_results -- a tiebreaker for when two candidates both show
    a 100% local win-rate but by very different margins (exactly what
    happened comparing v2 and v3)."""
    results = entry.get("evaluation_results") or []
    if not results:
        return 0.0
    margins = [r.get("mean_money", 0) - r.get("opponent_mean_money", 0) for r in results]
    return sum(margins) / len(margins)


def _sort_key(entry: dict) -> tuple:
    return (average_win_rate(entry), _avg_money_margin(entry))


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
    return sorted(candidates, key=_sort_key, reverse=True)


def format_recommendation(entry: dict) -> str:
    has_leaderboard = entry.get("kaggle_result") is not None
    local = average_win_rate(entry)
    lines = [f"Recommended final: {entry['agent_version']} (commit {entry.get('commit_sha', '?')[:8]})"]
    lines.append(f"  Local avg win-rate: {local:.0%} across {len(entry.get('evaluation_results') or [])} opponent(s)")
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
