# Implementation Plan: Improve Agent Beyond v18 Baseline

**Branch**: `002-improve-agent` | **Date**: 2026-09-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-improve-agent/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

This feature does not introduce new subsystems. It formalizes a process gap
this project's own history already exposed: initial evaluation batches
(16-40 seasons) have repeatedly produced results that flipped at a larger
confirmation scale (research.md's "Bench noise" finding — a 65% edge fell
to 53% pooled over 120 seasons). The existing evaluation toolchain
(`evaluation/run_batch.py`, `evaluation/demand_bench.py`,
`evaluation/select_final.py`, `experiments/log.jsonl`) already provides
every mechanism the spec's requirements need; the work here is (1) one
small, additive change to `evaluation/select_final.py` so an unconfirmed,
small-sample "adopt" cannot silently rank as the current best, and (2) a
documented, repeatable workflow (in `quickstart.md`) for confirmation runs,
prior-attempt lookup, and weakness-first prioritization — then applying that
workflow to actually produce and confirm a strategy improvement over `v18`.

## Technical Context

**Language/Version**: Python 3.11 (unchanged from `specs/001-win-kaggriculture`
— this feature extends the existing package, it does not start a new one).

**Primary Dependencies**: None added. Reuses `kaggle_environments`, the
project's own `evaluation/` scripts, and Python standard library only, per
`specs/001-win-kaggriculture/plan.md`.

**Storage**: Flat files only, unchanged — `experiments/log.jsonl` remains
the single experiment record; no schema change (see data-model.md below for
the one clarified/added convention).

**Testing**: `pytest`, extending the existing `tests/unit/test_select_final.py`
to cover the new low-sample caution; no new test tooling.

**Target Platform**: Unchanged — local development machine for evaluation,
Kaggle's sandboxed runner for the submitted agent.

**Project Type**: Single project — same package as `001-win-kaggriculture`;
this is an iteration on it, not a new project.

**Performance Goals**: N/A beyond what `001-win-kaggriculture` already
requires (per-turn decision time, batch-evaluation throughput). No new
performance target.

**Constraints**: Same as `001-win-kaggriculture` (no network access/deps in
the submitted agent file, human approval required before any Kaggle
upload). This feature adds one process constraint of its own: an "adopt"
decision in the experiment log MUST be backed by a confirmation-scale batch
(≈100+ seasons) against the opponent the promotion claim is about, not an
initial screening batch alone (spec FR-003).

**Scale/Scope**: Confirmation batches of ~100+ simulated seasons per
promising candidate, consistent with research.md's existing "Bench noise"
guidance (20 seasons screens out losers; ~100+ needed to trust a 55-60%
edge) and the `SEASONS` default already documented in the `Makefile`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --- | --- | --- |
| I. Leaderboard-Driven Iteration | PASS | This feature exists specifically to make the experiment log's "highest-value next step" signal trustworthy (weakness-first prioritization, no re-testing dead ends). |
| II. Trustworthy Validation (NON-NEGOTIABLE) | PASS | FR-003's confirmation-batch requirement directly enforces this principle's "no submission justified by an untrustworthy signal" rule, closing a gap this project's own history shows was real. |
| III. Full Reproducibility | PASS | No change to logging discipline — every evaluation, adopted or not, still appends to `experiments/log.jsonl`; the one addition (a caution flag) reads existing log data, writes nothing new. |
| IV. Rules & Legal Compliance (NON-NEGOTIABLE) | PASS | No new data/technique introduced; unaffected. |
| V. Time-Boxed Simplicity | PASS | Deliberately no new subsystem: reuses `run_batch.py`, `demand_bench.py`, `select_final.py` as-is wherever they already satisfy a requirement; the only code change is a small, additive warning in one existing function. |
| VI. Autonomous Clarification | PASS | No blocking questions raised; the "current best" ↔ `previous`-opponent equivalence (Research R1) was resolved autonomously and recorded rather than asked about. |

No violations — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-improve-agent/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory is added: this feature introduces no new external
interface. The Kaggle submission interface contract is unchanged and stays
at `specs/001-win-kaggriculture/contracts/agent-interface.md`.

### Source Code (repository root)

```text
# Existing structure from specs/001-win-kaggriculture, extended (not replaced):
src/kaggriculture_agent/
├── strategy.py           # Candidate strategy changes for this round land here, same as always
└── ...                   # (observation.py, constants.py, agent.py unchanged by this feature)

evaluation/
├── run_batch.py          # Unchanged; used for initial + confirmation batches per candidate
├── demand_bench.py        # Unchanged; used to find/confirm weakness-targeted candidates (FR-008)
└── select_final.py        # ONE additive change: flag an "adopt" ranked #1 on an unconfirmed
                            # sample size, per spec FR-003/FR-007 (see data-model.md)

tests/unit/
└── test_select_final.py   # Extended with cases for the new low-sample caution

experiments/
└── log.jsonl              # No schema change; same ExperimentLogEntry shape as 001's data-model.md
```

**Structure Decision**: No new top-level structure. This feature is an
in-place extension of the single project established by
`specs/001-win-kaggriculture`: one small, additive code change plus a
documented workflow, applied using the tooling that already exists.

## Complexity Tracking

*No Constitution Check violations — this section is not applicable.*
