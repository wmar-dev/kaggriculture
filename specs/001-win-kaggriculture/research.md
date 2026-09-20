# Phase 0 Research: Win Kaggriculture Competition

## R1: Per-turn / per-episode time limit

**Unknown**: Kaggle Simulations competitions enforce a compute time budget
per agent per turn (and often a cumulative "overage" budget per episode).
`CONTEST.md` does not state Kaggriculture's specific limits, and the live
competition page could not be fetched automatically (client-rendered /
requires a logged-in session).

- **Decision**: Design and test the agent against a conservative internal
  budget of **≤50ms per turn** on this development machine, with a hard
  internal guard that always returns a legal (possibly `PASS`-heavy)
  action set well before any plausible Kaggle-imposed ceiling. Treat the
  real limit as **TODO(TURN_TIME_LIMIT)** to confirm from the competition's
  episode/agent specification once accessible, and re-check this budget
  against it before final submission.
- **Rationale**: Every other Kaggle Simulations competition to date has
  used single-digit-second-per-turn budgets with a modest cumulative
  overage pool; a heuristic (non-ML-inference, non-tree-search-heavy)
  agent operating on a small board (≤10×10 tiles) will naturally run in
  low single-digit milliseconds, so a 50ms internal target leaves a large
  safety margin without blocking progress on an unconfirmed number
  (constitution Principle VI).
- **Alternatives considered**: (a) Block until the exact limit is
  confirmed — rejected, violates Principle VI (no reasonable default
  exists to justify blocking here; a conservative default does). (b)
  Design for heavier per-turn search (e.g., multi-ply lookahead) from the
  start — rejected for now per Principle V (Time-Boxed Simplicity); revisit
  only if a simple heuristic's ceiling proves insufficient.

## R2: Kaggle Simulations submission packaging

**Question**: How should a multi-module local package become the single
file Kaggle simulation submissions require?

- **Decision**: Keep agent decision logic in normal importable modules
  under `src/kaggriculture_agent/` during development (for testability),
  and add a small bundling step (`evaluation/` tooling, detailed in
  tasks.md) that inlines/concatenates those modules into one
  self-contained `submissions/<version>/agent.py` with a single
  `agent(obs, config)` entry point and no local imports, matching the
  `kaggle_environments` agent contract shown in `CONTEST.md`'s quickstart.
- **Rationale**: Writing and testing decision logic as one large file is
  error-prone and hard to unit-test; nearly every prior Kaggle Simulations
  competition solution uses a "develop modular, bundle flat" pattern for
  exactly this reason.
- **Alternatives considered**: Write the agent as a single flat file from
  day one — rejected, hurts testability/readability for no real benefit
  since bundling is a small, one-time tooling cost.

## R3: Local evaluation opponent pool

**Question**: What opponents should the local batch-evaluation harness use
to produce a trustworthy win-rate/score signal (constitution Principle II,
spec FR-002)?

- **Decision**: Maintain three reference opponents locally: (1) a
  `RANDOM` agent (legal-random actions, sanity/robustness baseline), (2) a
  simple hand-written `GREEDY` heuristic (e.g., always plant the
  best-`Yield/tile/day` affordable crop and sell immediately at current
  price — a stronger, non-trivial baseline), and (3) the **previous
  submitted version** of the agent itself (so every candidate must beat
  what is already on the leaderboard, not just weak bots). Track all three
  results per experiment-log entry.
- **Rationale**: A single weak baseline (e.g., only `RANDOM`) would let
  local evaluation rate strategies as "improving" even while they stay far
  behind real competitors; self-play against the last submitted version
  directly targets the quantity that matters (does this change actually
  beat what's currently scored?).
- **Alternatives considered**: Evaluate only via public leaderboard
  submissions — rejected outright, this is exactly the untrustworthy,
  submission-budget-burning pattern constitution Principle II forbids.

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

All Technical Context unknowns are resolved (R1's real-world limit remains
a tracked TODO but is no longer a blocking unknown — see decision above).
Proceeding to Phase 1 design.
