# Implementation Plan: Win Kaggriculture Competition

**Branch**: `001-win-kaggriculture` | **Date**: 2026-09-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-win-kaggriculture/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build and continuously improve a Python agent for the Kaggriculture Kaggle
Simulations competition (a two-player farming-economy game defined in
`CONTEST.md`): given the shared observation each turn, decide farmer/hand
actions and market orders to maximize end-of-season bank money against an
opponent agent. The approach is a fast, dependency-light heuristic/planning
agent (no training data exists — this is a game-playing agent, not a
supervised model), developed behind a local batch-evaluation harness that
plays many simulated seasons against reference opponents before any result
is spent on a real Kaggle submission, with every attempt logged for
reproducibility (constitution Principles I–III, V) and every actual Kaggle
upload gated on explicit human approval (Principle VI's irreversible-action
exception, spec FR-010).

## Technical Context

**Language/Version**: Python 3.11 (dictated by the domain: Kaggle
Simulations agents run via `kaggle_environments`, a Python package, and
`CONTEST.md`'s quickstart example is Python; this is not a free choice).

**Primary Dependencies**: `kaggle_environments` (the Kaggriculture
environment/engine, `make("kaggriculture", ...)`); Python standard library
only for the agent's decision logic itself, so the submitted file stays
simple to bundle and has no runtime network/install dependency inside
Kaggle's sandbox; `numpy` (optional, for batch-evaluation statistics, not
inside the submitted agent); `pytest` for unit/contract tests.

**Storage**: Flat files only — no database. Git is the source of truth for
code/config versioning (constitution Principle III). A JSON Lines
experiment log (`experiments/log.jsonl`, one record per attempt: strategy
description, local evaluation result, leaderboard result once known,
commit hash) satisfies spec FR-003. No other persistent storage is needed.

**Testing**: `pytest` for unit tests (observation parsing, action
encoding, individual strategy rules) and integration/contract tests
(agent completes a full 720-turn episode against a reference opponent via
`kaggle_environments` without an error, illegal action, or timeout — spec
FR-001, Edge Cases). The local batch-evaluation harness (many simulated
seasons vs. a fixed opponent pool, reporting win-rate and average
end-of-season money) is the primary tool satisfying FR-002/SC-002 and is
distinct from the pytest suite, which only guards correctness/regressions.

**Target Platform**: Developed and evaluated locally (this machine); the
deliverable is a single self-contained Python file (the Kaggle Simulations
submission format for an agent — one file, no local imports, no network
access at inference time) that runs inside Kaggle's sandboxed episode
runner.

**Project Type**: Single project — a small Python package plus scripts
(not a web/mobile/multi-service app).

**Performance Goals**: Each per-turn action decision MUST return well
within Kaggle's configured per-turn time budget for this competition.
*(NEEDS CLARIFICATION, deferred to research.md: the exact per-turn/episode
time limit is not stated in `CONTEST.md` and the live competition page
could not be fetched automatically; per constitution Principle VI this is
NOT a blocking clarification — research.md records a conservative default
target and the assumption is revisited once the real limit is confirmed.)*

**Constraints**: No network access and no dependencies beyond what
Kaggle's simulation runner provides MUST be assumed for the submitted
agent file (standard Kaggle Simulations sandboxing); the agent MUST
tolerate the full range of legal actions/inputs described in `CONTEST.md`
without crashing (a crash forfeits the match).

**Scale/Scope**: Local batch evaluation MUST be able to run at least
several dozen full 720-turn simulated seasons per strategy comparison in
a few minutes on a laptop, so that iteration (constitution Principle I)
is not bottlenecked by evaluation speed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --- | --- | --- |
| I. Leaderboard-Driven Iteration | PASS | Experiment log + batch evaluation harness exist specifically to prioritize changes by expected impact on end-of-season money / leaderboard rating. |
| II. Trustworthy Validation (NON-NEGOTIABLE) | PASS | Local batch evaluation against a fixed, reproducible opponent pool is the required signal before any submission (FR-002); Edge Cases require flagging local/leaderboard disagreement. |
| III. Full Reproducibility | PASS | Git-versioned code/config, one submittable file per version, experiment log records the commit each result came from (FR-003, FR-008). |
| IV. Rules & Legal Compliance (NON-NEGOTIABLE) | PASS | No external data, no Kaggle ToS-violating automation is planned; submission mode (FR-010) requires human approval, which also naturally prevents runaway/automated rule violations. |
| V. Time-Boxed Simplicity | PASS | Chosen approach is a dependency-light heuristic agent first (no ML training pipeline, no exotic architecture) with a single-file deliverable; complexity (e.g., search/learned policies) is deferred until a simple baseline's ceiling is understood. |
| VI. Autonomous Clarification | PASS | The one open technical unknown (per-turn time limit) is resolved with a conservative default in research.md rather than blocking; the one exception invoked (Kaggle upload approval) matches the principle's own carve-out. |

No violations — Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-win-kaggriculture/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── agent-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# Option 1: Single project
src/
└── kaggriculture_agent/
    ├── __init__.py
    ├── agent.py          # Kaggle submission entry point: agent(obs, config) -> actions
    ├── strategy.py        # Decision logic (planting/market/hiring heuristics)
    ├── observation.py     # Parses the raw obs dict into typed farm/market/town state
    └── constants.py        # Object-type table, market params, etc. from CONTEST.md

evaluation/
├── run_batch.py          # Local batch evaluator: N seasons vs. an opponent, win-rate + $ stats
└── opponents/             # Reference opponents used for local evaluation (random, do-nothing, prior versions)

tests/
├── unit/                  # observation parsing, individual strategy rules
└── integration/            # full-episode smoke test via kaggle_environments

experiments/
└── log.jsonl              # FR-003 experiment log: one line per attempt

submissions/
└── <version>/agent.py      # Frozen, single-file bundle actually uploaded for that version
```

**Structure Decision**: Single project (Option 1). The competition has no
frontend/backend split and no mobile target — it is one Python package
(`src/kaggriculture_agent/`) implementing the agent, a separate
`evaluation/` toolset for local validation (kept out of the submission
bundle), and `experiments/` + `submissions/` as the reproducibility/audit
trail required by constitution Principle III and spec FR-003/FR-008.

## Complexity Tracking

*No Constitution Check violations — this section is not applicable.*
