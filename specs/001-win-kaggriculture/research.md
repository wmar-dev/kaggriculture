# Phase 0 Research: Win Kaggriculture Competition

## R1: Per-turn / per-episode time limit — RESOLVED (confirmed from source)

**Update**: `kaggle_environments` (PyPI `kaggle-environments==1.32.7`)
actually bundles a working `kaggriculture` environment
(`kaggle_environments/envs/kaggriculture/`), including `kaggriculture.py`
(the real engine, 1086 lines), `kaggriculture.json` (the real
configuration schema), `README.md` (byte-identical to the competitor's
`CONTEST.md`), and `AGENTS.md` (a submission how-to guide). This resolves
the unknown directly from ground truth instead of needing a conservative
guess.

- **Confirmed values** (`kaggriculture.json`): `actTimeout: 1` (1 second
  per turn) and `remainingOverageTime: 60` (60-second cumulative overage
  pool for the whole episode) — both far above the ≤50ms internal design
  target originally chosen as a placeholder; that target remains valid
  and is now known to carry a very large safety margin rather than being
  an unconfirmed guess.
- **Also confirmed**: three built-in reference agents ship with the
  environment — `"pass"` (always PASS), `"random"` (weighted-random legal
  actions), and `"starter"` (a deterministic single-tile carrot loop,
  never expands land, never hires, never raises animals). These are
  addressable by name directly in `kaggle_environments.make(...).run([...])`
  without writing custom opponent files.
- **Rationale for using the bundled environment as ground truth**: it is
  the actual competition engine (not a re-implementation), so building
  and evaluating against it removes all guesswork about rules,
  observation shape, and action legality — strictly better than the
  conservative-default approach originally planned.
- **Impact on research.md R3 (opponent pool)**: superseded — see R3
  below.

## R2: Kaggle Simulations submission packaging

**Question**: How should a multi-module local package become the single
file Kaggle simulation submissions require?

- **Decision**: Keep agent decision logic in normal importable modules
  under `src/kaggriculture_agent/` during development (for testability),
  and add a small bundling step (`evaluation/` tooling, detailed in
  tasks.md) that inlines/concatenates those modules into one
  self-contained `submissions/<version>/main.py` with a single
  `agent(obs)` entry point and no local imports, matching the confirmed
  `kaggle_environments` agent contract (see R1 and
  `contracts/agent-interface.md`).
- **Rationale**: Writing and testing decision logic as one large file is
  error-prone and hard to unit-test; nearly every prior Kaggle Simulations
  competition solution uses a "develop modular, bundle flat" pattern for
  exactly this reason.
- **Alternatives considered**: Write the agent as a single flat file from
  day one — rejected, hurts testability/readability for no real benefit
  since bundling is a small, one-time tooling cost.

## R3: Local evaluation opponent pool — UPDATED (built-ins confirmed available)

**Question**: What opponents should the local batch-evaluation harness use
to produce a trustworthy win-rate/score signal (constitution Principle II,
spec FR-002)?

- **Decision**: Use the environment's own built-in `"random"` and
  `"starter"` agents (see R1) as the first two reference opponents —
  no custom opponent files needed for those. Add one custom, slightly
  stronger `GREEDY` heuristic opponent (plants the best-affordable
  `Yield/tile/day` crop, sells promptly) so there is a mid-tier target
  between the weak `"starter"` baseline and whatever our own agent
  becomes. Add the **previous submitted version** of our own agent as a
  fourth, self-play opponent once one exists. Track results against all
  available opponents per experiment-log entry.
- **Rationale**: `"starter"` never expands past one tile and never uses
  animals/hands/land, so beating it is a low bar; `"random"` is a
  robustness check, not a strategy benchmark. `GREEDY` and self-play
  against the previous version are what actually keep the local signal
  honest about whether a change is really an improvement (Principle II).
- **Alternatives considered**: Evaluate only via public leaderboard
  submissions — rejected outright, this is exactly the untrustworthy,
  submission-budget-burning pattern constitution Principle II forbids.
  Skip `GREEDY` and rely only on the two built-ins — rejected, both
  built-ins are weak enough that a mediocre agent could beat both while
  still losing badly to real competitors.

## R4: Baseline strategy shape

**Question**: What should the first (P1, baseline) strategy actually do?

- **Decision**: A deterministic, rule-based strategy driven directly by
  the economics already tabulated in `CONTEST.md` (Object Types table,
  Price Function table): prioritize buying land and labor only when
  affordable ROI is clear, plant/raise the currently-best
  `Yield/tile/day` × current-market-price combination that fits the
  budget, always water/feed/care for everything owned (avoiding the
  weed/escape failure modes called out in Edge Cases), and sell
  opportunistically while avoiding crashing the market price of any single
  good (batch sells informed by the documented price-decay curves).
- **Rationale**: This requires no training data or search infrastructure
  (fastest possible path to a valid, non-trivial P1 baseline, per
  constitution Principle V), and is directly falsifiable/improvable once
  measured against the R3 opponent pool.
- **Alternatives considered**: Start directly with a learned/search-based
  policy (e.g., reinforcement learning, Monte Carlo tree search) —
  rejected for the baseline; deferred to a later iteration (User Story 2)
  only if the local evaluation harness shows the rule-based ceiling has
  been reached, per Principle V.

## R4 addendum: v2 iteration, validated (User Story 2)

