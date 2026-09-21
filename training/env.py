"""Gymnasium environment for training the Kaggriculture FARMER's
tile-tending/movement policy via RL.

Deliberately scoped: this is NOT full end-to-end RL over the whole game.
Crop choice (`choose_best_crop`), all market orders (seed/animal/land
buying, hiring, selling), and every hired hand's animal-husbandry loop
are reused verbatim from `kaggriculture_agent.strategy` (the proven,
heavily-tuned v7 logic) and are NOT controlled by the RL policy. Only the
farmer's single per-turn action (movement, water, harvest, dig, plant,
pass) is replaced by a learned policy. This keeps the action space and
credit-assignment problem tractable within a realistic training budget,
and is a fair, isolated test of "can RL beat the hand-crafted
tile-tending heuristic specifically" while holding everything else
(already validated extensively -- see research.md) constant.
"""

from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import agents as BUILTIN_AGENTS

from kaggriculture_agent.constants import CROPS, MARKET_PARAMS
from kaggriculture_agent.observation import GameObservation, parse_observation, tile_kind
from kaggriculture_agent.strategy import (
    _count_growing_crops,
    _decide_hand_action,
    _is_harvest_ready,
    _market_orders,
    choose_best_crop,
)

CROP_LIST = list(CROPS.keys())
PRODUCT_LIST = list(MARKET_PARAMS.keys())

# Discrete farmer action set. FERTILIZE/PICKUP/PLACE are excluded: the
# farmer never carries fertilizer or animals in this design (that's the
# hands' job), so those would always no-op.
FARMER_ACTIONS: list[list[str]] = [
    ["NORTH"],
    ["SOUTH"],
    ["EAST"],
    ["WEST"],
    ["WATER"],
    ["HARVEST"],
    ["DIG"],
    ["PLANT"],  # crop filled in at step time from choose_best_crop
    ["PASS"],
]
N_ACTIONS = len(FARMER_ACTIONS)


def _find_nearest_needy_tile(obs: GameObservation, target_crop: str | None) -> tuple[int, int] | None:
    """Same predicate as strategy._tile_needs_attention, inlined here so
    training doesn't depend on strategy's private claimed-set threading."""
    board_size = len(obs.my_farm["tiles"])
    fx, fy = obs.farmer_position()
    best, best_dist = None, None
    for y in range(board_size):
        for x in range(board_size):
            tile = obs.tile_at(x, y)
            kind = tile_kind(tile)
            needs = False
            if kind == "PLANT":
                needs = not tile["watered_today"] or _is_harvest_ready(tile, obs.day)
            elif kind == "WEED":
                needs = True
            elif kind == "EMPTY":
                needs = target_crop is not None
            if not needs:
                continue
            dist = abs(x - fx) + abs(y - fy)
            if best_dist is None or dist < best_dist:
                best, best_dist = (x, y), dist
    return best


def encode_observation(obs: GameObservation) -> np.ndarray:
    farm = obs.my_farm
    money = farm["money"]
    fx, fy = obs.farmer_position()
    tile = obs.tile_at(fx, fy)
    kind = tile_kind(tile)
    target_crop = choose_best_crop(money, obs.market_prices, _count_growing_crops(obs))

    features: list[float] = [
        money / 10_000.0,
        obs.day / 30.0,
        obs.hour / 24.0,
        fx / 10.0,
        fy / 10.0,
        len(obs.hand_positions()) / 10.0,
        len(obs.unlocked_quadrants()) / 4.0,
        farm.get("hires_today", 0) / 10.0,
    ]

    # Market price ratio to base (how scarce/abundant each product is).
    for product in PRODUCT_LIST:
        base = MARKET_PARAMS[product]["base"]
        price = obs.market_prices.get(product, base)
        features.append(min(3.0, price / base))

    # Seeds held per crop, and shed stock per crop product.
    for crop in CROP_LIST:
        features.append(min(1.0, obs.seeds.get(crop, 0) / 5.0))
    for crop in CROP_LIST:
        features.append(min(1.0, obs.shed.get(crop, 0) / 20.0))

    # Tile the farmer is standing on: one-hot kind.
    for k in ("EMPTY", "LOCKED", "PLANT", "WEED", "COOP", "PASTURE"):
        features.append(1.0 if kind == k else 0.0)
    # If it's a plant: which crop, watered/ready flags, age, yield.
    is_plant = kind == "PLANT"
    for crop in CROP_LIST:
        features.append(1.0 if is_plant and tile["crop"] == crop else 0.0)
    features.append(1.0 if is_plant and tile["watered_today"] else 0.0)
    features.append(1.0 if is_plant and _is_harvest_ready(tile, obs.day) else 0.0)
    age = (obs.day - tile["planted_day"]) if is_plant else 0
    features.append(min(1.0, age / 15.0))
    features.append(min(1.0, (tile.get("yield_units", 0) if is_plant else 0) / 6.0))

    # Board-wide summary counts (not the full grid -- keeps the feature
    # vector fixed-size and small regardless of board complexity).
    empty = locked = weed = needs_water = ready_harvest = structures = 0
    for row in farm["tiles"]:
        for t in row:
            k2 = tile_kind(t)
            if k2 == "EMPTY":
                empty += 1
            elif k2 == "LOCKED":
                locked += 1
            elif k2 == "WEED":
                weed += 1
            elif k2 == "PLANT":
                if not t["watered_today"]:
                    needs_water += 1
                if _is_harvest_ready(t, obs.day):
                    ready_harvest += 1
            elif k2 in ("COOP", "PASTURE"):
                structures += 1
    for count in (empty, locked, weed, needs_water, ready_harvest, structures):
        features.append(min(1.0, count / 100.0))

    # Nearest tile needing attention: distance + relative direction.
    target = _find_nearest_needy_tile(obs, target_crop)
    if target is None:
        features.extend([0.0, 0.0, 0.0])
    else:
        dist = abs(target[0] - fx) + abs(target[1] - fy)
        features.append(min(1.0, dist / 20.0))
        features.append((target[0] - fx) / 10.0)
        features.append((target[1] - fy) / 10.0)

    # Which crop the heuristic currently recommends (one-hot).
    for crop in CROP_LIST:
        features.append(1.0 if target_crop == crop else 0.0)

    return np.array(features, dtype=np.float32)


