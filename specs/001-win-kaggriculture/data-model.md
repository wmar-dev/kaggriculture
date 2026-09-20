# Phase 1 Data Model: Win Kaggriculture Competition

Entities below combine the spec's Key Entities with the concrete
observation shape documented in `CONTEST.md`. This is a design reference
for implementation, not the wire format itself — the wire format is the
raw `obs`/action dicts specified in `CONTEST.md` and mirrored in
`contracts/agent-interface.md`.

## GameObservation (parsed from the raw `obs` dict each turn)

| Field | Type | Notes |
| --- | --- | --- |
| player | int (0/1) | Which side this agent is playing. |
| day | int | 0-indexed in-game day (0–29). |
| hour | int | 0-indexed turn within the day (0–23). |
| farms | [FarmState, FarmState] | Indexed by player id; both public. |
| market | MarketState | Shared. |
| town | TownState | Shared. |
| private | PrivateState | This player only. |

## FarmState (public, one per player)

| Field | Type | Notes |
| --- | --- | --- |
| money | float | Bank balance — the quantity the agent ultimately maximizes (spec FR-009). |
| tiles | Tile[boardSize][boardSize] | `tiles[y][x]`; see Tile below. |
| farmer | (x, y) | Main farmer position. |
| hands | (x, y)[] | Hired hands for the current day only. |
| unlocked_quadrants | subset of {NW, NE, SW, SE} | Determines usable board area. |
| hires_today | int | Drives the Fibonacci `HIRE` cost for the next hire. |

## Tile (one board cell)

A tagged union, per `CONTEST.md`'s Observation Format:

- `None` — empty, unlocked.
- `"LOCKED"` — unbought quadrant; passable but all tile actions no-op.
- **Plant**: `crop`, `planted_day`, `watered_today`,
  `consecutive_unwatered` (≥2 → weed), `yield_units`, `max_lifespan_step`,
  `fertilized_until_day`.
- **Weed**: no fields beyond `kind`.
- **Animal structure** (coop/pasture): `animal` (or `None`), `placed_day`,
  `yield_units`, `fed_today`, `consecutive_unfed` (≥2 → escape),
  `cared_today`, `fertilizer_available`, `pending_care_bonus`.

## MarketState (shared)

| Field | Type | Notes |
| --- | --- | --- |
| inventory | {resource: int} | Drives the dynamic price curve per `CONTEST.md`'s Price Function. |
| prices | {resource: int} | Current sell price per resource; floored at $1. |

## TownState (shared)

| Field | Type | Notes |
| --- | --- | --- |
| unlocked_shops | string[] | May repeat; each entry independently consumes matching products every `townShopSellInterval` turns. |

## PrivateState (this player only)

| Field | Type | Notes |
| --- | --- | --- |
| shed | {item: int} | Capped at `shedCapacity` (default 100), excluding seeds. |
| seeds | {crop: int} | Purchased-but-unplanted seed counts. |
| inventories | Inventory[] | `[0]` is the main farmer; rest are hired hands, current-day only. |

## ActionSet (what the agent returns each turn)

| Field | Type | Notes |
| --- | --- | --- |
| farmer / hand actions | one action string (+ args) per controlled unit | Movement, plant/water/harvest/fertilize, animal care/feed/place, shed pickup/drop/place, build/dig, or PASS. |
| market | ordered list of up to `maxMarketOrdersPerTurn` (default 10) orders | BUY_SEED / BUY_ANIMAL / BUY_PRODUCT / SELL / HIRE / BUY_LAND; extras beyond the cap are silently dropped. |

## Strategy-layer entities (this implementation's own design, not part of the wire contract)

- **AgentVersion**: a named, git-committed snapshot of `src/kaggriculture_agent/` plus the bundled `submissions/<version>/agent.py` it produces. Maps directly to spec's "Agent" entity.
- **EvaluationResult**: output of one local batch run — opponent name, seasons played, win/loss/tie counts, mean/median end-of-season money for both sides. Maps to spec's "Match / Episode" aggregate.
- **ExperimentLogEntry** (`experiments/log.jsonl`, one JSON object per line): `{timestamp, agent_version, commit_sha, hypothesis, evaluation_results: EvaluationResult[], kaggle_result: {submitted_at, public_score, rank} | null, decision: "adopt" | "reject" | "investigate"}`. Maps to spec's "Experiment Log" entity and satisfies FR-003/FR-008.
- **CompetitionRuleset**: the fixed, non-code facts governing what's legal — `CONTEST.md`'s game mechanics plus Kaggle's own competition rules (submission caps, deadline, team rules). Not stored as application data; referenced as documentation (`CONTEST.md`, and once confirmed, the Kaggle rules page) per spec's "Competition Ruleset" entity.
