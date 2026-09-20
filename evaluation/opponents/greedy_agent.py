"""Reference opponent for local evaluation (research.md R3): a mid-tier
bot, stronger than the environment's built-in `"starter"` (which only ever
farms one fixed crop on one tile) but deliberately simpler than our own
`kaggriculture_agent.strategy.baseline_strategy` -- it dynamically picks
the best-affordable crop by yield/tile/day * price, but only ever tends
the single tile the main farmer stands on, never hires hands or buys land.

Standalone by design (only imports from kaggriculture_agent's constants
module, not the agent/strategy modules it's meant to be benchmarked
against) so it can be loaded by `kaggle_environments.make(...).run([...])`
independently of whatever the primary agent bundle looks like.
"""

from __future__ import annotations

from kaggriculture_agent.constants import CROPS, yield_per_tile_per_day


def _is_harvest_ready(tile: dict, current_day: int) -> bool:
    """See kaggriculture_agent.strategy._is_harvest_ready for why this
    extra day check is required and not just `yield_units > 0`."""
    if tile.get("yield_units", 0) <= 0:
        return False
    first_yield_day = CROPS[tile["crop"]]["first_yield_day"]
    return current_day - tile["planted_day"] >= first_yield_day


def _choose_crop(money: float, prices: dict) -> str | None:
    """See kaggriculture_agent.strategy.choose_best_crop for why this is
    divided by first_yield_day (a payback-speed penalty)."""
    best_crop, best_value = None, -1.0
    for crop, info in CROPS.items():
        if info["seed"] > money:
            continue
        value = yield_per_tile_per_day(crop) * prices.get(crop, 0) / info["first_yield_day"]
        if value > best_value:
            best_crop, best_value = crop, value
    return best_crop


def agent(obs: dict) -> dict:
    farms = obs.get("farms", [])
    player = obs.get("player", 0)
    private = obs.get("private", {}) or {}
    if not farms or player >= len(farms):
        return {"farmer": ["PASS"], "hands": [], "market": []}

    farm = farms[player]
    fx, fy = farm["farmer"]
    tile = farm["tiles"][fy][fx]
    day = obs.get("day", 0)
    seeds = private.get("seeds", {}) or {}
    shed = private.get("shed", {}) or {}
    prices = (obs.get("market", {}) or {}).get("prices", {}) or {}
    money = farm["money"]

    market = [["SELL", item, qty] for item, qty in shed.items() if qty > 0]

    target_crop = _choose_crop(money, prices)
    if target_crop and seeds.get(target_crop, 0) == 0 and money >= CROPS[target_crop]["seed"]:
        market.append(["BUY_SEED", target_crop, 1])

    farmer = ["PASS"]
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        if _is_harvest_ready(tile, day):
            farmer = ["HARVEST"]
        elif not tile["watered_today"]:
            farmer = ["WATER"]
    elif isinstance(tile, dict) and tile.get("kind") == "WEED":
        farmer = ["DIG"]
    elif tile is None and target_crop and seeds.get(target_crop, 0) > 0:
        farmer = ["PLANT", target_crop]

    return {"farmer": farmer, "hands": [], "market": market[:10]}
