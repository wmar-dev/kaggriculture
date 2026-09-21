from __future__ import annotations

# ---- constants.py ------------------------------------------------
"""Game constants for Kaggriculture.

Transcribed directly from the bundled `kaggle_environments` package's
`kaggriculture.py` engine (the real competition environment, confirmed
present in `kaggle-environments==1.32.7`) rather than re-derived from
prose, so these values are exact, not approximations. See
specs/001-win-kaggriculture/research.md R1.
"""


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

# ---- observation.py ----------------------------------------------
"""Typed-ish parsing helpers over the raw Kaggriculture `obs` dict.

The wire format is plain dicts (see contracts/agent-interface.md and
data-model.md); this module doesn't change that shape, it just gives the
strategy layer named, testable accessors instead of repeating dict lookups
and tile-kind checks everywhere.
"""


from dataclasses import dataclass
from typing import Any

Tile = Any  # None | "LOCKED" | plant dict | weed dict | structure dict


@dataclass(frozen=True)
class GameObservation:
    raw: dict
    player: int
    step: int
    day: int
    hour: int

    @property
    def farms(self) -> list[dict]:
        return self.raw["farms"]

    @property
    def my_farm(self) -> dict:
        return self.farms[self.player]

    @property
    def opponent_farm(self) -> dict:
        return self.farms[1 - self.player]

    @property
    def private(self) -> dict:
        return self.raw.get("private", {}) or {}

    @property
    def shed(self) -> dict:
        return self.private.get("shed", {}) or {}

    @property
    def seeds(self) -> dict:
        return self.private.get("seeds", {}) or {}

    @property
    def inventories(self) -> list[dict]:
        return self.private.get("inventories", []) or []

    @property
    def market(self) -> dict:
        return self.raw.get("market", {}) or {}

    @property
    def market_prices(self) -> dict:
        return self.market.get("prices", {}) or {}

    @property
    def market_inventory(self) -> dict:
        return self.market.get("inventory", {}) or {}

    @property
    def unlocked_shops(self) -> list[str]:
        return (self.raw.get("town", {}) or {}).get("unlocked_shops", []) or []

    def farmer_position(self) -> tuple[int, int]:
        x, y = self.my_farm["farmer"]
        return x, y

    def hand_positions(self) -> list[tuple[int, int]]:
        return [(x, y) for x, y in self.my_farm.get("hands", [])]

    def tile_at(self, x: int, y: int) -> Tile:
        return self.my_farm["tiles"][y][x]

    def unlocked_quadrants(self) -> list[str]:
        return self.my_farm.get("unlocked_quadrants", []) or []

    def hand_inventory(self, hand_index: int) -> dict:
        """`hand_index` is 0-based over hands (not counting the farmer)."""
        idx = hand_index + 1  # inventories[0] is the farmer's
        if idx < len(self.inventories):
            return self.inventories[idx] or {}
        return {}

    def farmer_inventory(self) -> dict:
        return self.inventories[0] if self.inventories else {}


def parse_observation(obs: dict) -> GameObservation:
    """Parse the raw `obs` dict into a `GameObservation`.

    `step` may be absent when an obs is constructed synthetically (e.g. in
    unit tests); it defaults to 0 rather than raising, since nothing in
    this module actually requires it.
    """
    return GameObservation(
        raw=obs,
        player=obs["player"],
        step=obs.get("step", 0),
        day=obs["day"],
        hour=obs["hour"],
    )


def tile_kind(tile: Tile) -> str:
    """Classify a tile per CONTEST.md's Observation Format."""
    if tile is None:
        return "EMPTY"
    if tile == "LOCKED":
        return "LOCKED"
    if isinstance(tile, dict):
        kind = tile.get("kind")
        if kind == "PLANT":
            return "PLANT"
        if kind == "WEED":
            return "WEED"
        if kind in ("COOP", "PASTURE"):
            return kind
    raise ValueError(f"Unrecognized tile value: {tile!r}")