Measured via `evaluation/run_batch.py` (15 seasons/opponent,
`experiments/log.jsonl`): v1 (R4's original baseline) scored 100%/60%/67%
win rate vs random/starter/greedy. Two small, targeted changes -- (a)
penalizing `choose_best_crop` by how much of that crop is already growing
(diversification) and (b) capping SELL order size for premium goods
(STRAWBERRY/MELON/MILK/WOOL) instead of dumping the whole shed stack each
turn (research.md's original "no market-impact-aware sell batching"
simplification) -- took v2 to 100% vs all three AND 100% vs v1 itself in
direct self-play (mean money roughly double v1's). This suggests the
single biggest lever left unexploited by v1 wasn't crop selection at all,
but self-inflicted price crashes from selling accumulated stock in one
shot; batching sells is a stronger lead for a v3 iteration than adding
entirely new mechanics (animals, fertilizing) would be.

## v3: animal husbandry, prompted by v2's real Kaggle result

**Trigger**: v2 was submitted to Kaggle for real (submission ref
`56386069`) and scored a public leaderboard `public_score` of **389.9**,
while the field's scores clustered around **2900-3300**. This is exactly
the local/leaderboard divergence scenario the spec's Edge Cases and
constitution Principle II anticipated -- 100% local win rate did not
predict competitive standing at all, and per Principle II that divergence
had to be investigated before any further local-only tuning.

**Investigation**: downloaded and inspected the actual episode replays
(`kaggle competitions episodes` / `replay`) rather than guessing. All
three played episodes completed cleanly (`status: DONE`, no crash/timeout
-- so the gap was a strategy gap, not a bug in submission handling). The
worst loss: our agent scored 4,531 money; the opponent scored **132,021**.
Inspecting that opponent's final farm composition directly from the
replay JSON showed 12 COW pastures, 3 SHEEP pastures, and 8 hired hands
-- vs. our zero animals. Crops have a hard yield cap; animals (per
CONTEST.md) produce indefinitely as long as fed, which is the likely
source of that scale of return.

**Implementation**: added a dedicated animal-husbandry loop for hired
hands (build a PASTURE, buy/PICKUP/PLACE a COW, then FEED/CARE/HARVEST
daily, restocking WHEAT and COWs from the shed as needed), while the
farmer keeps doing exactly what it did in v2. Getting this working
surfaced three more real bugs, each found by testing against the actual
engine rather than assumption, the same way the harvest-timing and
last-callable bugs were found for v1/v2:

1. The existing "sell everything in the shed" loop didn't check whether
   an item was an actual priced product -- it sold a freshly bought COW
   right back out of the shed before a hand could ever pick it up.
2. `HIRE` was only ever queued once per day (a single `if`, not a loop)
   despite `hires_today < HIRE_TARGET` intending to allow several --
   hiring never scaled past 1 hand/day.
3. Even after (2) was fixed, hands at the shed always preferred picking
   up a *new* COW (to keep progressing toward the structure target) over
   picking up WHEAT for animals that were already hungry -- so every
   animal we placed starved after 2 unfed days and escaped
   (unrecoverable), for nothing. Feeding existing animals now strictly
   outranks acquiring new ones.
4. Even with all three fixed, targeting the opponent's *end-state* scale
   directly (10 structures, 6 hands) overextended the starting $3,000
   across land + animals + aggressive hiring simultaneously and stalled
   the economy for most of the 30-day season. Scaling the target down to
   3 structures / 3 hands (validate the mechanic at a size the starting
   budget can actually sustain, per constitution Principle V) immediately
   turned a losing run into a strongly winning, compounding one.

**Outcome (local)**: `evaluation/run_batch.py` (12 seasons/opponent) shows
v3 at 100% win rate vs random/starter/greedy and vs v2 in direct
self-play, at roughly **3x v2's average final money** (~18-19k vs
~6-6.6k).

**Outcome (real, submission ref `56387121`)**: unlike v2 (0 wins in its
sampled episodes), v3 went **6W-12L (33%) across all 18 played
episodes**, with money margins in a competitive range rather than
blowouts (we scored ~13k-23k most games). Downloaded and inspected every
replay (`kaggle competitions episodes` / `replay`, cross-referenced
against `info.TeamNames` since player index isn't fixed per episode).
Pattern: we beat clearly weaker/newer submissions (opponents scoring
1k-12k) and lose to a visible tier of strong opponents scoring
**40k-74k** -- well beyond even our improved range, and beyond what the
single 132,021-scoring opponent from the v2 investigation suggested was
the ceiling. The public leaderboard `score` column itself moved only
235.2 -> 262.8 -> 282.3 across these submissions and is evidently a
converging rating (the same submission's own displayed score changed
over time as more episodes completed) rather than a fixed value -- too
early/noisy to read much into on its own, but the raw episode rewards are
real, direct evidence and point the same direction as the leaderboard
did: still meaningfully behind the strong tier of the field.

**v4 attempt, reverted**: tried raising the targets incrementally --
6 structures/5 hands first (regressed badly: only barely beat `starter`,
zero cows ever got placed), then a smaller step, 4 structures/4 hands
(also regressed the same way: lost to `starter`, zero cows placed). Both
are worse than 3/3 by a wide margin, not a smooth scaling curve -- there
is a sharp cliff somewhere between 3 and 4 that isn't understood yet
(candidates: per-hand shed-queueing congestion in `_decide_hand_action`,
or the fixed daily cost of feeding/managing more animals outpacing
income before enough of them mature). Reverted `TARGET_STRUCTURES`/
`HIRE_TARGET` back to 3/3 (matches the actually-submitted v3) rather than
ship an untested regression. Understanding *why* 4 fails where 3
succeeds -- not just retrying different numbers -- is the right next
step before attempting a v4 scale-up again.

## Outcome

All Technical Context unknowns are resolved, including R1's real-world
per-turn time limit, which was confirmed directly from the bundled
environment's source rather than assumed. Proceeding to Phase 1 design.
