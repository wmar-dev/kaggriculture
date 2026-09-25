"""Demand-stratified head-to-head benchmark.

Real leaderboard data showed v17's results are dictated by the town's shop
draw: when the unlocked shops barely buy MILK or WOOL (combined demand
<= 3 shop-units), v17 went 1W/7L in real matches; with healthy demand
(>= 4) it went 9W/4L. Plain self-play win rate averages over both regimes
and can hide a change that fixes one while breaking the other.

Both players share the town, so every game is already a paired comparison.
This runs N games (alternating seats, in parallel), records the shop draw
each game actually produced, and reports results split by that demand.
The seed cannot pin the draw across different agents -- the engine
re-seeds per day but consumes RNG for weed spawns on every empty tile
before drawing a shop, so the draw depends on board state -- hence
post-hoc stratification rather than fixed seeds.

    python evaluation/demand_bench.py --agent A.py --opponent B.py --games 120
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from multiprocessing import Pool
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

LOW_DEMAND_MAX = 3  # milk+wool shop-units at or below this = "weak" town


def _demand(shops: list[str], product: str) -> int:
    from kaggriculture_agent.constants import SHOPS

    return sum((2 if len(SHOPS[s]) == 1 else 1) for s in shops if s in SHOPS and product in SHOPS[s])


def _play(job: tuple[str, str, int]) -> dict:
    agent, opponent, game = job
    from kaggle_environments import make

    we_first = game % 2 == 0
    env = make("kaggriculture", configuration={"episodeSteps": 720})
    env.run([agent, opponent] if we_first else [opponent, agent])
    us, them = (0, 1) if we_first else (1, 0)
    final = env.steps[-1]
    shops = final[0]["observation"]["town"]["unlocked_shops"]
    return {
        "ours": final[us].reward or 0,
        "theirs": final[them].reward or 0,
        "status": final[us].status,
        "shops": shops,
        "milk_wool": _demand(shops, "MILK") + _demand(shops, "WOOL"),
    }


def _summary(rows: list[dict], label: str) -> str:
    if not rows:
        return f"{label:>14}: (none)"
    w = sum(r["ours"] > r["theirs"] for r in rows)
    lo = sum(r["ours"] < r["theirs"] for r in rows)
    return (
        f"{label:>14}: {w}W/{lo}L/{len(rows) - w - lo}T ({w / len(rows):.0%})  "
        f"money {statistics.mean(r['ours'] for r in rows):7.0f} vs "
        f"{statistics.mean(r['theirs'] for r in rows):7.0f}  n={len(rows)}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--games", type=int, default=120)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", help="write raw per-game results as JSON")
    args = ap.parse_args(argv)

    jobs = [(args.agent, args.opponent, g) for g in range(args.games)]
    with Pool(args.workers) as pool:
        rows = pool.map(_play, jobs)

    if args.out:
        Path(args.out).write_text(json.dumps(rows))
    weak = [r for r in rows if r["milk_wool"] <= LOW_DEMAND_MAX]
    strong = [r for r in rows if r["milk_wool"] > LOW_DEMAND_MAX]
    print(_summary(weak, f"weak (<= {LOW_DEMAND_MAX})"))
    print(_summary(strong, "strong"))
    print(_summary(rows, "all"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