def is_actionable_tile(tile: Tile) -> bool:
    """Tile actions (PLANT/WATER/BUILD_*/etc.) no-op on LOCKED tiles."""
    return tile_kind(tile) != "LOCKED"

# ---- strategy.py -------------------------------------------------
"""Rule-based Kaggriculture strategy (research.md R4, iterated per User
Story 2 and a post-submission v3 -- see research.md's Outcome / v2 note
and experiments/log.jsonl for the before/after evaluation behind v2, and
the "v3: animal husbandry" note for why this file grew a whole second
subsystem after the first real Kaggle submission).

Design, deliberately simple per constitution Principle V (Time-Boxed
Simplicity): every farmer/hand independently tends whatever tile it's
standing on (water/harvest/dig/plant), or walks toward the nearest tile
that needs attention when there's nothing to do locally. Crop choice is
driven by current `yield/tile/day * market price`, penalized by how much
of that crop is already growing (diversification, v2) so a single good's
price isn't crashed by an all-eggs-in-one-basket harvest. Sells are
batched (v2) for premium goods for the same reason.

v3 adds animal husbandry (COW/milk specifically): the farmer keeps
tending crops exactly as before, but every hired hand is now dedicated to
a build-cow-pasture -> buy/pickup/place a cow -> feed/care/harvest daily
loop, and hiring is scaled up sharply (v1/v2 capped at 2 hands/day; v3
targets up to HIRE_TARGET) to staff it. This exists because the crop-only
v2 agent, despite a 100% local win rate against every reference opponent
this project could build, scored a leaderboard public_score of 389.9 on
its first real Kaggle submission against actual competitors -- and replay
analysis of the episode we lost worst (their reward: 132,021 vs our
4,531) showed the winning opponent running 12 COW pastures + 3 SHEEP
pastures with 8 hired hands, while we ran zero animals. Fertilizing
remains out of scope for the same reasoning as before (a similar
multi-step PICKUP-then-walk logistics chain, but with a much smaller
demonstrated payoff than animals).
"""





MAX_MARKET_ORDERS = DEFAULT_CONFIG["maxMarketOrdersPerTurn"]
_DIRECTION_DELTA = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}

# v3: animal husbandry knobs. COW is the sole target animal for now --
# it's what the strongest observed real opponent scaled hardest (see the
# module docstring); SHEEP/GOOSE are a natural follow-up but out of scope
# here per Principle V (validate the biggest lever first).
TARGET_ANIMAL = "COW"
TARGET_STRUCTURES = 3
HIRE_TARGET = 3
# Hiring 6 hands costs at most 1+1+2+3+5+8=20 (Fibonacci schedule, resets
# daily) -- this reserve only needs to cover THAT, not a general safety
# buffer, or it ends up blocking cheap hiring during an unrelated cash
# crunch from land/animal spending (which is exactly what happened during
# tuning: a 300 reserve stalled re-hiring for ~20 of the 30-day season).
HIRE_MONEY_RESERVE = 50

# Cap how many units of a "premium" item (base price > $100: STRAWBERRY,
# MELON, MILK, WOOL) we sell in one turn (v2): dumping an entire shed
# stack of one of these in one SELL order crashes its price hard (their
# `above_target` > 1, per CONTEST.md's Price Function table). Staples are
# sold in full every turn as before -- they absorb gluts gently enough
# that batching isn't worth the shed-overflow risk (the shed's 100-item
# cap is shared across ALL items, so leaving unsold stock sitting around
# for non-premium goods needlessly risks discarding a later harvest).
SELL_BATCH_CAP = 15
PREMIUM_GOODS = frozenset(item for item, params in MARKET_PARAMS.items() if params["base"] > 100)


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


def _count_growing_crops(obs: GameObservation) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in obs.my_farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                counts[tile["crop"]] = counts.get(tile["crop"], 0) + 1
    return counts


