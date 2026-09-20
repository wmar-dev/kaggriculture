"""Baseline rule-based Kaggriculture strategy (research.md R4).

Design, deliberately simple per constitution Principle V (Time-Boxed
Simplicity): every farmer/hand independently tends whatever tile it's
standing on (water/harvest/dig/plant), or walks toward the nearest tile
that needs attention when there's nothing to do locally. Crop choice is
driven by current `yield/tile/day * market price`. No animal husbandry,
no fertilizing, and no market-impact-aware sell batching in this first
version -- those are natural targets for the next iteration (User Story 2)
once this baseline's ceiling is measured against the opponent pool in
research.md R3.
"""

from __future__ import annotations

from kaggriculture_agent.constants import CROPS, DEFAULT_CONFIG, yield_per_tile_per_day
from kaggriculture_agent.observation import GameObservation, tile_kind

MAX_MARKET_ORDERS = DEFAULT_CONFIG["maxMarketOrdersPerTurn"]
_DIRECTION_DELTA = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def _is_harvest_ready(tile: dict, current_day: int) -> bool:
    """True once HARVEST would actually do something.

    `yield_units` is seeded to 1 for one-time crops at planting time (not
    0), but the engine's own HARVEST handler silently no-ops until
    `day - planted_day >= first_yield_day` regardless of `yield_units` --
    so `yield_units > 0` alone is NOT a valid readiness check for one-time
    crops (confirmed by reading the bundled `kaggriculture.py` engine
    directly; ongoing crops happen to keep `yield_units` at 0 until ready,
    so this check is a safe no-op guard for them too).
    """
    if tile.get("yield_units", 0) <= 0:
        return False
    first_yield_day = CROPS[tile["crop"]]["first_yield_day"]
    return current_day - tile["planted_day"] >= first_yield_day


def choose_best_crop(money: float, prices: dict) -> str | None:
    """Best crop among affordable seeds.

    Value is (yield/tile/day * current price), divided by `first_yield_day`
    as a payback-speed penalty. Without this penalty MELON (high
    steady-state yield/tile/day, but a 10-day wait before HARVEST does
    anything at all -- see strategy._is_harvest_ready) dominates the raw
    metric and the agent over-commits seed money into several melons
    before any of them can pay back, starving cash for the fast-cycling
    WHEAT/CARROT loops that would actually fund expansion early on.
    """
    best_crop = None
    best_value = -1.0
    for crop, info in CROPS.items():
        if info["seed"] > money:
            continue
        price = prices.get(crop, 0)
        value = yield_per_tile_per_day(crop) * price / info["first_yield_day"]
        if value > best_value:
            best_value = value
            best_crop = crop
    return best_crop


def _step_toward(pos: tuple[int, int], target: tuple[int, int]) -> list[str]:
    fx, fy = pos
    tx, ty = target
    dx, dy = tx - fx, ty - fy
    if dx == 0 and dy == 0:
        return ["PASS"]
    if abs(dx) >= abs(dy) and dx != 0:
        return ["EAST"] if dx > 0 else ["WEST"]
    return ["SOUTH"] if dy > 0 else ["NORTH"]


def _tile_needs_attention(obs: GameObservation, x: int, y: int, target_crop: str | None, plantable_remaining: int) -> bool:
    tile = obs.tile_at(x, y)
    kind = tile_kind(tile)
    if kind == "PLANT":
        return not tile["watered_today"] or _is_harvest_ready(tile, obs.day)
    if kind == "WEED":
        return True
    if kind == "EMPTY":
        return target_crop is not None and plantable_remaining > 0
    return False


def _find_nearest_tile(obs: GameObservation, from_pos: tuple[int, int], target_crop: str | None, plantable_remaining: int, claimed: set) -> tuple[int, int] | None:
    board_size = len(obs.my_farm["tiles"])
    best = None
    best_dist = None
    for y in range(board_size):
        for x in range(board_size):
            if (x, y) in claimed:
                continue
            if not _tile_needs_attention(obs, x, y, target_crop, plantable_remaining):
                continue
            dist = abs(x - from_pos[0]) + abs(y - from_pos[1])
            if best_dist is None or dist < best_dist:
                best, best_dist = (x, y), dist
    return best


def _decide_unit_action(obs: GameObservation, pos: tuple[int, int], target_crop: str | None, plant_budget: dict, claimed: set) -> list[str]:
    x, y = pos
    tile = obs.tile_at(x, y)
    kind = tile_kind(tile)

    if kind == "PLANT":
        if _is_harvest_ready(tile, obs.day):
            return ["HARVEST"]
        if not tile["watered_today"]:
            return ["WATER"]
    elif kind == "WEED":
        return ["DIG"]
    elif kind == "EMPTY" and target_crop is not None and plant_budget.get(target_crop, 0) > 0:
        plant_budget[target_crop] -= 1
        return ["PLANT", target_crop]

    remaining = plant_budget.get(target_crop, 0) if target_crop else 0
    target = _find_nearest_tile(obs, pos, target_crop, remaining, claimed)
    if target is None or target == pos:
        return ["PASS"]
    claimed.add(target)
    return _step_toward(pos, target)


def _market_orders(obs: GameObservation, target_crop: str | None) -> list[list]:
    orders: list[list] = []
    for item, qty in obs.shed.items():
        if qty > 0:
            orders.append(["SELL", item, qty])

    money = obs.my_farm["money"]
    seeds = obs.seeds
    if target_crop and seeds.get(target_crop, 0) == 0:
        cost = CROPS[target_crop]["seed"]
        if money >= cost:
            orders.append(["BUY_SEED", target_crop, 1])

    if obs.hour == 0:
        hires_today = obs.my_farm.get("hires_today", 0)
        if hires_today < 2 and money >= 500:
            orders.append(["HIRE"])

    unlocked = obs.unlocked_quadrants()
    if len(unlocked) < 4:
        next_cost = [1000, 2000, 4000][len(unlocked) - 1]
        if money >= next_cost * 2:
            orders.append(["BUY_LAND"])

    return orders[:MAX_MARKET_ORDERS]


def baseline_strategy(obs: GameObservation) -> dict:
    prices = obs.market_prices
    money = obs.my_farm["money"]
    target_crop = choose_best_crop(money, prices)

    plant_budget = {target_crop: obs.seeds.get(target_crop, 0)} if target_crop else {}
    claimed: set = set()

    farmer_action = _decide_unit_action(obs, obs.farmer_position(), target_crop, plant_budget, claimed)
    hands_actions = [
        _decide_unit_action(obs, pos, target_crop, plant_budget, claimed)
        for pos in obs.hand_positions()
    ]

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": _market_orders(obs, target_crop),
    }
