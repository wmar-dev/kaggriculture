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

## Heuristic-tuning plateau assessment (post-v7)

After v7, checked for further quick, high-confidence wins the same way
`REINVEST_RESERVE` was found -- direct parameter sweeps with enough
seasons to trust the result:

- `HAND_SLACK` (0-4): no stable ranking. An 8-season sweep suggested 0
  and 3 were best; a follow-up 15-season comparison of 2 vs 3 flipped
  the result entirely (2 came out clearly ahead). The variance
  (stdev ~11-20k) swamps any true effect at this sample size.
- `SELL_BATCH_CAP` (8-60): same pattern. A 15-season comparison favored
  25 over 15; a 20-season comparison of the same two values flipped it
  back in favor of 15.
- Land-purchase threshold (`next_cost * 2`): not swept -- land is a
  one-time ~$7,000 total across all 3 quadrants against an economy now
  routinely reaching $40k+, so even a real effect here is unlikely to be
  distinguishable from the noise floor just demonstrated on two other
  parameters.

This is a real contrast with `REINVEST_RESERVE`, which showed a large,
sharp, and *reproducible* effect (a genuine cliff, confirmed across 3
independent batches) -- these parameters don't have that kind of signal
to find. Combined with the reverted animal-diversification attempt
(a real, understood regression, not a tuning question), this is a
reasonable point to call the current heuristic-tuning approach at a
plateau: the remaining big levers (making the agent react to the
opponent's farm state at all -- currently never read, see `opponent_farm`
in observation.py; or a genuinely different approach such as
reinforcement learning) are qualitatively different investments, not
further parameter search.

## RL experiment: can a learned policy beat the farmer heuristic?