def choose_best_crop(money: float, prices: dict, growing_counts: dict[str, int] | None = None) -> str | None:
    """Best crop among affordable seeds.

    Value is (yield/tile/day * current price), divided by `first_yield_day`
    as a payback-speed penalty. Without this penalty MELON (high
    steady-state yield/tile/day, but a 10-day wait before HARVEST does
    anything at all -- see strategy._is_harvest_ready) dominates the raw
    metric and the agent over-commits seed money into several melons
    before any of them can pay back, starving cash for the fast-cycling
    WHEAT/CARROT loops that would actually fund expansion early on.

    `growing_counts` (v2), when given, further divides the value by
    `1 + count already growing` -- a soft diversification penalty so the
    farm doesn't pile everything into one crop and then crash that
    crop's own sell price harvesting it all at once.
    """
    best_crop = None
    best_value = -1.0
    for crop, info in CROPS.items():
        if info["seed"] > money:
            continue
        price = prices.get(crop, 0)
        value = yield_per_tile_per_day(crop) * price / info["first_yield_day"]
        if growing_counts:
            value /= 1 + growing_counts.get(crop, 0)
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


def _find_nearest_matching(obs: GameObservation, from_pos: tuple[int, int], claimed: set, predicate) -> tuple[int, int] | None:
    board_size = len(obs.my_farm["tiles"])
    best, best_dist = None, None
    for y in range(board_size):
        for x in range(board_size):
            if (x, y) in claimed:
                continue
            if not predicate(obs.tile_at(x, y)):
                continue
            dist = abs(x - from_pos[0]) + abs(y - from_pos[1])
            if best_dist is None or dist < best_dist:
                best, best_dist = (x, y), dist
    return best


def _count_placed_animals(obs: GameObservation) -> int:
    return sum(
        1
        for row in obs.my_farm["tiles"]
        for tile in row
        if isinstance(tile, dict) and tile.get("animal")
    )


def _count_unfed_animals(obs: GameObservation) -> int:
    return sum(
        1
        for row in obs.my_farm["tiles"]
        for tile in row
        if isinstance(tile, dict) and tile.get("animal") and not tile["fed_today"]
    )


