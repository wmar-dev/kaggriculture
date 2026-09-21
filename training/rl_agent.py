"""Load a trained PPO checkpoint and expose it as an `agent(obs)` callable
compatible with `kaggle_environments`/`evaluation/run_batch.py`, for local
evaluation against v7 and the reference opponents.

This is NOT the Kaggle submission format (it depends on stable-baselines3
and torch, which a bundled single-file submission can't rely on being
available) -- it's purely for deciding whether the trained policy is
worth the separate effort of extracting into a dependency-free bundle.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from stable_baselines3 import PPO

from env import FARMER_ACTIONS, encode_observation
from kaggriculture_agent.observation import parse_observation
from kaggriculture_agent.strategy import _count_growing_crops, _decide_hand_action, _market_orders, choose_best_crop

_model = None


def load_model(path: str) -> None:
    global _model
    _model = PPO.load(path)


def agent(obs: dict) -> dict:
    if _model is None:
        raise RuntimeError("Call rl_agent.load_model(path) before using agent()")

    parsed = parse_observation(obs)
    target_crop = choose_best_crop(parsed.my_farm["money"], parsed.market_prices, _count_growing_crops(parsed))

    encoded = encode_observation(parsed)
    action_idx, _ = _model.predict(encoded, deterministic=True)
    farmer_action = list(FARMER_ACTIONS[int(action_idx)])
    if farmer_action[0] == "PLANT":
        if target_crop and parsed.seeds.get(target_crop, 0) > 0:
            farmer_action = ["PLANT", target_crop]
        else:
            farmer_action = ["PASS"]

    claimed: set = set()
    hands_actions = [
        _decide_hand_action(parsed, pos, parsed.hand_inventory(i), claimed)
        for i, pos in enumerate(parsed.hand_positions())
    ]
    market_orders = _market_orders(parsed, target_crop)
    return {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}
