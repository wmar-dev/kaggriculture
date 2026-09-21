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

**v4: root-caused the scale-up cliff, shipped the fix at proven scale**

First tried raising the targets incrementally -- 6 structures/5 hands
(regressed badly: only barely beat `starter`, zero cows ever got placed),
then a smaller step, 4/4 (same failure mode). Rather than keep guessing
numbers, traced the 4/4 attempt day by day: cows were placed successfully
around day 0-1, **all escaped by day 3** (a hiring gap left them unfed 2
consecutive days), and -- critically -- **never replaced for the rest of
the 30-day season**, even though a spare cow sat unused in the shed the
whole time. Root cause: the BUY_ANIMAL/PICKUP gating compared
`structures_owned + pending_animals < TARGET_STRUCTURES`, where
`structures_owned` counts built PASTURE/COOP tiles -- and a built
structure never reverts to `None` even after its animal starves and
escapes. Once built-structure-count alone ever reached the target, the
agent considered itself "done" acquiring animals, permanently, regardless
of how many were actually still alive.

**Fix**: gate on `_count_placed_animals(obs) + pending_animals` (live
animals, not built structures) in both the market-order buy check and
the shed PICKUP check. This is a real correctness bug independent of
scale -- it just took a higher target (where the hiring-gap/escape event
is more likely to occur at least once during tuning) to surface clearly.
Re-tested 4/4 with the fix: cows are now replaced after escaping, and
the run flips from a loss to a win (~8k vs starter, up from losing
outright) -- though still well under 3/3's own ~19-20k, because a
separate, not-yet-understood cash-flow volatility issue remains at that
scale (money repeatedly dropped to single digits for several consecutive
days in the 4/4 trace, blocking even the now-cheap `HIRE_MONEY_RESERVE`
gate). That deeper issue is left for a future scale-up attempt.

**Decision**: ship the fix at the already-proven 3/3 scale rather than
the still-shaky 4/4 one. Batch evaluation (12 seasons/opponent) shows v4
at 100% vs random/starter/greedy (comparable to v3's own numbers,
~18-20k), and roughly a **coin flip against v3 in direct self-play**
(4W-4L-4T, mean money essentially tied: 17,955 vs 17,982). That's
expected and correct for this kind of fix: the escape/replacement bug is
a rare tail-risk event, not something that fires every game -- when it
doesn't trigger, v3 and v4 play identically; when it does, v4 recovers
and v3 stays stuck with a permanently smaller operation for the rest of
the season. A fix that only matters in the tail won't move an *average*
head-to-head result much (which is exactly what the near-50/50 self-play
record shows) and is still worth shipping, since real Kaggle matches
will hit that tail case some nonzero fraction of the time.

**v4's real Kaggle result** (submission ref `56415012`): `public_score`
293.6, a modest improvement over v3's 297.3/282.3-ish readings from
around the same time (still a converging, noisy rating -- see the note
above about v2's own score moving between checks).

## v5: fix a second, larger animal-economics bug (wheat over-buying)

Went back to investigate the deeper cash-flow volatility noted as
unresolved in the v4 section above, rather than leave it. Traced a 4/4
run's per-turn money deltas directly (not just daily snapshots this
time) and found the real, larger drain: `BUY_PRODUCT WHEAT` orders
firing on almost every qualifying turn, each nudging the scarcity price
up further. Root cause: the wheat-restock check compared
`shed.get("WHEAT", 0)` against the number of placed animals -- but hands
PICKUP wheat into their own inventory immediately once it lands in the
shed (see `_decide_hand_action`), so shed stock alone constantly reads
as "low" even when there is already enough wheat in transit to feed
every animal that day. This is the same class of bug as v4's fix
(gating on the wrong count), just for wheat instead of cows, and a much
bigger drain in practice since it could re-trigger many times per day
rather than being a rare escape event.

**Fix**: count wheat already held across all hand inventories, not just
the shed, before buying more.