def _decide_hand_action(obs: GameObservation, pos: tuple[int, int], unit_inv: dict, claimed: set) -> list[str]:
    """v3: every hand is dedicated to the animal-husbandry loop (see module
    docstring) -- build a pasture, get a cow onto it, then keep it fed,
    cared for, and harvested, restocking from the shed as needed."""
    tile = obs.tile_at(*pos)
    kind = tile_kind(tile)

    if kind in ("COOP", "PASTURE") and isinstance(tile, dict) and tile.get("animal"):
        if not tile["fed_today"] and unit_inv.get("WHEAT", 0) > 0:
            return ["FEED"]
        if not tile["cared_today"]:
            return ["CARE"]
        if tile.get("yield_units", 0) > 0:
            return ["HARVEST"]
        if tile.get("fertilizer_available"):
            return ["COLLECT_FERTILIZER"]
        # Nothing to do on THIS tile right now (fed, cared, nothing to
        # harvest/collect) -- fall through and go be useful elsewhere.

    for animal, info in ANIMALS.items():
        if unit_inv.get(animal, 0) <= 0:
            continue
        structure = info["structure"]
        if kind == structure and isinstance(tile, dict) and not tile.get("animal"):
            return ["PLACE", animal]
        target = _find_nearest_matching(
            obs, pos, claimed,
            lambda t, s=structure: isinstance(t, dict) and t.get("kind") == s and not t.get("animal"),
        )
        if target:
            claimed.add(target)
            return _step_toward(pos, target)
        if kind == "EMPTY":
            return [f"BUILD_{structure}"]
        target = _find_nearest_matching(obs, pos, claimed, lambda t: t is None)
        if target:
            claimed.add(target)
            return _step_toward(pos, target)
        return ["PASS"]

    if unit_inv.get("WHEAT", 0) > 0:
        target = _find_nearest_matching(
            obs, pos, claimed,
            lambda t: isinstance(t, dict) and t.get("animal") and not t["fed_today"],
        )
        if target:
            claimed.add(target)
            return _step_toward(pos, target)

    target = _find_nearest_matching(
        obs, pos, claimed,
        lambda t: isinstance(t, dict)
        and t.get("animal")
        and (not t["cared_today"] or t.get("yield_units", 0) > 0 or t.get("fertilizer_available")),
    )
    if target:
        claimed.add(target)
        return _step_toward(pos, target)

    board_size = len(obs.my_farm["tiles"])
    sheds = shed_tiles(board_size)
    if pos in sheds:
        # Feeding animals that are already placed and hungry MUST outrank
        # acquiring more animals -- otherwise, as long as we're still
        # short of TARGET_STRUCTURES (routinely true while scaling up),
        # hands keep grabbing new cows at the shed instead of wheat, the
        # existing herd goes unfed for 2 consecutive days, and every
        # animal we've placed so far escapes (unrecoverable) for nothing.
        if obs.shed.get("WHEAT", 0) > 0 and _count_unfed_animals(obs) > 0:
            return ["PICKUP", "WHEAT", 1]
        pending_animals = obs.shed.get(TARGET_ANIMAL, 0) + sum(
            inv.get(TARGET_ANIMAL, 0) for inv in obs.inventories
        )
        # Count LIVE animals, not built structures: a structure stays
        # built forever even after its animal starves and escapes (an
        # empty PASTURE tile never reverts to None), so gating on
        # structure count alone means a dead animal is never replaced
        # once we've ever reached TARGET_STRUCTURES -- confirmed via
        # replay: 3 cows placed on day 0-1, all escaped by day 3 (no
        # hands to feed them that day), and the shed's spare cow then sat
        # unused for the rest of the season because structures_owned(3)
        # + pending(1) already read as "enough".
        if _count_placed_animals(obs) + pending_animals < TARGET_STRUCTURES and obs.shed.get(TARGET_ANIMAL, 0) > 0:
            return ["PICKUP", TARGET_ANIMAL, 1]
        if obs.shed.get("WHEAT", 0) > 0 and _count_placed_animals(obs) > 0:
            return ["PICKUP", "WHEAT", 1]
        return ["PASS"]

    shed_target = min(sheds, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))
    if shed_target in claimed:
        return ["PASS"]
    claimed.add(shed_target)
    return _step_toward(pos, shed_target)


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
    shed = obs.shed
    # v3: keep enough WHEAT in the shed to feed every placed animal today
    # rather than selling all of it -- feeding needs 1 WHEAT/animal/day
    # picked up from the shed (see _decide_hand_action).
    placed_animals = _count_placed_animals(obs)
    for item, qty in shed.items():
        if qty <= 0 or item not in MARKET_PARAMS:
            # Animals (COW/SHEEP/GOOSE) pass through the shed too, between
            # BUY_ANIMAL and a hand's PICKUP -- they aren't real market
            # products (not in MARKET_PARAMS) and must never be sold, or a
            # freshly bought animal gets sold right back out from under
            # the hand that was about to go collect it.
            continue
        sellable = qty - placed_animals if item == "WHEAT" else qty
        if sellable <= 0:
            continue
        cap = SELL_BATCH_CAP if item in PREMIUM_GOODS else sellable
        orders.append(["SELL", item, min(sellable, cap)])

    money = obs.my_farm["money"]
    seeds = obs.seeds
    if target_crop and seeds.get(target_crop, 0) == 0:
        cost = CROPS[target_crop]["seed"]
        if money >= cost:
            orders.append(["BUY_SEED", target_crop, 1])

    if obs.hour == 0:
        hires_today = obs.my_farm.get("hires_today", 0)
        # HIRE cost follows a Fibonacci schedule per hire *today*
        # (1, 1, 2, 3, 5, 8, ... * farmHandCostMult) and resets daily, so
        # this queues several HIRE orders in the same turn (previously
        # just one), each cheap, up to HIRE_TARGET hands -- provided we
        # still keep HIRE_MONEY_RESERVE unspent for everything else this
        # turn also wants to buy.
        if money >= HIRE_MONEY_RESERVE:
            orders.extend(["HIRE"] for _ in range(hires_today, HIRE_TARGET))

    unlocked = obs.unlocked_quadrants()
    if len(unlocked) < 4:
        next_cost = [1000, 2000, 4000][len(unlocked) - 1]
        if money >= next_cost * 2:
            orders.append(["BUY_LAND"])

    # Gate on LIVE animals + pending, not built structures -- see the
    # matching comment in _decide_hand_action for why (a starved,
    # escaped animal must be replaced, and structure count alone can't
    # tell that apart from "target already met").
    pending_animals = shed.get(TARGET_ANIMAL, 0) + sum(inv.get(TARGET_ANIMAL, 0) for inv in obs.inventories)
    if _count_placed_animals(obs) + pending_animals < TARGET_STRUCTURES and money >= ANIMALS[TARGET_ANIMAL]["cost"]:
        orders.append(["BUY_ANIMAL", TARGET_ANIMAL, 1])

    if placed_animals > 0 and shed.get("WHEAT", 0) < placed_animals:
        needed = placed_animals - shed.get("WHEAT", 0)
        wheat_price = obs.market_prices.get("WHEAT", CROPS["WHEAT"]["seed"])
        if money >= wheat_price * needed:
            orders.append(["BUY_PRODUCT", "WHEAT", needed])

    return orders[:MAX_MARKET_ORDERS]


