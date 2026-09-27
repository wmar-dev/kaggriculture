# Feature Specification: Improve Agent Beyond v18 Baseline

**Feature Branch**: `002-improve-agent`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Improve agent"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ratchet the current-best agent forward with confirmed wins (Priority: P1)

As the competitor, I want to keep finding strategy changes that beat the
current best agent version (v18) by a real, non-noise margin, so that each
promotion to a new "current best" version represents genuine strength
gained, not a fluke result from a small evaluation batch.

**Why this priority**: The entire point of this effort is a stronger agent.
If a "win" that later turns out to be noise gets promoted, the competitor
loses ground while believing they gained it — exactly the failure mode
already observed in this project's history (small-batch results flipping on
a larger confirmation run).

**Independent Test**: Can be fully tested by taking any candidate strategy
change, running it through an initial evaluation batch against the current
best version, and — only for promising results — a larger confirmation
batch against the same opponent, then confirming the promotion decision
matches the confirmed (not the initial) result.

**Acceptance Scenarios**:

1. **Given** a candidate strategy change, **When** it is evaluated against
   the current best version across an initial batch of simulated seasons,
   **Then** a win-rate and average end-of-season money for both sides are
   produced.
2. **Given** an initial batch result that favors the candidate, **When** a
   larger confirmation batch is run against the same opponent, **Then** the
   candidate is promoted to "current best" only if the confirmation batch
   still favors it; otherwise it is rejected or marked inconclusive.
3. **Given** a newly promoted current-best version, **When** it is checked
   against the fixed reference opponent pool (random, starter, greedy) that
   the previous best already beat, **Then** it does not regress against any
   of them.

---

### User Story 2 - Avoid re-investigating already-rejected ideas (Priority: P2)

As the competitor, I want to check the experiment log before spending an
evaluation batch on a strategy idea, so that ideas already tested and
rejected (or shown to be noise) are not re-run from scratch without new
information that would change the expected outcome.

**Why this priority**: Evaluation batches and wall-clock time are limited;
repeating a already-answered question is waste that directly competes with
time available to test genuinely new ideas.

**Independent Test**: Can be fully tested by picking a strategy idea,
searching the experiment log for a prior attempt at the same or a materially
similar hypothesis, and confirming that a prior rejected/no-op result is
surfaced before any new evaluation batch is run for it.

**Acceptance Scenarios**:

1. **Given** a new candidate idea, **When** the experiment log is checked,
   **Then** any prior attempt at the same or a materially similar hypothesis
   (and its recorded decision) is found before a new evaluation run starts.
2. **Given** a prior attempt was recorded as "rejected" or "noise" with no
   new information changing the situation, **Then** the idea is not
   re-evaluated from scratch.
3. **Given** a prior attempt's outcome is genuinely uncertain (e.g., an
   initial promising result never got a confirmation batch), **Then** it is
   treated as unresolved and eligible for a confirming re-run, not as a
   settled rejection.

---

### User Story 3 - Target specific, already-observed weaknesses first (Priority: P3)

As the competitor, I want new candidate improvements to be prioritized
against weaknesses already surfaced by prior evaluation (e.g., matches
where the current best loses money or loses outright to a specific opponent
pattern or town condition), so that effort goes toward the changes most
likely to move the win-rate, rather than unrelated exploration.

**Why this priority**: Undirected exploration is lower expected value than
following up on concrete evidence already collected; this priority matters
less than not regressing (P1) or not wasting effort on dead ends (P2), but
still meaningfully affects how fast the leaderboard rank improves.

**Independent Test**: Can be fully tested by pulling the current best
version's losses/near-losses from recorded evaluation data, confirming at
least one concrete weakness is identified from them, and confirming a
candidate change is proposed that targets that specific weakness.

**Acceptance Scenarios**:

1. **Given** the experiment log and evaluation results for the current best
   version, **When** they are reviewed, **Then** at least one concrete,
   specific weakness (a losing pattern, not a vague guess) is identified.
2. **Given** an identified weakness, **When** a candidate change is
   proposed, **Then** its hypothesis explicitly names the weakness it is
   meant to address.

---

### Edge Cases

- What happens when a candidate change wins against the current best version
  but regresses against one or more of the fixed reference opponents (random,
  starter, greedy)? The regression MUST be treated as disqualifying unless
  explicitly and deliberately accepted with a recorded reason.
- What happens when an initial small-batch result and a larger confirmation
  batch disagree (as already observed for several v17/v18 candidates)? The
  larger-sample result MUST govern the promotion decision.
- What happens when two candidate changes are both promising but interact
  badly when combined (each individually beats the current best, but the
  combination does not)? The combination MUST be evaluated on its own before
  being adopted together — individual results MUST NOT be assumed to compose.
- What happens when no candidate change beats the current best version after
  a reasonable investigation effort? The current best version MUST remain the
  standing baseline; it is a valid outcome for a round of investigation to
  produce no promotion.
- What happens when the current best version itself is later found to have a
  bug (not a strategy weakness) that inflated its recorded results? The bug
  MUST be fixed and the current best version's baseline results MUST be
  re-established before further candidates are judged against it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: At any point in time, exactly one agent version MUST be
  designated the "current best" — the baseline that every new candidate
  strategy change is evaluated against.