**Re-tested after the fix**: 4/4 jumped from ~8k (v4, cow-fix only) to
~16.5k vs `starter` in a single run; a reliable 10-season batch
comparison of 3/3 vs 4/4 (both with *both* fixes applied) gave 3/3 a
mean of 19,965 vs 4/4's 16,149 -- **3/3 is still clearly better**, just
by a smaller margin than before. So the wheat-buying bug explains most,
but not all, of why naive scale-up underperformed; some other, smaller
inefficiency remains at 4+ hands (candidate: per-hand shed-queueing/path
congestion noted in the original scale-up investigation), left as an
open question rather than chased further this iteration.

**Decision**: ship the wheat fix at the same proven 3/3 scale (still the
best-performing configuration found so far). Batch evaluation (12
seasons/opponent) shows v5 at 100% vs random/starter/greedy, at a
noticeably higher money level than v3/v4's own numbers (~19-21k vs
~18-20k), and a clean **100% win rate vs v4 in direct self-play**
(mean money 16,508 vs 14,804) -- unlike v4's fix, this one is a real,
consistent improvement at the shipped scale, not just a tail-risk
mitigation.

**v5's real Kaggle result** (submission ref `56417041`): `public_score`
342.0 -- a clean upward trend across all five real submissions so far
(235.2 -> 242.6 -> 297.3 -> 311.1 -> 342.0), the first time the
leaderboard signal has moved consistently in the same direction as the
local improvements rather than being flat/noisy.

## v6: replace the fixed animal-acquisition target with progressive reinvestment

With both v4's and v5's bugs fixed, went back to the still-unexplained
part of the original scale-up investigation: why did a *proportionally*
scaled 4/4 setup (same 1:1 hands-to-structures ratio as the working 3/3)
still underperform 3/3, when neither of the two fixed bugs should have
cared about the ratio itself?

**Isolation test** (8 seasons/config): held hands and structures apart
to see which one actually mattered.

| Config | Mean final money |
| --- | --- |
| 3 structures / 3 hands (baseline) | 20,521 |
| 4 structures / 3 hands (animals w/o matching hands) | 15,319 |
| 3 structures / 4 hands (extra idle hand) | 18,280 |

More animals without matching hands was clearly the worst combination --
but a *second* run of plain 4/4 (matching ratio) still only averaged
12,304-16,149 across two separate batches, confirming the regression
isn't just an hours-per-animal coverage problem either.

