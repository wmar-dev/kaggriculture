"""Typed-ish parsing helpers over the raw Kaggriculture `obs` dict.

The wire format is plain dicts (see contracts/agent-interface.md and
data-model.md); this module doesn't change that shape, it just gives the
strategy layer named, testable accessors instead of repeating dict lookups
and tile-kind checks everywhere.
"""

from __future__ import annotations

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
