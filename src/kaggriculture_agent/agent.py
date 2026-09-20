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

from __future__ import annotations

from kaggriculture_agent.observation import parse_observation
from kaggriculture_agent.strategy import baseline_strategy

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
