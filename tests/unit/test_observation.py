"""Unit tests for observation parsing (data-model.md Tile variants)."""

from __future__ import annotations

import pytest

from kaggriculture_agent.observation import is_actionable_tile, parse_observation, tile_kind


def _base_obs(tiles):
    farm = {
        "money": 1234,
        "tiles": tiles,
        "farmer": [1, 2],
        "hands": [[3, 4]],
        "unlocked_quadrants": ["NW"],
        "hires_today": 1,
    }
    return {
        "player": 0,
        "step": 5,
        "day": 1,
        "hour": 3,
        "farms": [farm, dict(farm)],
        "market": {"inventory": {"WHEAT": 9000}, "prices": {"WHEAT": 30}},
        "town": {"unlocked_shops": ["BAKERY"]},
        "private": {"shed": {"WHEAT": 2}, "seeds": {"CARROT": 1}, "inventories": [{}]},
    }


def test_parse_observation_basic_fields():
    obs = _base_obs([[None]])
    parsed = parse_observation(obs)
    assert parsed.player == 0
    assert parsed.step == 5
    assert parsed.day == 1
    assert parsed.hour == 3
    assert parsed.my_farm["money"] == 1234
    assert parsed.farmer_position() == (1, 2)
    assert parsed.hand_positions() == [(3, 4)]
    assert parsed.shed == {"WHEAT": 2}
    assert parsed.seeds == {"CARROT": 1}
    assert parsed.market_prices == {"WHEAT": 30}
    assert parsed.unlocked_shops == ["BAKERY"]


def test_parse_observation_defaults_step_when_absent():
    obs = _base_obs([[None]])
    del obs["step"]
    assert parse_observation(obs).step == 0


@pytest.mark.parametrize(
    "tile,expected_kind,expected_actionable",
    [
        (None, "EMPTY", True),
        ("LOCKED", "LOCKED", False),
        ({"kind": "PLANT", "crop": "WHEAT"}, "PLANT", True),
        ({"kind": "WEED"}, "WEED", True),
        ({"kind": "COOP", "animal": None}, "COOP", True),
        ({"kind": "PASTURE", "animal": "SHEEP"}, "PASTURE", True),
    ],
)
def test_tile_kind_and_actionability(tile, expected_kind, expected_actionable):
    assert tile_kind(tile) == expected_kind
    assert is_actionable_tile(tile) is expected_actionable


def test_tile_kind_rejects_unrecognized_value():
    with pytest.raises(ValueError):
        tile_kind({"kind": "SOMETHING_ELSE"})


def test_tile_at_indexes_tiles_as_y_then_x():
    tiles = [[None, "LOCKED"], [{"kind": "WEED"}, None]]
    obs = _base_obs(tiles)
    parsed = parse_observation(obs)
    assert parsed.tile_at(0, 0) is None
    assert parsed.tile_at(1, 0) == "LOCKED"
    assert parsed.tile_at(0, 1) == {"kind": "WEED"}