**Real hypothesis**: `TARGET_STRUCTURES` raced to acquire N animals as
soon as barely affordable, which front-loads capital into several
simultaneously-young, unproductive animals (each needs 8 days before
`HARVEST` does anything at all) and delays the compounding that would
otherwise fund further expansion -- classic "too wide too fast" in a
game with strong compounding dynamics. A fixed target chosen in advance
(3, 4, 6 -- doesn't matter which) can never adapt to how healthy the
economy actually is at the moment of each purchase.

**Fix**: replaced `TARGET_STRUCTURES`/`HIRE_TARGET` with
`REINVEST_RESERVE` (buy another cow only once money is comfortably above
`REINVEST_RESERVE * cost`, i.e. cash health gates expansion, not a
number decided in advance) and a dynamic `_hire_target()` that tracks
live+pending animals plus a small buffer, both capped by a generous
safety ceiling (`MAX_STRUCTURES`/`MAX_HANDS` = 15, roughly matching the
strongest real opponent observed) rather than a small target to race
toward.

**Outcome**: night-and-day difference. A single trace shows organic,
staged growth -- 2 cows by day 3, 6 by day 15, money compounding from
~5k at day 15 to 35k+ by day 27 -- instead of the previous pattern of
racing to acquire everything on day 0 and then surviving a cash crunch.
Batch evaluation (12 seasons/opponent) on the bundled submission: 100%
vs random/starter/greedy at **~35-41k** average money (roughly *double*
v5's ~19-21k), and a decisive **92% win rate vs v5 in direct self-play**
(mean money 26,830 vs 14,817, nearly 2x). This is the largest single
improvement since the original v2->v3 animal-husbandry addition itself,
and it came from questioning a design assumption (a fixed target number)
rather than another parameter tweak or bug fix.

**v6's real Kaggle result** (submission ref `56436146`): `public_score`
448.6 -- the biggest single jump yet (up from v5's 328.4), and the
biggest jump across all six real submissions so far. Confirms the v6
mechanism change (not just local benchmarks) translated to real
competitive improvement.

## v7: tune the v6 reinvestment reserve itself

`REINVEST_RESERVE = 3` was a reasonable first guess when the mechanism
was introduced (v6), not a tuned value. Swept it directly instead of
assuming "more conservative is safer": 8-10 seasons/setting, 3
independent batches.

| `REINVEST_RESERVE` | Mean final money (batch 1 / 2 / 3) |
| --- | --- |
| 1.0 | 2,383 (reproduces the original cash-crash failure mode) |
| 1.5 | 16,187 |
| 2.0 | 48,846 / 37,058 / 38,732 |
| 2.5 | -- / -- / 30,465 |
| 3.0 (original v6 value) | 38,486 |
| 4.0 | 34,031 |

2.0 is a genuine local optimum -- it beats 1.5 *and* 2.5/3.0/4.0
consistently, not a point on a monotonic "safer is better" curve.
Reserve too low (1.0-1.5) reproduces the pre-v6 overspending crash;
reserve too high (2.5+) is unnecessarily conservative and leaves cash
idle that could already be compounding.

**Outcome**: shipped `REINVEST_RESERVE = 2`. Batch evaluation on the
bundled submission: 100% vs random/starter/greedy at **~39-43k** average
money (up from v6's own ~35-41k), and a **67% self-play win rate vs v6**
(19,532 vs 17,390) -- a real but more modest improvement than v6's own
jump, as expected for tuning an already-good mechanism rather than
introducing a new one.

## Tried and reverted: diversifying animal type (GOOSE/SHEEP)

Computed the same payback-speed-weighted metric already used for crop
choice, applied to all three animals: GOOSE scores 12.5 (cost 300, EGG@50,
first_yield_day 4), SHEEP 11.1 (cost 500, WOOL@200, first_yield_day 6),
COW only 10.0 (cost 400, MILK@160, first_yield_day 8) -- on paper, COW
(the animal hardcoded since v3, chosen only because it's what the
strongest real opponent happened to scale) looks like the *worst* of the
three.

Generalized `choose_best_animal` the same way as `choose_best_crop`
(including the v2-style diversification penalty) and re-tested:

- All three animals, dynamically chosen: **~6.1k** final money vs
  starter -- a severe regression from COW-only's ~19-48k.
- GOOSE only (single animal type, isolating the choice from any
  structure-diversity coordination cost): **mean 6,362** across 8
  seasons -- still badly underperforms COW-only.

So it isn't structure-type fragmentation (COOP + PASTURE built
alongside each other) causing the regression -- GOOSE itself
underperforms COW even alone. Best current explanation: the
payback-speed metric only accounts for time-to-first-return, not ongoing
attention cost, and GOOSE's `interval=1` (daily production, capped at
`max_held=4`) needs harvesting roughly twice as often as COW's
`interval=2` (every other day, `max_held=6`) to avoid wasting capped
production -- and hands are the confirmed throughput-limiting resource
for this whole subsystem (see the v6 isolation test above). A metric
that ignores hand-turns-consumed-per-dollar-earned can favor an animal
that "pays back fast" in isolation but starves the rest of the operation
of hand attention in practice. Reverted cleanly to the proven COW-only
v7 code rather than ship the regression; a real fix would need to weight
by hand-turn cost per unit of ongoing production, not just initial
payback speed -- left as a documented open question rather than
half-solved this iteration.

## Outcome

All Technical Context unknowns are resolved, including R1's real-world
per-turn time limit, which was confirmed directly from the bundled
environment's source rather than assumed. Proceeding to Phase 1 design.
