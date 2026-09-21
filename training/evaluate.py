"""Evaluate a trained PPO checkpoint against the reference opponents and
v7, the same way evaluation/run_batch.py evaluates heuristic versions.

Usage:
    python training/evaluate.py --model training/models/checkpoints/ppo_farmer_v1_500000_steps.zip --seasons 10
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evaluation"))

from kaggle_environments import make

import rl_agent
from run_batch import resolve_opponent


def evaluate(model_path: str, opponent: str, seasons: int, episode_steps: int = 720) -> dict:
    rl_agent.load_model(model_path)
    opponent_resolved = resolve_opponent(opponent)

    wins = losses = ties = 0
    our_money: list[float] = []
    opp_money: list[float] = []
    for _ in range(seasons):
        env = make("kaggriculture", configuration={"episodeSteps": episode_steps})
        env.run([rl_agent.agent, opponent_resolved])
        final = env.steps[-1]
        our, opp = final[0].reward, final[1].reward
        status = final[0].status
        if status not in ("DONE", "ACTIVE"):
            losses += 1
        elif our > opp:
            wins += 1
        elif our < opp:
            losses += 1
        else:
            ties += 1
        our_money.append(our)
        opp_money.append(opp)

    return {
        "opponent": opponent,
        "seasons": seasons,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": wins / seasons if seasons else 0.0,
        "mean_money": statistics.mean(our_money) if our_money else 0.0,
        "median_money": statistics.median(our_money) if our_money else 0.0,
        "opponent_mean_money": statistics.mean(opp_money) if opp_money else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--opponents", nargs="+", default=["random", "starter", "greedy", "previous"])
    parser.add_argument("--seasons", type=int, default=10)
    parser.add_argument("--episode-steps", type=int, default=720)
    args = parser.parse_args()

    for opponent in args.opponents:
        result = evaluate(args.model, opponent, args.seasons, args.episode_steps)
        print(
            f"vs {opponent:>10}: {result['wins']}W/{result['losses']}L/{result['ties']}T "
            f"(win_rate={result['win_rate']:.0%}, mean_money={result['mean_money']:.0f} "
            f"vs opponent's {result['opponent_mean_money']:.0f})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