- **FR-002**: A candidate strategy change MUST be evaluated against the
  current best version across an initial batch of simulated seasons before
  any promotion decision is made.
- **FR-003**: A candidate strategy change MUST NOT be promoted to "current
  best" on the strength of an initial batch result alone; a promising
  initial result MUST be re-checked with a larger confirmation batch against
  the same opponent, and the promotion decision MUST follow the confirmation
  batch's result.
- **FR-004**: A candidate strategy change MUST also be checked against the
  fixed reference opponent pool (random, starter, greedy, and prior versions
  used as regression benchmarks) before promotion, and MUST NOT be promoted
  if it regresses against any opponent the current best version already
  beat, unless the regression is explicitly and deliberately accepted with a
  recorded reason.
- **FR-005**: Before a new candidate idea is evaluated, the experiment log
  MUST be checked for a prior attempt at the same or a materially similar
  hypothesis; an idea already recorded as rejected or confirmed-noise MUST
  NOT be re-evaluated without new information that would change the expected
  outcome.
- **FR-006**: Every evaluation of a candidate strategy change (win-rate,
  money outcome, and the decision: adopt, reject, or investigate further)
  MUST be recorded in the experiment log, consistent with the existing
  experiment-log requirement for this project.
- **FR-007**: When a candidate is promoted to "current best," that fact MUST
  be recorded unambiguously (e.g., in the experiment log and/or the
  submissions directory) so later work always knows the correct current
  baseline to test against.
- **FR-008**: Investigation MUST prioritize candidate changes that target a
  concrete weakness already observed in the current best version's recorded
  evaluation results (a specific losing pattern) over undirected exploration,
  whenever such an observed weakness exists and is not already being
  actively investigated.
- **FR-009**: This effort MUST continue to operate within the existing
  submission-budget, reproducibility, and human-approval-for-upload
  constraints already established for this project (see
  `specs/001-win-kaggriculture/spec.md` FR-004, FR-007, FR-008, FR-010).

### Key Entities

- **Current Best Version**: The single agent version presently designated as
  the baseline to beat; every candidate strategy change is judged against
  it, and it changes only on a confirmed promotion.
- **Candidate Change**: A single proposed strategy modification under
  investigation, with a stated hypothesis (what weakness it targets or what
  behavior it changes), an initial evaluation result, and — if promising — a
  confirmation evaluation result.
- **Weakness**: A concrete, evidence-backed losing pattern of the current
  best version (e.g., a specific opponent matchup, town condition, or game
  phase where it loses money or the match), identified from recorded
  evaluation data rather than guessed.
- **Experiment Log** *(shared with `specs/001-win-kaggriculture`)*: The
  ordered record of every attempt, extended here with enough detail to
  distinguish an initial result from its confirmation result and to mark
  which entry (if any) corresponds to the current best version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every promoted "current best" version's win-rate improvement
  over the version it replaced holds up in a confirmation batch at least as
  large as the one that first flagged it as promising (no promotion stands
  on an unconfirmed small-sample result alone).
- **SC-002**: Zero promoted versions regress against any reference opponent
  (random, starter, greedy) that the previous current best version already
  beat, without an explicit, recorded reason for accepting that regression.
- **SC-003**: Zero strategy ideas are re-evaluated from scratch after
  already being recorded as rejected or confirmed-noise with no new
  information.
- **SC-004**: At least one concrete, evidence-backed weakness of the current
  best version is identified and has a candidate change proposed against it
  before undirected exploration is prioritized ahead of it.
- **SC-005**: The current best version's identity is unambiguous at every
  point during this effort — anyone reviewing the experiment log can
  determine, without guessing, which version to beat next.

## Assumptions

- "Improve agent" continues the existing effort defined in
  `specs/001-win-kaggriculture/spec.md` (winning the Kaggriculture
  competition) rather than starting an unrelated new agent; this spec adds
  process requirements for this next round of iteration rather than
  replacing that spec's scope, goals, or constraints.
- The current best version at the start of this effort is `v18` (per
  `experiments/log.jsonl`); this is expected to change as this effort
  succeeds, and "current best" always refers to whichever version is
  presently so designated, not literally v18 forever.
- "A larger confirmation batch" follows the pattern already established in
  this project's own history (an initial batch of roughly 16-40 simulated
  seasons, confirmed at roughly 100 seasons before trusting the result) — no
  new statistical framework is introduced; this is an explicit requirement
  to keep doing what has already proven necessary, not a new technique.
- This effort does not by itself require a new Kaggle submission; producing
  a confirmed, improved current-best version is the deliverable, and
  whether/when to spend submission budget on it remains governed by
  `specs/001-win-kaggriculture/spec.md` FR-004/FR-010 and the project
  constitution's human-approval requirement for any actual upload.
- The fixed reference opponent pool (random, starter, greedy) and the
  practice of also benchmarking against prior submitted versions continue
  unchanged from current practice; this spec does not redefine that pool.
