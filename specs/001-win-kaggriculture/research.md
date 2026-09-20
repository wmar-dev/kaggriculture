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

## Outcome

All Technical Context unknowns are resolved, including R1's real-world
per-turn time limit, which was confirmed directly from the bundled
environment's source rather than assumed. Proceeding to Phase 1 design.