def baseline_strategy(obs: GameObservation) -> dict:
    prices = obs.market_prices
    money = obs.my_farm["money"]
    target_crop = choose_best_crop(money, prices, _count_growing_crops(obs))

    plant_budget = {target_crop: obs.seeds.get(target_crop, 0)} if target_crop else {}
    claimed: set = set()

    farmer_action = _decide_unit_action(obs, obs.farmer_position(), target_crop, plant_budget, claimed)
    hands_actions = [
        _decide_hand_action(obs, pos, obs.hand_inventory(i), claimed)
        for i, pos in enumerate(obs.hand_positions())
    ]

    return {
        "farmer": farmer_action,
        "hands": hands_actions,
        "market": _market_orders(obs, target_crop),
    }

# ---- agent.py ----------------------------------------------------
"""Kaggle Simulations entry point for the Kaggriculture agent.

Matches the confirmed single-argument contract (`def agent(obs) -> dict`,
see contracts/agent-interface.md). `evaluation/bundle_submission.py`
inlines this module (and its imports) into `submissions/<version>/main.py`
for actual Kaggle submission.

IMPORTANT: when `kaggle_environments` loads an agent from a file path
(exactly how both local batch evaluation and a real Kaggle submission
load it -- see `evaluation/run_batch.py` and `AGENTS.md`), it execs the
file and picks the LAST callable defined at module level as the agent,
not necessarily whatever is named `agent` (`kaggle_environments/agent.py`:
`get_last_callable`). `agent()` MUST therefore stay the last top-level
def in this file -- an earlier version imported `strategy.py` in a
try/except block below `agent()` to wire it in, which made
`baseline_strategy` (not `agent`) the last callable, silently reducing
the whole file to a no-op PASS agent whenever loaded by path. Keeping the
strategy import at the top and `agent()` as the only def avoids the trap.
"""





_PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def agent(obs: dict) -> dict:
    """Return this player's action for the current turn.

    Never raises: any strategy failure falls back to a legal PASS action,
    since a crash forfeits the match (see contracts/agent-interface.md).
    """
    try:
        parsed = parse_observation(obs)
        action = baseline_strategy(parsed)
    except Exception:
        return dict(_PASS_ACTION)
    if not isinstance(action, dict) or "farmer" not in action:
        return dict(_PASS_ACTION)
    action.setdefault("hands", [])
    action.setdefault("market", [])
    return action

