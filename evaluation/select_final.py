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


def _sort_key(entry: dict) -> tuple:
    has_leaderboard = entry.get("kaggle_result") is not None
    public_score = entry["kaggle_result"]["public_score"] if has_leaderboard else 0
    return (has_leaderboard, public_score, average_win_rate(entry))


def rank_candidates(entries: list[dict]) -> list[dict]:
    """Best candidate first: real leaderboard evidence outranks local-only
    evidence (regardless of local win-rate), then by leaderboard score,
    then by local win-rate."""
    candidates = _latest_per_version(entries)
    return sorted(candidates, key=_sort_key, reverse=True)


def format_recommendation(entry: dict) -> str:
    has_leaderboard = entry.get("kaggle_result") is not None
    local = average_win_rate(entry)
    lines = [f"Recommended final: {entry['agent_version']} (commit {entry.get('commit_sha', '?')[:8]})"]
    if has_leaderboard:
        lines.append(f"  Leaderboard public_score: {entry['kaggle_result']['public_score']}")
    lines.append(f"  Local avg win-rate: {local:.0%} across {len(entry.get('evaluation_results') or [])} opponent(s)")
    for r in entry.get("evaluation_results") or []:
        lines.append(f"    vs {r['opponent']}: {r['wins']}W/{r['losses']}L/{r['ties']}T (win_rate={r['win_rate']:.0%})")
    if not has_leaderboard:
        lines.append("  NOTE: no leaderboard result recorded yet for this version -- this recommendation is local-evidence only.")
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