class KaggricultureFarmerEnv(gym.Env):
    """Single-agent Gym view of the farmer's per-turn action, playing
    against a fixed built-in opponent (see BUILTIN_AGENTS). Hands and all
    market orders are driven automatically by the proven v7 heuristic."""

    metadata = {"render_modes": []}

    def __init__(self, opponent: str = "starter", episode_steps: int = 192):
        super().__init__()
        if opponent not in BUILTIN_AGENTS:
            raise ValueError(f"Unknown built-in opponent {opponent!r}; choices: {list(BUILTIN_AGENTS)}")
        self.opponent = opponent
        self.episode_steps = episode_steps
        self._kaggle_env = None
        self._prev_money = 0.0
        self.action_space = spaces.Discrete(N_ACTIONS)
        sample_dim = len(encode_observation(_dummy_obs()))
        self.observation_space = spaces.Box(low=-5.0, high=5.0, shape=(sample_dim,), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._kaggle_env = make("kaggriculture", configuration={"episodeSteps": self.episode_steps})
        self._kaggle_env.reset()
        obs = parse_observation(self._kaggle_env.state[0].observation)
        self._prev_money = obs.my_farm["money"]
        return encode_observation(obs), {}

    def step(self, action_idx: int):
        obs = parse_observation(self._kaggle_env.state[0].observation)
        target_crop = choose_best_crop(obs.my_farm["money"], obs.market_prices, _count_growing_crops(obs))

        farmer_action = list(FARMER_ACTIONS[action_idx])
        if farmer_action[0] == "PLANT":
            if target_crop and obs.seeds.get(target_crop, 0) > 0:
                farmer_action = ["PLANT", target_crop]
            else:
                farmer_action = ["PASS"]

        claimed: set = set()
        hands_actions = [
            _decide_hand_action(obs, pos, obs.hand_inventory(i), claimed)
            for i, pos in enumerate(obs.hand_positions())
        ]
        market_orders = _market_orders(obs, target_crop)
        our_action = {"farmer": farmer_action, "hands": hands_actions, "market": market_orders}

        opp_obs = self._kaggle_env.state[1].observation
        opp_action = BUILTIN_AGENTS[self.opponent](opp_obs)

        self._kaggle_env.step([our_action, opp_action])

        new_obs = parse_observation(self._kaggle_env.state[0].observation)
        money = new_obs.my_farm["money"]
        reward = float(money - self._prev_money) / 100.0  # scaled for training stability
        self._prev_money = money

        done = bool(self._kaggle_env.done)
        info = {}
        if done:
            info["final_money"] = money
            info["opponent_final_money"] = self._kaggle_env.state[1].observation["farms"][1]["money"]
        return encode_observation(new_obs), reward, done, False, info


def _dummy_obs() -> GameObservation:
    """Minimal synthetic observation, used only to size the observation
    space at __init__ time without needing a live kaggle_environments
    instance."""
    tiles = [[None for _ in range(10)] for _ in range(10)]
    farm = {
        "money": 3000,
        "tiles": tiles,
        "farmer": [4, 4],
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }
    raw = {
        "player": 0,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [farm, dict(farm)],
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
        "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
    }
    return parse_observation(raw)
