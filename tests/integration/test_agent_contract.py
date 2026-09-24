"""Contract tests for the Kaggriculture agent (contracts/agent-interface.md).

The full-episode test deliberately loads the agent BY FILE PATH, exactly
as `evaluation/run_batch.py` and a real Kaggle submission do -- this is
what caught the "last callable in the file, not necessarily `agent`"
loader trap during development (see the note at the top of
src/kaggriculture_agent/agent.py). A test that instead imported `agent`
directly as a Python callable would have missed that bug entirely.
"""

from __future__ import annotations

from pathlib import Path

from kaggle_environments import make

from kaggriculture_agent.agent import agent
from kaggriculture_agent.constants import DEFAULT_CONFIG

AGENT_PATH = str(Path(__file__).resolve().parent.parent.parent / "src" / "kaggriculture_agent" / "agent.py")


def test_full_episode_completes_without_error_vs_random():
    env = make("kaggriculture", configuration={"episodeSteps": 96})
    env.run([AGENT_PATH, "random"])
    final = env.steps[-1]
    our_status = final[0].status
    assert our_status == "DONE", f"agent did not finish cleanly (status={our_status!r})"


def test_full_episode_completes_without_error_vs_starter():
    env = make("kaggriculture", configuration={"episodeSteps": 96})
    env.run([AGENT_PATH, "starter"])
    final = env.steps[-1]
    our_status = final[0].status
    assert our_status == "DONE", f"agent did not finish cleanly (status={our_status!r})"


def test_agent_is_the_last_callable_loaded_from_the_file():
    """Regression test for the loader trap described in agent.py's module
    docstring: whatever `kaggle_environments.agent.get_last_callable`
    would pick from this file must be the real `agent` entry point.
    """
    import sys

    raw = Path(AGENT_PATH).read_text()
    code_object = compile(raw, AGENT_PATH, "exec")
    namespace: dict = {}
    exec_dir = str(Path(AGENT_PATH).parent)
    sys.path.append(exec_dir)
    try:
        exec(code_object, namespace)
    finally:
        sys.path.pop()
    callables = [v for k, v in namespace.items() if callable(v) and not k.startswith("__")]
    assert callables, "no callables found in agent.py"
    assert callables[-1].__name__ == "agent"


def _minimal_obs(player: int = 0) -> dict:
    tiles = [[None for _ in range(10)] for _ in range(10)]
    farm = {
        "money": 3000,
        "tiles": tiles,
        "farmer": [4, 4],
        "hands": [],
        "unlocked_quadrants": ["NW"],
        "hires_today": 0,
    }
    return {
        "player": player,
        "step": 0,
        "day": 0,
        "hour": 0,
        "farms": [farm, dict(farm)],
        "market": {"inventory": {}, "prices": {}},
        "town": {"unlocked_shops": []},
        "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
    }


def test_agent_never_returns_empty_response():
    action = agent(_minimal_obs())
    assert isinstance(action, dict)
    assert "farmer" in action and isinstance(action["farmer"], list) and action["farmer"]


def test_agent_response_has_hands_and_market_keys():
    action = agent(_minimal_obs())
    assert isinstance(action.get("hands"), list)
    assert isinstance(action.get("market"), list)


def test_agent_never_crashes_on_a_malformed_observation():
    # Missing most fields entirely -- agent() must fall back to PASS, not raise.
    action = agent({"player": 0, "day": 0, "hour": 0, "farms": [{}, {}]})
    assert action["farmer"] == ["PASS"]


def test_agent_bounds_market_orders_to_the_configured_limit():
    obs = _minimal_obs()
    # Fill the shed with many distinct sellable items to try to blow past the cap.
    obs["private"]["shed"] = {f"ITEM_{i}": 1 for i in range(20)}
    action = agent(obs)
    assert len(action["market"]) <= DEFAULT_CONFIG["maxMarketOrdersPerTurn"]


def test_agent_stays_within_internal_per_turn_time_budget():
    """research.md R1: designed against an internal <=50ms/turn budget,
    a large safety margin under the confirmed real actTimeout of 1s.
    Measured across a real (short) episode, not synthetic obs, so board
    scans (e.g. the animal-tile searches) run against a realistically populated
    farm rather than an empty one.
    """
    import time

    from kaggriculture_agent.constants import INTERNAL_TURN_BUDGET_SECONDS

    env = make("kaggriculture", configuration={"episodeSteps": 48})
    env.reset()
    durations = []
    for _ in range(48):
        obs = env.state[0].observation
        start = time.perf_counter()
        action = agent(obs)
        durations.append(time.perf_counter() - start)
        if env.done:
            break
        # env.step() takes literal actions for both agents (unlike env.run(),
        # it does not resolve "random" as a named agent) -- the opponent's
        # own play doesn't matter for this timing test, so it just PASSes.
        env.step([action, {"farmer": ["PASS"], "hands": [], "market": []}])
    assert max(durations) < INTERNAL_TURN_BUDGET_SECONDS, (
        f"slowest turn took {max(durations) * 1000:.1f}ms, "
        f"over the {INTERNAL_TURN_BUDGET_SECONDS * 1000:.0f}ms internal budget"
    )
