# Contract: Kaggle Simulations Agent Interface

This is the external interface the submitted `submissions/<version>/agent.py`
must implement — the only "contract" this project exposes, since it is a
single-file Kaggle Simulations submission, not a service with an API.
Source of truth for the shapes below is `CONTEST.md`; this file restates
them as an explicit input/output contract for implementation and testing.

## Entry point

```python
def agent(obs: dict, config: dict) -> dict:
    """Return this player's actions for the current turn."""
```

- Called once per turn (`episodeSteps`, default 720; 24 turns/day × 30
  days) by the `kaggle_environments` runner, alternating/concurrent with
  the opponent's own `agent` call.
- MUST return within the per-turn time budget (see
  `research.md` R1 — TODO(TURN_TIME_LIMIT) pending confirmation; designed
  against an internal ≤50ms target).
- MUST NOT raise, hang, or import anything unavailable in Kaggle's sandbox
  (no local package imports beyond the standard library once bundled — see
  `research.md` R2).

## Input: `obs`

Matches `CONTEST.md`'s "Observation Format" exactly — see `data-model.md`
for the parsed/typed view. Top-level shape:

```python
{
  "player": int,           # 0 or 1
  "day":    int,
  "hour":   int,
  "farms":  [farm, farm],  # public, indexed by player id
  "market": {"inventory": {...}, "prices": {...}},
  "town":   {"unlocked_shops": [...]},
  "private": {"shed": {...}, "seeds": {...}, "inventories": [...]},
}
```

## Output: actions dict

```python
{
  "farmer": [ACTION, *args],           # required: one action for the main farmer
  "hands":  [[ACTION, *args], ...],    # optional: one entry per currently-hired hand, same order as obs.farms[player].hands
  "market": [[ORDER, *args], ...],     # optional: up to maxMarketOrdersPerTurn (default 10); extras are silently dropped
}
```

### Legal `farmer` / `hands` actions

`NORTH | SOUTH | EAST | WEST | PICKUP <item> [n] | DROP | PLANT <crop> | WATER | HARVEST | FERTILIZE | PLACE <item> [n] | FEED | COLLECT_FERTILIZER | CARE | BUILD_COOP | BUILD_PASTURE | DIG | PASS`

Invalid/no-op cases (per `CONTEST.md`) that the agent MUST tolerate
producing (not crash on) rather than rely on the engine to reject
gracefully in every case: moves off-board, tile actions on a `LOCKED`
tile, over-committing a scarce seed across multiple units in one turn
(none get planted), `DIG` on an occupied coop/pasture.

### Legal `market` orders

`BUY_SEED <item> <n> | BUY_ANIMAL <item> <n> | BUY_PRODUCT <WHEAT|FERTILIZER> <n> | SELL <item> <n> | HIRE | BUY_LAND`

## Contract-level acceptance tests (see `quickstart.md` for how to run these)

1. **Full-episode smoke test**: `agent` vs. a reference opponent completes
   all `episodeSteps` turns with no exception, no illegal-action penalty,
   and no timeout, for at least one full simulated season.
2. **Never-empty response**: `agent` always returns a dict with at least a
   `farmer` key (defaulting to `["PASS"]` if there is nothing else to do),
   never `None` or a missing key.
3. **Bounded market orders**: `agent` never emits more than
   `maxMarketOrdersPerTurn` market orders in a single turn (avoids relying
   on silent truncation as the actual limiting behavior).
