"""Local batch-evaluation harness (spec FR-002, constitution Principle II).

Runs N simulated seasons of a candidate agent against a named opponent via
the real `kaggle_environments` "kaggriculture" engine, reports win/loss/tie
counts and money statistics, and appends an ExperimentLogEntry (per
data-model.md) to experiments/log.jsonl -- the trustworthy local signal
that must exist before any result is spent on an actual Kaggle submission.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "experiments" / "log.jsonl"
SUBMISSIONS_DIR = REPO_ROOT / "submissions"

BUILTIN_OPPONENTS = {"random", "starter", "pass"}


def resolve_opponent(name: str) -> str:
    """Map a short opponent name to what `kaggle_environments` expects."""
    if name in BUILTIN_OPPONENTS:
        return name
    if name == "greedy":
        return str(REPO_ROOT / "evaluation" / "opponents" / "greedy_agent.py")
    if name == "previous":
        return str(_latest_submission_path())
    return name  # assume caller passed an explicit path


def _latest_submission_path() -> Path:
    versions = sorted(
        (p for p in SUBMISSIONS_DIR.glob("v*") if (p / "main.py").exists() and p.name[1:].isdigit()),
        key=lambda p: int(p.name[1:]),
    )
    if not versions:
        raise FileNotFoundError(
            "No submissions/v*/main.py found for the 'previous' opponent -- "
            "run evaluation/bundle_submission.py first."
        )
    return versions[-1] / "main.py"


def _final_money(env) -> tuple[float, float]:
    """Final (player0, player1) money, per kaggriculture.json's reward
    definition (player money at end of game) -- read straight from each
    agent's terminal `reward` rather than re-deriving it from the farm
    state.
    """
    final_state = env.steps[-1]
    return final_state[0].reward, final_state[1].reward


def _outcome(our_money: float, opp_money: float, our_status: str) -> str:
    if our_status not in ("DONE", "ACTIVE"):
        return "loss"  # crash/timeout/invalid forfeits the match
    if our_money > opp_money:
        return "win"
    if our_money < opp_money:
        return "loss"
    return "tie"


def run_batch(agent_path: str, opponent_name: str, seasons: int, config: dict | None = None) -> dict:
    from kaggriculture_agent.constants import DEFAULT_CONFIG
    from kaggle_environments import make

    opponent = resolve_opponent(opponent_name)
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(config or {})

    wins = losses = ties = 0
    our_money: list[float] = []
    opp_money: list[float] = []

    for _ in range(seasons):
        env = make("kaggriculture", configuration=cfg)
        env.run([agent_path, opponent])
        our, opp = _final_money(env)
        our_status = env.steps[-1][0].status
        outcome = _outcome(our, opp, our_status)
        wins += outcome == "win"
        losses += outcome == "loss"
        ties += outcome == "tie"
        our_money.append(our)
        opp_money.append(opp)

    return {
        "opponent": opponent_name,
        "seasons": seasons,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / seasons if seasons else 0.0,
        "mean_money": statistics.mean(our_money) if our_money else 0.0,
        "median_money": statistics.median(our_money) if our_money else 0.0,
        "opponent_mean_money": statistics.mean(opp_money) if opp_money else 0.0,
    }


def average_win_rate(entry: dict) -> float:
    results = entry.get("evaluation_results") or []
    if not results:
        return 0.0
    return sum(r["win_rate"] for r in results) / len(results)


def check_divergence(entries: list[dict]) -> list[str]:
    """Flag consecutive submitted versions where the local win-rate trend
    disagrees with the recorded leaderboard `public_score` trend (spec
    Edge Cases, constitution Principle II). Only entries that already have
    a `kaggle_result` are compared -- versions never actually submitted to
    Kaggle have nothing to diverge from yet.
    """
    scored = [e for e in entries if e.get("kaggle_result")]
    warnings = []
    for prev, curr in zip(scored, scored[1:]):
        local_improved = average_win_rate(curr) > average_win_rate(prev)
        leaderboard_improved = curr["kaggle_result"]["public_score"] > prev["kaggle_result"]["public_score"]
        if local_improved != leaderboard_improved:
            warnings.append(
                f"Divergence: {prev.get('agent_version')} -> {curr.get('agent_version')}: "
                f"local win-rate {'improved' if local_improved else 'declined'} but "
                f"leaderboard score {'improved' if leaderboard_improved else 'declined'}"
            )
    return warnings


def _commit_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def append_log_entry(agent_version: str, hypothesis: str, evaluation_results: list[dict], decision: str = "investigate") -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_version": agent_version,
        "commit_sha": _commit_sha(),
        "hypothesis": hypothesis,
        "evaluation_results": evaluation_results,
        "kaggle_result": None,
        "decision": decision,
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, help="Path to the agent file to evaluate")
    parser.add_argument("--opponents", nargs="+", default=["random"], help="Opponent names: random, starter, pass, greedy, previous, or a path")
    parser.add_argument("--seasons", type=int, default=20, help="Simulated seasons per opponent")
    parser.add_argument("--agent-version", default="dev", help="Label recorded in the experiment log")
    parser.add_argument("--hypothesis", default="", help="One-line note recorded in the experiment log")
    parser.add_argument("--no-log", action="store_true", help="Don't append to experiments/log.jsonl")
    args = parser.parse_args(argv)

    results = []
    for opponent in args.opponents:
        result = run_batch(args.agent, opponent, args.seasons)
        results.append(result)
        print(
            f"vs {opponent:>10}: {result['wins']}W/{result['losses']}L/{result['ties']}T "
            f"(win_rate={result['win_rate']:.0%}, mean_money={result['mean_money']:.0f} "
            f"vs opponent's {result['opponent_mean_money']:.0f})"
        )

    if not args.no_log:
        append_log_entry(args.agent_version, args.hypothesis, results)
        print(f"Logged to {LOG_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
