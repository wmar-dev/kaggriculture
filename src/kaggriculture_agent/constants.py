"""Game constants for Kaggriculture.

Transcribed directly from the bundled `kaggle_environments` package's
`kaggriculture.py` engine (the real competition environment, confirmed
present in `kaggle-environments==1.32.7`) rather than re-derived from
prose, so these values are exact, not approximations. See
specs/001-win-kaggriculture/research.md R1.
"""

from __future__ import annotations

# Crop economics: seed cost, days to first/max yield, ongoing-production
# interval (0 for one-time crops), max harvestable yield, and whether the
# crop keeps producing after its first yield.
CROPS: dict[str, dict[str, int | bool]] = {
    "WHEAT":      {"seed": 10,  "first_yield_day": 2,  "max_yield_day": 4,  "interval": 0, "max_yield": 6, "ongoing": False},
    "CARROT":     {"seed": 20,  "first_yield_day": 2,  "max_yield_day": 3,  "interval": 0, "max_yield": 4, "ongoing": False},
    "TOMATO":     {"seed": 50,  "first_yield_day": 8,  "max_yield_day": 8,  "interval": 1, "max_yield": 4, "ongoing": True},
    "STRAWBERRY": {"seed": 100, "first_yield_day": 10, "max_yield_day": 10, "interval": 2, "max_yield": 4, "ongoing": True},
    "MELON":      {"seed": 80,  "first_yield_day": 10, "max_yield_day": 12, "interval": 0, "max_yield": 6, "ongoing": False},
}

# Animal economics: purchase cost, required structure, days to first yield,
# production interval, max unharvested product held on the tile, and the
# product it yields.
ANIMALS: dict[str, dict[str, int | str]] = {
    "GOOSE": {"cost": 300, "structure": "COOP",    "first_yield_day": 4, "interval": 1, "max_held": 4, "product": "EGG"},
    "COW":   {"cost": 400, "structure": "PASTURE", "first_yield_day": 8, "interval": 2, "max_held": 6, "product": "MILK"},
    "SHEEP": {"cost": 500, "structure": "PASTURE", "first_yield_day": 6, "interval": 3, "max_held": 6, "product": "WOOL"},
}

PRODUCTS: list[str] = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]

MARKET_I0 = 10_000
PRICE_FLOOR = 1

# Dynamic price-curve parameters per resource. See
# contracts/agent-interface.md and CONTEST.md's "Price Function" section
# for the formula these parameters feed.
MARKET_PARAMS: dict[str, dict[str, int | str | float]] = {
    "WHEAT":      {"base": 25,  "I0": MARKET_I0, "T": 400, "below_func": "sqrt",   "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base": 35,  "I0": MARKET_I0, "T": 450, "below_func": "hinge",  "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base": 60,  "I0": MARKET_I0, "T": 200, "below_func": "hinge",  "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",   "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base": 50,  "I0": MARKET_I0, "T": 332, "below_func": "hinge",  "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",   "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",    "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear", "below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

# Which products each town shop demands; a shop instance consumes one of
# each listed product per townShopSellInterval turns (single-product shops
# consume 2x, per CONTEST.md).
SHOPS: dict[str, list[str]] = {
    "BAKERY":         ["EGG", "WHEAT"],
    "PIZZA_SHOP":     ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT":    ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE":     ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE":       ["CARROT"],
    "SMOOTHIE_SHOP":  ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

TOWN_CENTER_PRODUCTS: list[str] = [p for p in PRODUCTS if p != "FERTILIZER"]
MAX_SHOP_INSTANCES = 8
FARM_HAND_COST_MULT = 1

# Confirmed episode/turn `configuration` defaults, i.e. what
# `kaggle_environments.make("kaggriculture", configuration={...})` accepts
# (kaggriculture.json's "configuration" section).
DEFAULT_CONFIG = {
    "episodeSteps": 720,
    "actTimeout": 1,
    "boardSize": 10,
    "startingMoney": 3000,
    "maxMarketOrdersPerTurn": 10,
    "turnsPerDay": 24,
    "shedCapacity": 100,
    "weedSpawnChance": 0.005,
    "townShopUnlockInterval": 3,
    "townShopSellInterval": 4,
    "townCenterSellInterval": 24,
    "farmHandCostMult": FARM_HAND_COST_MULT,
}

# NOT a `configuration` key -- this is the per-episode *observation* field
# (kaggriculture.json's "observation.remainingOverageTime"): the shared
# cumulative overage budget (seconds) on top of the per-turn `actTimeout`.
REMAINING_OVERAGE_TIME_SECONDS = 60

# Internal per-turn compute budget target for our own agent, well under the
# confirmed actTimeout of 1s (research.md R1).
INTERNAL_TURN_BUDGET_SECONDS = 0.05

QUADRANTS: list[str] = ["NW", "NE", "SW", "SE"]
BUY_LAND_COSTS: list[int] = [1000, 2000, 4000]

FARMER_MOVE_OPS: list[str] = ["NORTH", "SOUTH", "EAST", "WEST"]


def shed_tiles(board_size: int) -> list[tuple[int, int]]:
    """The four board tiles orthogonally adjacent to the shed (CONTEST.md):
    (half-1,half-1), (half,half-1), (half-1,half), (half,half) for
    half = board_size // 2. The shed itself is never a tile."""
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def yield_per_tile_per_day(crop: str) -> float:
    """Total units harvested per day the tile is occupied, watering daily,
    no fertilizer -- matches the "Yield / tile / day" column in CONTEST.md.
    Computed from CROPS rather than hardcoded so it can't drift out of sync.
    """
    info = CROPS[crop]
    if info["ongoing"]:
        # Ongoing crops: base 1 unit per scheduled production, at the
        # configured interval, divided by the interval (not occupancy --
        # ongoing crops don't have a fixed lifespan to divide by, per
        # CONTEST.md; we approximate "value density" as yield/turn-interval
        # converted to a per-day rate assuming a scheduled production every
        # `interval` days after first yield).
        interval = info["interval"] or 1
        return 1.0 / interval
    # One-time crops: max_yield achieved by max_yield_day (unfertilized cap
    # may be lower in-game, but this is a planning-time estimate).
    return info["max_yield"] / info["max_yield_day"]