Scoped deliberately (see `training/env.py`'s docstring): trained PPO
(stable-baselines3) to control only the farmer's per-turn tile-tending
action (9-way discrete: movement, water, harvest, dig, plant, pass), with
crop choice, all market orders, and the entire animal-husbandry hand loop
left exactly as v7 (unchanged, not RL-controlled). Training used
192-step episodes (vs. the real 720) against the built-in `starter`
opponent for faster throughput (~550-650 env-steps/sec single-process).

**Training plateaued early**: the rolling-window training reward (final
money on 192-step episodes) stopped improving somewhere around
timestep 100,000-150,000 and stayed flat (~370-385) through 500,000 --
no further learning in the next 350,000 timesteps. Training was stopped
at 500,000 steps rather than run the full planned 2,000,000, since two
evaluated checkpoints (100k and 500k) already performed statistically
indistinguishably on real 720-step episodes.

**Evaluation** (the 500k checkpoint, full 720-step episodes): 100% win
rate vs random/starter/greedy at ~36-40k average money -- comparable to
v7's own ~39-43k range vs the same opponents. Direct self-play vs v7,
two independent 15-season batches: **9W-6L (60%)**, then **7W-8L
(47%)** -- combined 16W-14L (53%) across 30 games, with money roughly
tied in both batches (~10-12k each side). This is the same
noise-dominated pattern seen for `HAND_SLACK`/`SELL_BATCH_CAP` above,
not the sharp, reproducible signal `REINVEST_RESERVE` showed: **the
trained policy performs roughly on par with the hand-crafted farmer
heuristic, not a confident improvement over it.**

**Assessment**: this is still a genuinely interesting result on its own
terms -- a policy trained from scratch with no domain knowledge of
movement/pathing strategy reached rough parity, in under 15 minutes of
wall-clock training, with a heuristic that took an entire session of
careful, domain-informed iteration (and several real bugs found and
fixed) to build. But "roughly tied" doesn't justify the substantial
additional engineering this would need to actually ship: torch/
stable-baselines3 aren't guaranteed available in Kaggle's actual
sandboxed episode runner, so a real submission would need the trained
policy's weights extracted into a dependency-free pure-Python/numpy
forward pass, bundled the same way `evaluation/bundle_submission.py`
bundles the heuristic agent -- real work, not worth doing for a policy
that isn't yet a clear win. Left as `training/models/checkpoints/
ppo_farmer_v1_500000_steps.zip` (gitignored, regeneratable via
`training/train.py`) rather than deployed. A stronger next attempt would
likely need training against `v7` itself (self-play) rather than
`starter`, a longer/better-tuned run, and a look at whether the reward
shaping or observation encoding (see `training/env.py`) is limiting
what the policy can learn -- left as a documented option, not pursued
further this session.

**Follow-up: self-play against v7 itself.** Added support for loading a
real bundled submission as the training opponent (`training/env.py`'s
`load_agent_from_file`, mirroring `kaggle_environments`' own
last-callable-in-the-file loading convention -- needed a
`sys.modules` registration fix for the bundle's `@dataclass`-decorated
`GameObservation` to import correctly). Warm-started from the 500k
`starter`-trained checkpoint and continued training against
`submissions/v7/main.py` directly, on the theory that a weak, static
opponent doesn't create enough competitive pressure to learn something
better than parity.

**Result: an even flatter plateau.** The rolling training-reward curve
was completely flat from timestep 10,000 through 300,000 (295-302
throughout, no trend at all) -- more pronounced than the `starter` run's
plateau. Evaluation confirmed no improvement: 42% win rate vs v7 (13,348
vs 14,467), statistically the same as the earlier checkpoint's 50%.
Training stopped at 300k rather than continue to the planned 1,000,000,
since two independent training runs (different opponents, one warm-started
from the other) both plateaued this clearly and this quickly.

**Conclusion**: this is now reasonably strong, convergent evidence that
the *current* RL setup -- this observation encoding, this 9-action
discrete space, per-step money-delta reward, 192-step training episodes
-- has hit its own ceiling around "roughly tied with the hand-crafted
heuristic," not a compute or opponent-strength limitation. Pushing
further would need to change the setup itself (richer/different
observation features, a different reward shaping, full-length training
episodes, or a fundamentally different action space) rather than more
timesteps or a stronger opponent -- a genuinely different follow-up
project, not a continuation of this one. v7 remains the submitted/
recommended agent; the RL exploration ends here for this session with
an honest "matched, didn't beat" result.

## v8: diversify animals as a hedge against milk-market collapse

Went back to replay analysis -- the technique that produced every real
breakthrough this session -- on v7's 17 played Kaggle episodes.

**Record**: 8W-9L, our mean 30,909 vs the field's 29,200 -- essentially
even with the field, a big step up from v3's 6W-12L. But the
*distribution* was the finding: every win scored 28k-60k, while six of
nine losses scored under 25k (one as low as 1,664). The remaining lever
was never our ceiling -- it was our floor.

**Cause, found by cross-referencing every replay's final state**:

| Outcome | Opponent's cows | End-of-season MILK price | Our money |
| --- | --- | --- | --- |
| all 8 wins | 0-1 | 207-305 | 28k-60k |
| 8 of 9 losses | 6-13 | 11-137 | 1.6k-30k |

The correlation is near-perfect. Our economy was ~100% milk-driven, and
MILK has one of the harshest glut curves in the game (`above_target`
1.60 -- CONTEST.md warns premium goods "drive straight to the $1 floor"
on modest gluts). An opponent who also farms cows floods the shared
market and collapses our entire revenue stream. Two further losses had
milk at 36-38 against an animal-free opponent -- i.e. we crashed our own
price by overproducing, unaided.

**First attempt, rejected**: hold premium stock through the crash rather
than dumping into it (with shed-pressure and end-of-season escape
valves, since unsold inventory is worth $0 at the end). Measured at 40%
win rate vs v7, money slightly *behind* -- no help. The reason is
instructive: in a glut driven by a *competitor* the price never
recovers, because they keep selling while we sit on stock. You cannot
wait out a flood you do not control.

**What worked**: diversify production itself. Buy COW or SHEEP based on
each product's *current* price relative to base, divided by a
`1 + already owned` penalty. The price ratio is what makes it a hedge --
once milk trades far below base (whoever caused it), WOOL automatically
becomes the better buy, so new capital stops compounding a collapsing
revenue stream. Restricted deliberately to COW and SHEEP: both use the
same PASTURE structure (no second structure type to coordinate), and
SHEEP's `interval=3` needs *fewer* harvest visits than COW's
`interval=2`.

**Results** (bundled submission, 12 seasons/opponent): 100% vs
random/starter/greedy at ~40-49k, and **100% vs v7** (12W-0L, 27,574 vs
16,774). Two earlier dev-version batches both measured 80% vs v7 (16W-4L
then 12W-3L, combined 28W-7L) with no regression against the fixed
opponents. The largest win since v6.

**The methodological lesson is the real takeaway.** An earlier
diversification attempt was tried and *reverted* (see the
reverted-diversification note above) after measuring a severe regression
-- but that was measured against `random`/`starter`/`greedy`, **none of
which farm animals at all**. Those opponents never compete for the milk
market, so a hedge against milk collapse could only ever look like pure
cost there. The evaluation bench was structurally incapable of revealing
the value of the very thing being tested, and a genuinely good idea was
discarded on that evidence. The fix that finally surfaced it was
changing *what we evaluated against* (v7, which farms cows), not
changing the idea. Worth remembering for any future "tried it, didn't
work" conclusion: check whether the test bench can even express the
effect being looked for.

## Harness correctness: the two player seats are not symmetric

Found while testing whether GOOSE belonged in v8's diversification mix.
The control variant -- byte-identical settings to v8 -- scored only 2 of
12 against v8, which should have been a coin flip. That made the whole
comparison suspect, so the control itself got checked:

**v8 against a byte-identical copy of itself, player 0 won 3 of 14** --
despite near-identical mean money (26,195 vs 25,949). A by-seat
breakdown confirmed the direction: **3W-4L as player 0, 6W-2L as player
1**. The means being equal while the win counts differ says player 1
systematically takes the *narrow* games; player 0's wins come by larger
margins. Over a season of thousands of market transactions, a tiny
per-unit sequencing edge compounds into a consistent narrow-win bias.

This is a harness-validity bug, not a game insight: `run_batch` always
seated the agent under test as player 0, so **every self-play comparison
this session carried a roughly 30-point win-rate bias** -- larger than
most of the real effects the harness was being used to detect.

**Fixed** by alternating seats (`evaluation/run_batch.py`): even-numbered
seasons play the agent as player 0, odd-numbered as player 1, with the
win/loss accounting reading whichever slot the agent actually occupied.
Two regression tests cover the alternation order and the
score-from-the-correct-seat accounting.

**Re-validating the affected conclusions:**

- **v8 vs v7 stands, and was understated.** The original 12W-0L was
  measured from the *disadvantaged* seat. Re-measured seat-fair over 20
  seasons: **17W-3L (85%)**, money 23,723 vs 17,555. A real, large win.
- **The GOOSE question is now answered on valid evidence.** Against a
  correct control (17-21% is the positional baseline, not 50%),
  COW+SHEEP+GOOSE scored 2/12 -- i.e. no better than the control -- and
  COW+GOOSE scored 1/12 with clearly worse money (20k vs 30k). GOOSE
  stays out, now for a defensible reason rather than a bench-blind one.
- **Results that measured ~40-50% vs an opponent may have been
  understated**, since they were also measured from the weak seat. That
  includes the RL policy's 42-50% (so "rough parity" may have been
  slightly pessimistic, though not enough to change the conclusion) and
  the rejected hold-through-the-crash experiment's 40%.

Two bench-validity problems in a row now -- opponents that couldn't
express the effect being tested (the diversification revert), and a
seat bias larger than the effects being measured -- both of which
produced confidently wrong conclusions from clean-looking numbers.
Worth treating "the measurement might be the thing that's broken" as a
first-class hypothesis whenever a result looks surprising.

## v9: grow the herd's feed instead of buying it

Replay analysis of v8's 19 real episodes, now on a trustworthy harness:
**8W-11L, our mean 34,488 vs the field's 43,248.** We improved on v7
(30,909) but *the field improved faster* (29,200 -> 43,248 in two days)
-- worth noting that a static agent loses ground here even when it isn't
getting worse.

The failure pattern had shifted away from price crashes (v8's fix
worked -- we now reliably win at high milk prices, taking 5 of 8 wins
against animal-free opponents). The new binding constraint was **scale**:
v8 stalls around 10 animals while the strong opponents run **17-28**
(`COW:12 + SHEEP:8`, `COW:8 + SHEEP:20`).

**Two hypotheses tested and rejected first**, both worth recording
because they were the obvious guesses:

- *Reinvestment pace is mistuned for a contested market.* `REINVEST_RESERVE`
  had been tuned against `starter` (animal-free, no market competition),
  so this looked like another bench-blindness case. Re-swept against v8
  on the seat-fair harness: 1.25 and 1.5 are catastrophic (0/16), 2.5 is
  worse, and **2.0 remains the optimum**. The original tuning was robust
  after all.
- *The ceilings are binding.* Opponents exceed `MAX_STRUCTURES=15`
  outright, so raising it looked necessary. Raising both caps made
  things strictly **worse** (15/15 -> 12%, 25/25 -> 12%, 40/40 -> 6%,
  money 27k -> 20k -> 17.6k) -- it just reproduces the v6-era
  over-extension failure. The ~10-animal plateau is self-imposed by the
  loop's own economics, not by the caps.

**What the measurement actually showed.** Instrumenting a single game:
v8 bought **143 units of wheat for ~5,855 -- about 39% of that game's
final money** -- and its own buying drained market inventory enough to
drive the wheat price from its base of 25 up to **50** (WHEAT's
`below_func` is `sqrt` at `below_target` 0.80, so scarcity bites hard).
Feed cost per animal therefore *rises* with herd size: a self-inflicted
brake on precisely the scaling we were trying to achieve.

**Fix**: when the herd's wheat buffer is thin (`< herd * FEED_BUFFER_DAYS`),
plant WHEAT regardless of what the value-ranked crop choice prefers. A
wheat seed costs 10 and yields 4-6 units (~2.5/unit against a market
price of 25-50/unit), and growing it *adds* supply instead of draining
it.

**Results**: wheat purchases fell from 143 units (~5,855) to 61
(~2,363), a 58% cut. Three batches vs v8: **65%, 60%, 57%** (combined
33W-21L, 61%), with 100% vs random/starter/greedy at 36-42k and no
regression anywhere.

**Worth noting the hypothesis was half wrong.** The theory was that
cheaper feed would unlock a *bigger* herd; herd size didn't actually
grow (one instrumented game ran 6 animals against v8's 10). The gain is
pure cost reduction, not scale. The prediction was wrong while the
intervention still worked -- which is a good argument for measuring the
mechanism (wheat units bought) separately from the outcome (win rate),
rather than assuming a win confirms the story that motivated it.

## v9 was a regression: herd size, not feed cost, drives real results

v9 won local self-play against v8 across three batches (65/60/57%) and
then scored **363.3 against v8's 430.5** on the real leaderboard. Per
Principle II that divergence had to be resolved before any further
tuning, so it was, and the answer generalises.

**Herd size is the dominant driver of real results.** Across all 43 real
episodes played by v7, v8 and v9:

| Our herd size | Games | Our mean money | Win rate |
| --- | --- | --- | --- |
| 7-8 | 21 | 28,253 | 24% |
| 9-10 | 14 | 35,432 | 57% |
| 11+ | 7 | 49,995 | **71%** |

Opponents show the same pattern (animal-free opponents average 21,104;
those running 7+ animals average 49-57k). And v9's median herd was
**7 against v8's 9** -- growing its own feed costs the farmer's turns,
the farmer is the only worker on high-value crops, and that income is
what funds reinvestment. v9 traded the thing that matters for the thing
that doesn't.

*Caveat worth stating*: this is a correlation, and causation plausibly
runs both ways -- a game going well affords more animals. The v9
comparison is the stronger evidence, since it shrank the herd *by
design* and underperformed.

**Why local evaluation couldn't see it.** Self-play against our own
previous version pits two agents of the *same scale* against each other,
so feed-cost efficiency decides the match. The real field contains
opponents running 12-28 animals, where scale decides instead. Third
instance this session of the bench failing to represent the real
opponent distribution.

**An attempted rescue, also rejected.** Since 39% of all hand-turns were
PASS (1,840 of 4,707 in a measured game), idle hands were routed onto
wheat so feed could be grown without taxing the farmer. The labour did
get used (PASS fell to 0.1%) and herd size was preserved (11 vs v8's
10), but wheat purchases went *up*, not down: the greedy nearest-tile
logic plants instantly and has to walk to water, so it planted 176 wheat
against only 70 waterings, leaving 11 tiles of weeds (unwatered plants
die). Capping plantings to the herd's actual need helped the weeds
(11 -> 6) but not the purchases (173 -> 156, against v9's 61). Reverted.

**Outcome**: v8 is restored as the recommended submission.

### Harness: stale scores are not comparable across versions

Fixing the above surfaced two more ranking defects, both now fixed and
regression-tested:

1. When two candidates *both* have real leaderboard scores, that direct
   comparison should outrank any local proxy. Ranking previously used
   local signals only -- a deliberate earlier fix, because letting *any*
   stale real score outrank an untested newer version had kept
   recommending a known-weak v2 over v3. Requiring **both** sides to have
   real evidence keeps the useful case without reviving the broken one.
2. Applying that immediately recommended v6, because the log stored each
   score as read *at submission time* -- and scores converge downward as
   episodes accumulate (v6 read 448.6 fresh, 406.4 now). Snapshots taken
   at different times are not comparable to each other. All scores were
   re-read in a single pass and re-logged, so the comparison is
   apples-to-apples.

## v10: stop paying for animals that never reach a pasture

Chasing the herd-size lever surfaced a concrete leak. Tracing herd size
per day showed it growing to 9 by day 12, dropping to 7, and then
sitting at **exactly 7 for the final 17 days with two built pastures
standing empty** -- while 17 animals had been purchased in total.

The shed explained it: from day 10 onward **8 animals (3 COW + 5 SHEEP,
~3,700) sat in the shed, never collected**. Cause: hands prioritise
feeding over collecting a new animal (added in v3, correctly -- an unfed
animal escapes permanently). But every animal is unfed at dawn, so once
the herd is large enough that *someone* is always unfed when a hand
reaches the shed, wheat always wins and the waiting animal is never
picked up. Worse, pending animals count toward `MAX_STRUCTURES`, so
7 placed + 8 pending = 15 also jammed the purchase gate shut.

**The obvious fix made things dramatically worse.** Letting hands
collect the stranded animals grew the herd to 12 and measured
**0W-20L** against v8. Gating expansion on the herd being fed on
schedule still measured **1W-19L**. The strandings had been accidentally
load-bearing: beyond roughly seven animals the marginal animal costs
more in feed -- bought at a price our own buying inflates -- than its
product earns into a market we are simultaneously glutting.

**That also resolves the previous section's caveat.** The herd-size
correlation (herd 11+ winning 71%) really was mostly reverse causation:
a game going well affords more animals. Forcing the herd higher
*causally* collapses the economy. Worth remembering as a case where
acting on a correlation would have been actively harmful, and only the
intervention test distinguished the two.

**The actual fix** is therefore not to place the stranded animals but to
never buy them: don't purchase while one is still pending. The herd
ceiling stays exactly where it was; the wasted ~3,700 does not.
Purchases fell from 17 to 11 (7,300 -> 4,900) with the herd unchanged at
7 and nothing stranded.

**Results** (bundled, 14 seasons/opponent): 100% vs
random/starter/greedy at 42-49k, and **100% vs v8** (14W-0L, 32,111 vs
23,630). Two dev batches measured 90% and 85%.

## v10 confirmed on the leaderboard; feed self-sufficiency abandoned

**v10 scored 447.6, the best of any submission** (v8 430.5, v7 410.2,
v6 406.4, v9 405.6). Real episodes: **7W-8L, our mean 39,764 against
the field's 40,450** -- near parity, up from v8's 34,488 against 43,248.
Local evaluation predicted this correctly, unlike v9, which fits: v10
only removed waste (animals bought and never placed) without changing
scale or strategy, so there was no scale-dependent effect for the
same-scale local bench to miss.

Also worth recording: **v9 rose from 363.3 to 405.6** as its episodes
accumulated. Fresh scores really do understate, so the earlier decision
to judge v9 on episode outcomes rather than its day-one score was the
right call -- though v9 still sits below v8, so the revert stands.

**Why the herd cannot simply be grown.** Diagnosing the ~7-animal
ceiling directly: at that size our own products are *not* glutted
(MILK 257, WOOL 245, both near base), but our wheat buying has pushed
WHEAT from its base of 25 to **51** across 78 units. Feed cost, not
market saturation and not land, is what caps the herd. Animals are
already optimally placed (mean distance 0.9 tiles from the shed), so
travel isn't it either.

**Feed self-sufficiency: three attempts, all abandoned.** The obvious
implication -- grow the feed instead of buying it -- was tried three
distinct ways and never delivered its own mechanism:

1. *Farmer grows it* (v9): purchases fell 143 -> 61, but the herd shrank
   from 9 to 7 and the real score dropped. The farmer is the only worker
   on high-value crops, and that income funds reinvestment.
2. *Idle hands grow it, uncapped*: 39% of hand-turns were PASS, so the
   labour existed. But greedy nearest-tile logic plants instantly and
   must walk to water, so it planted 176 against 70 waterings, left 11
   tiles of weeds, and purchases went *up* (173).
3. *Idle hands, cap sized to actual need* (one wheat tile yields ~1
   unit/day, so a herd of N needs ~N tiles): weeds fell to 3 and the
   herd reached 10, but purchases still rose (113 vs the 78 baseline)
   and the batch measured 55% -- inside noise.

The common failure is that "idle" hands are only idle in the sense that
they PASS; given crop work they spend nearly all their turns walking
between scattered tiles. `PLANT_WHEAT` never even reached the top eight
hand actions, while movement took 2,472 turns. Productive multi-tile
farming needs coordination the current greedy per-unit loop doesn't
have -- assigning each hand a stable plot, rather than every hand
re-deciding for the nearest needy tile each turn. That's a different
design, not a tweak, and it is where this thread stops.

## v11: stop buying land we never use

Switched from the cost side to the income side and measured, for the
first time, **where the money actually comes from** in a full game:

| Product | Units sold | Gross revenue | Price at season end |
| --- | --- | --- | --- |
| MILK | 130 | 30,400 (62%) | 278 (base 160 -- healthy) |
| FERTILIZER | 176 | 11,629 (24%) | 30 (free: collected from animals) |
| WOOL | 57 | 6,340 (13%) | **5** (base 200 -- cratered) |
| WHEAT | 25 | 939 | 52 |

**A tempting misreading, and the correction.** Wool cratering to 5 while
milk held at 278 looked like the forced diversification penalty
(`/ 1 + owned`) was buying sheep we didn't need. Removing it, so price
ratio alone drove animal choice, measured **30%** against v10 -- clearly
worse. The reason is that the hedge has to be *pre-positioned*: animals
take 6-8 days to first yield, so by the time the price signal says milk
is collapsing it is far too late to start a sheep pipeline. Insurance
has to be bought before the fire. v8's diversification was right, for a
subtler reason than originally recorded.

**What the cost side did reveal.** Gross revenue of 49,308 against
33,935 final money means ~15k goes to costs, and the single largest line
is **land: 7,000 for three extra quadrants**. A measured game ended with
all four quadrants bought and only **27 of 100 tiles occupied** (weeds
included) -- 73 empty. Land was never the constraint; feeding throughput
is (see the previous section).

Swept directly against v10, 16 seasons per setting:

| Quadrants bought | Result vs v10 |
| --- | --- |
| 1 | 25% (genuinely too little land) |
| 2 | 62% |
| **3** | **100% (16W-0L)** |
| 4 (v10's behaviour) | control |

Three reproduced at 75% and 90% over two further 20-season batches
(combined 49W-7L). The fourth quadrant alone costs 4,000 -- more than
the first two together -- for tiles that sit empty, and end-of-season
money *is* the score.

**Results** (bundled, 14 seasons/opponent): 100% vs random/starter/greedy
at **48-55k** (v10 managed 42-49k), and **93% vs v10** (13W-1L, 27,697
against 23,896).

## Outcome

All Technical Context unknowns are resolved, including R1's real-world
per-turn time limit, which was confirmed directly from the bundled
environment's source rather than assumed. Proceeding to Phase 1 design.
