# Feature Specification: Win Kaggriculture Competition

**Feature Branch**: `001-win-kaggriculture`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "Win https://www.kaggle.com/competitions/kaggriculture using claude code."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a valid baseline agent on the leaderboard (Priority: P1)

As the competitor, I want a simple, fully working farming agent submitted
to the competition as early as possible, so that I have a proven,
non-crashing player and a leaderboard rating to improve from, instead of
discovering a rules-interface problem late.

**Why this priority**: Nothing else matters until there is a valid,
accepted agent. A working baseline de-risks the rest of the competition and
gives a concrete rating to beat.

**Independent Test**: Can be fully tested by running the agent through a
full simulated season (locally, via the game's environment) against a
reference opponent without errors or timeouts, then confirming Kaggle
accepts the submitted agent and returns an initial leaderboard rating.

**Acceptance Scenarios**:

1. **Given** the agent implements the required observation-in/actions-out
   interface, **When** it plays a full season locally against a reference
   opponent, **Then** it completes without errors, illegal actions, or
   turn timeouts.
2. **Given** an agent submission, **When** it is uploaded to Kaggle,
   **Then** it is accepted without a validation error and begins playing
   rated matches.

---

### User Story 2 - Climb the leaderboard through validated iteration (Priority: P2)

As the competitor, I want each change to the agent's strategy to be tested
locally (via simulated seasons against reference and prior-version
opponents) before it costs a submission, so that I spend limited
submissions only on strategies I already trust, and I keep a record of
what was tried.

**Why this priority**: Winning requires many strategy iterations (planting
mix, market timing, hand-hiring, land expansion, opponent responses);
without a trusted local signal and a record of results, effort is wasted
re-testing bad strategies or chasing noise on the public leaderboard.

**Independent Test**: Can be fully tested by running two competing agent
strategies through local simulated seasons against the same opponent pool,
confirming the one with the better local win-rate/end-of-season money also
performs better (or at least not worse) on the public leaderboard, and
confirming both attempts are recorded with their results.

**Acceptance Scenarios**:

1. **Given** a candidate change to the agent's strategy, **When** it is
   evaluated locally across a batch of simulated seasons, **Then** a
   win-rate/score is produced before any submission is used on it.
2. **Given** a completed evaluation, **When** the result is reviewed,
   **Then** it appears in a single record alongside all prior attempts with
   enough detail to reproduce it.
3. **Given** the local win-rate disagrees sharply with a public leaderboard
   rating change for the same submission, **Then** that disagreement is
   flagged before further iteration continues.

---

### User Story 3 - Lock in the best final submission before the deadline (Priority: P3)

As the competitor, I want to deliberately choose which submission(s) count
as final before the competition closes, so that my best, most trustworthy
result is the one that is scored — not whatever happened to run last.

**Why this priority**: A competition is won or lost on the final selected
submission(s); without a deliberate choice, the strongest result can be
left unselected by accident.

**Independent Test**: Can be fully tested by confirming, at any point in
the competition, which submission(s) are currently marked as final and
that this choice is backed by recorded validation/leaderboard evidence.

**Acceptance Scenarios**:

1. **Given** multiple scored submissions, **When** the deadline approaches,
   **Then** the competitor can identify the best-supported submission(s)
   from the record.
2. **Given** a final selection has been made, **When** the competition
   closes, **Then** the selected submission(s) are the ones scored — none
   are missed and none are late.

---

### Edge Cases

- What happens when a submission fails Kaggle's validation checks (bad
  interface, import error, crash on the first observation)? The local
  evaluation harness MUST catch the same failure before the submission is
  spent, wherever practical.
- What happens when the agent produces an illegal or malformed action, or
  exceeds the per-turn time limit during a live match? The agent MUST be
  built to avoid both, and local evaluation MUST specifically test for
  timeouts and illegal-action cases, not just favorable-case play.
- What happens when the daily or total submission limit is reached before
  a promising strategy has been tried?
- How does the process handle a large gap between local win-rate/score and
  public leaderboard rating movement for the same submission (possible
  overfitting to the local opponent pool)?
- How does the process handle the leaderboard's opponent pool or rating
  shifting under the agent as other competitors submit and improve their
  own agents?
- What happens if the game rules, environment code, or configuration
  defaults are amended by the competition mid-way through?
- What happens if the deadline passes with no submission selected as
  final? The most recently accepted submission MUST stand rather than
  nothing being scored.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The solution MUST be an agent that matches the competition's
  required interface (consumes the observation format and returns a legal
  action set each turn, per the rules in `CONTEST.md`) and is accepted by
  Kaggle without a validation error.
- **FR-002**: The solution MUST establish a local evaluation method
  (simulated seasons against a reference/random opponent and against prior
  versions of itself) whose result is a reliable predictor of leaderboard
  performance before it is used to decide which strategy changes are worth
  submitting.
- **FR-003**: Every submission attempt MUST be recorded in a single,
  reviewable log containing at minimum: what strategy change was tried, its
  local evaluation result (e.g. win-rate and average end-of-season money
  against a fixed opponent set), its leaderboard result (once known), and
  enough information to reproduce it exactly.
- **FR-004**: The solution MUST track remaining submission budget (daily
  and/or total, as set by the competition) and MUST NOT exceed it.
- **FR-005**: The competitor MUST be able to see current standing
  (validation score, latest leaderboard score/rank) on request at any time.
