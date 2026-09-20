"""Unit tests for strategy.py, including the v2 iteration (User Story 2):
crop diversification and premium-good sell batching."""

from __future__ import annotations

from kaggriculture_agent.observation import parse_observation
from kaggriculture_agent.strategy import (
    _is_harvest_ready,
    _market_orders,
    choose_best_crop,
)


def test_is_harvest_ready_false_before_first_yield_day():
    tile = {"crop": "MELON", "planted_day": 0, "yield_units": 1}
    assert _is_harvest_ready(tile, current_day=5) is False  # MELON first_yield_day=10


def test_is_harvest_ready_true_once_first_yield_day_reached():
    tile = {"crop": "MELON", "planted_day": 0, "yield_units": 1}
    assert _is_harvest_ready(tile, current_day=10) is True


def test_is_harvest_ready_false_when_no_yield_units():
    tile = {"crop": "WHEAT", "planted_day": 0, "yield_units": 0}
    assert _is_harvest_ready(tile, current_day=10) is False


def test_choose_best_crop_prefers_fast_payback_over_raw_yield():
    # MELON has much higher raw yield/tile/day * price, but a 10-day
    # first_yield_day; WHEAT pays back in 2 days. At comparable prices
    # WHEAT should win once the payback-speed penalty is applied.
    prices = {"WHEAT": 25, "MELON": 250}
    best = choose_best_crop(money=3000, prices=prices)
    assert best == "WHEAT"


def test_choose_best_crop_respects_affordability():
    prices = {"WHEAT": 25, "CARROT": 35}
    best = choose_best_crop(money=15, prices=prices)  # can't afford CARROT (20) or more
    assert best == "WHEAT"


def test_choose_best_crop_diversification_penalty_can_flip_choice():
    prices = {"WHEAT": 25, "CARROT": 200}  # CARROT artificially inflated so it'd normally win
    without_counts = choose_best_crop(money=3000, prices=prices)
    assert without_counts == "CARROT"
    with_heavy_carrot_growing = choose_best_crop(money=3000, prices=prices, growing_counts={"CARROT": 10})
    assert with_heavy_carrot_growing == "WHEAT"


def _obs_with_shed(shed: dict):
    farm = {
        "money": 1000,
        "tiles": [[None]],
        "farmer": [0, 0],
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }
    return parse_observation(
        {
            "player": 0,
            "day": 0,
            "hour": 1,  # avoid the hour==0 HIRE order for a cleaner assertion
            "farms": [farm, dict(farm)],
            "market": {"inventory": {}, "prices": {}},
            "town": {"unlocked_shops": []},
            "private": {"shed": shed, "seeds": {}, "inventories": [{}]},
        }
    )


def test_market_orders_sells_staples_in_full():
    obs = _obs_with_shed({"WHEAT": 40})
    orders = _market_orders(obs, target_crop=None)
    assert ["SELL", "WHEAT", 40] in orders


def test_market_orders_batches_premium_goods():
    obs = _obs_with_shed({"MELON": 40})
    orders = _market_orders(obs, target_crop=None)
    sell_orders = [o for o in orders if o[0] == "SELL"]
    assert sell_orders == [["SELL", "MELON", 15]]


def test_market_orders_sells_small_premium_stock_in_full():
    obs = _obs_with_shed({"MELON": 3})
    orders = _market_orders(obs, target_crop=None)
    assert ["SELL", "MELON", 3] in orders
