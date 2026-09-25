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


def test_units_are_not_blocked_from_the_shed_by_another_units_claim():
    """v14 regression: the shed is a shared logistics hub, not an
    exclusive work site. `claimed` must not gate travel to it.

    Claiming it idled 22.5% of ALL unit-turns -- two thirds of v13's
    idle rate -- because a unit with nothing else to do would stand
    still whenever another unit was already walking to the shed. That
    is also why adding hands never improved feeding.
    """
    from kaggriculture_agent.constants import shed_tiles
    from kaggriculture_agent.observation import parse_observation
    from kaggriculture_agent.strategy import _decide_hand_action

    board = [[None for _ in range(10)] for _ in range(10)]
    obs = parse_observation(
        {
            "player": 0,
            "step": 0,
            "day": 3,
            "hour": 5,
            "farms": [
                {
                    "money": 1000,
                    "tiles": board,
                    "farmer": [0, 0],
                    "hands": [],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                },
                {"money": 1000, "tiles": board, "farmer": [9, 9], "hands": []},
            ],
            "market": {"inventory": {}, "prices": {}},
            "town": {"unlocked_shops": []},
            "private": {"shed": {"WHEAT": 5}, "seeds": {}, "inventories": [{}]},
        }
    )
    # Every shed tile already claimed by other units this turn.
    claimed = set(shed_tiles(10))
    action = _decide_hand_action(obs, (0, 0), {}, claimed)
    assert action != ["PASS"], "unit idled instead of heading for the shed"


def test_placement_duty_never_selects_an_excluded_index():
    """v16 regression: _placement_duty_index must never return an index
    in `exclude`.

    Crop workers ignore the placement_duty flag entirely, so if the
    nearest-to-shed unit happens to be a crop worker, picking it silently
    wastes the assignment -- no herd unit ever collects the pending
    animal. This was a real bug in an earlier attempt at a joint
    crop+animal subsystem.
    """
    from kaggriculture_agent.observation import parse_observation
    from kaggriculture_agent.strategy import _placement_duty_index

    board = [[None for _ in range(10)] for _ in range(10)]
    obs = parse_observation(
        {
            "player": 0,
            "step": 0,
            "day": 5,
            "hour": 3,
            "farms": [
                {
                    "money": 1000,
                    "tiles": board,
                    # Hand 0 (index 1) sits ON the shed -- the nearest
                    # possible unit -- but is excluded as a crop worker.
                    "farmer": [9, 9],
                    "hands": [[4, 4], [8, 8]],
                    "unlocked_quadrants": ["NW"],
                    "hires_today": 0,
                },
                {"money": 1000, "tiles": board, "farmer": [0, 0], "hands": []},
            ],
            "market": {"inventory": {}, "prices": {}},
            "town": {"unlocked_shops": []},
            "private": {
                "shed": {"COW": 1},  # a pending animal is waiting
                "seeds": {},
                "inventories": [{}, {}, {}],
            },
        }
    )
    duty = _placement_duty_index(obs, exclude={1})
    assert duty != 1, "excluded index was selected for placement duty"


def test_plot_tiles_never_includes_land_beyond_max_quadrants():
    """v16 regression: an earlier version of plot_tiles anchored on the
    tile FURTHEST from the shed, which selects the SE quadrant -- land
    MAX_QUADRANTS=3 never actually unlocks. The entire plot sat on
    permanently locked ground and zero crops were ever planted.
    """
    from kaggriculture_agent.strategy import MAX_QUADRANTS, QUADRANTS, plot_tiles

    board_size = 10
    half = board_size // 2
    ownable = set(QUADRANTS[:MAX_QUADRANTS])

    def quadrant(x, y):
        return ("N" if y < half else "S") + ("W" if x < half else "E")

    for tile in plot_tiles(board_size):
        assert quadrant(*tile) in ownable, f"{tile} is in a quadrant we never buy"


def test_plot_tiles_are_spatially_contiguous():
    """v16 regression: sorting candidate tiles by shed-distance alone
    picks the right SET of tiles but not a spatially contiguous ORDER,
    so slicing the result into per-worker blocks (worker_block) produced
    blocks spanning opposite sides of the ring. Each worker's block
    should be a short walk from itself, not the whole board.
    """
    from kaggriculture_agent.strategy import plot_tiles, worker_block

    plot = plot_tiles(10)
    assert len(plot) >= 4, "test needs a non-trivial plot to be meaningful"
    # A 3-way split of a well-ordered ring should keep each worker's
    # tiles within a small neighbourhood, not scattered across the board
    # (a scattered block's internal span approaches the board's diameter).
    for worker in range(3):
        block = worker_block(plot, worker, 3)
        if len(block) < 2:
            continue
        span = max(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a in block for b in block)
        assert span <= 8, f"worker {worker}'s block is scattered (internal span {span}): {block}"


def _obs_with_animal(tile: dict, day: int, prices: dict):
    board = [[None for _ in range(10)] for _ in range(10)]
    board[0][0] = tile
    farm = {
        "money": 1000,
        "tiles": board,
        "farmer": [9, 9],
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }
    return parse_observation(
        {
            "player": 0,
            "step": 0,
            "day": day,
            "hour": 5,
            "farms": [farm, dict(farm)],
            "market": {"inventory": {}, "prices": prices},
            "town": {"unlocked_shops": []},
            "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        }
    )


def _cow(**kw):
    tile = {"kind": "PASTURE", "animal": "COW", "placed_day": 0, "fed_today": False,
            "cared_today": False, "consecutive_unfed": 0, "yield_units": 0}
    tile.update(kw)
    return tile


def test_should_feed_skips_optional_feed_when_product_is_crashed():
    """v18: the engine produces an animal's base unit whether or not it
    was fed; an off-schedule feed only banks one bonus unit, so it is not
    worth a wheat when milk trades far below wheat."""
    from kaggriculture_agent.strategy import _should_feed

    # COW first_yield_day 8, interval 2: day 10 -> tonight is day 11, a
    # non-production night.
    obs = _obs_with_animal(_cow(), day=10, prices={"MILK": 5, "WHEAT": 50})
    assert _should_feed(obs, obs.tile_at(0, 0)) is False


def test_should_feed_always_feeds_before_an_escape():
    from kaggriculture_agent.strategy import _should_feed

    obs = _obs_with_animal(_cow(consecutive_unfed=1), day=10, prices={"MILK": 5, "WHEAT": 50})
    assert _should_feed(obs, obs.tile_at(0, 0)) is True


def test_should_feed_always_feeds_on_a_production_night():
    """A fed production night is what cashes in the banked care bonus."""
    from kaggriculture_agent.strategy import _should_feed

    obs = _obs_with_animal(_cow(), day=9, prices={"MILK": 5, "WHEAT": 50})
    assert _should_feed(obs, obs.tile_at(0, 0)) is True


def test_should_feed_feeds_when_product_is_valuable():
    from kaggriculture_agent.strategy import _should_feed

    obs = _obs_with_animal(_cow(), day=10, prices={"MILK": 160, "WHEAT": 30})
    assert _should_feed(obs, obs.tile_at(0, 0)) is True


def test_should_feed_never_feeds_on_the_final_day():
    from kaggriculture_agent.strategy import SEASON_DAYS, _should_feed

    obs = _obs_with_animal(_cow(consecutive_unfed=1), day=SEASON_DAYS - 1, prices={"MILK": 160, "WHEAT": 30})
    assert _should_feed(obs, obs.tile_at(0, 0)) is False