- **FR-006**: A final submission (or set of final submissions, where the
  competition allows selecting more than one) MUST be deliberately chosen
  and MUST be confirmed as selected before the competition deadline.
- **FR-007**: The solution MUST NOT use data, code, pretrained models, or
  techniques excluded by the competition's official rules, and MUST NOT
  violate applicable law (see project constitution, Principle IV).
- **FR-008**: Every scored submission MUST be reproducible end-to-end from
  a committed, versioned state of the code and configuration that produced
  it (see project constitution, Principle III).
- **FR-009**: The agent's objective MUST match the official competition
  specification: maximize the amount of money in the bank at the end of a
  30-day (720-turn) simulated farming season, played head-to-head against
  one opponent agent per match, per the rules and mechanics documented in
  `CONTEST.md` (farm/crop/animal actions, market dynamics, town demand,
  turn processing order). Ties (equal money) are a possible, valid match
  outcome. The exact submission deadline and leaderboard scoring/ranking
  mechanism (e.g., rating system across many matches) are not yet
  confirmed from the live competition page; treat the timeline in
  Assumptions as provisional until confirmed.
- **FR-010**: Every upload of an agent to Kaggle (the actual submission
  action, spending submission budget) MUST require the competitor's
  explicit review/approval before it is sent — it MUST NOT be performed
  automatically without that approval. Building, local evaluation, and
  preparing a ready-to-submit agent file MAY proceed without per-step
  approval. *(Resolved per project constitution Principle VI: a Kaggle
  submission is an irreversible, credentialed, budget-spending action, one
  of the principle's explicit exceptions to autonomous decision-making.)*
- **FR-011**: "Winning" for this effort is defined as achieving the best
  leaderboard rank reasonably achievable by the competitor's own agent
  before the deadline — there is no fixed rank/medal/score threshold below
  which the effort is considered a failure; work continues to improve
  standing for as long as the deadline allows. *(Resolved per project
  constitution Principle VI: no user-specified target was given, so the
  open-ended, always-keep-improving default was chosen — the interpretation
  most aligned with Principle I, Leaderboard-Driven Iteration.)*

### Key Entities

- **Agent**: One version of the farming strategy; holds the code/config
  version it was built from, its local evaluation results (win-rate,
  average end-of-season money vs. a fixed opponent set), its public (and
  later private/final) leaderboard rating, timestamp, and whether it is
  marked as a final selection.
- **Match / Episode**: One simulated season between two agents (the
  submission and an opponent), producing a definite outcome (win, loss, or
  tie by end-of-season money) used as a unit of both local evaluation and
  leaderboard scoring.
- **Experiment Log**: The ordered record of every attempt (submitted or
  local-evaluation-only), its hypothesis (e.g., "prioritize animal
  products over one-time crops"), its result, and the decision made
  (adopt, reject, investigate further).
- **Competition Ruleset**: The official rules (the game mechanics in
  `CONTEST.md`, plus Kaggle's competition-level rules — submission limits,
  team constraints, deadline, and disallowed behavior) that bound what the
  agent is allowed to do.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A valid, leaderboard-scored submission exists within the
  first day of active work on the competition.
- **SC-002**: Across recorded attempts, the local evaluation ranking of
  candidate strategies (by win-rate/average end-of-season money against a
  fixed opponent set) agrees with their public leaderboard rating movement
  at least 90% of the time (few surprises between local and public
  results).
- **SC-003**: 100% of scored submissions can be reproduced from a recorded,
  committed code/config state — none are "lost" or unreproducible.
- **SC-004**: Zero submission-limit violations and zero missed/late final
  submissions occur over the course of the competition.
- **SC-005**: A final submission is deliberately selected and confirmed no
  later than the competition deadline, with recorded evidence for why it
  was chosen over the alternatives.
- **SC-006**: At the moment the competition closes, the competitor's final
  rank is the best rank the recorded experiment history can support (i.e.,
  no known, already-validated improvement was left unsubmitted due to
  process failure rather than genuine time/submission-budget constraints),
  measured against the private leaderboard once released.

## Assumptions

- This is a Kaggle Simulations-style competition (like other two-player
  agent competitions Kaggle has run): competitors submit code implementing
  an agent, and standing is determined by playing matches (episodes)
  against other submitted agents rather than scoring predictions against a
  static held-out dataset. `CONTEST.md` (the game rules, provided by the
  competitor) and the referenced `kaggle_environments`-style
  `make("kaggriculture", ...)` interface are the authoritative game
  specification for this assumption.
- A Kaggle account for the competitor already exists and has accepted the
  Kaggriculture competition rules.
- Unless the competition's own rules state otherwise, standard Kaggle
  Simulations mechanics apply: a per-day and/or total submission cap, a
  rating that updates as matches complete, and the ability to select which
  submitted agent version counts as final before the deadline.
- This is a solo entry (single competitor, no team) unless stated
  otherwise.
- Local compute available to the competitor is sufficient to run many
  simulated seasons for local evaluation; larger compute needs, if any
  emerge, are a technical detail to be resolved during planning rather than
  a scope question here.
- The competition's actual submission deadline and precise leaderboard
  scoring/ranking mechanism are not yet confirmed (the live competition
  page could not be read automatically); once known, they become
  authoritative over the provisional assumptions above for all
  timing-related requirements and success criteria in this spec.
