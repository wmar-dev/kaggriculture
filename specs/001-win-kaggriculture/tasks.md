---

description: "Task list for feature implementation"
---

# Tasks: Win Kaggriculture Competition

**Input**: Design documents from `/specs/001-win-kaggriculture/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/agent-interface.md, quickstart.md

**Tests**: Included. Constitution Principle II (Trustworthy Validation, NON-NEGOTIABLE) and the plan's Testing strategy make automated tests and the local batch-evaluation harness load-bearing, not optional, for this feature.

**Organization**: Tasks are grouped by user story (spec.md) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Single project, per plan.md: `src/kaggriculture_agent/`, `evaluation/`, `tests/`, `experiments/`, `submissions/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directories per plan.md: `src/kaggriculture_agent/`, `evaluation/opponents/`, `tests/unit/`, `tests/integration/`, `experiments/`, `submissions/` (with `__init__.py` where needed for `src/kaggriculture_agent/`)
- [X] T002 Initialize Python project dependencies in `pyproject.toml` (or `requirements.txt`): `kaggle_environments`, `numpy`, `pytest` (per plan.md Technical Context)
- [X] T003 [P] Add `pytest` configuration (`pyproject.toml` `[tool.pytest.ini_options]` or `pytest.ini`) pointing at `tests/`, and add `experiments/`, `submissions/`, `__pycache__/`, `.pytest_cache/` entries to `.gitignore` where appropriate (note: `experiments/log.jsonl` and `submissions/<version>/main.py` themselves ARE committed per constitution Principle III — only caches/build noise are ignored)

**Checkpoint**: Project scaffold exists and dependencies are declared.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement observation parsing in `src/kaggriculture_agent/observation.py`: typed accessors for `GameObservation`/`FarmState`/`Tile`/`MarketState`/`TownState`/`PrivateState` per data-model.md, parsing the raw `obs` dict from `CONTEST.md`'s Observation Format
- [X] T005 [P] Implement `src/kaggriculture_agent/constants.py`: the Object Types table (seed cost, base price, yield timing per crop/animal), the Price Function parameters table, and configuration defaults, transcribed from `CONTEST.md`
- [X] T006 Implement the agent entry point skeleton in `src/kaggriculture_agent/agent.py`: `def agent(obs) -> dict` matching contracts/agent-interface.md, parsing `obs` via T004, delegating to a pluggable strategy function, defaulting to `{"farmer": ["PASS"], "hands": [], "market": []}` when no strategy is wired in yet (depends on T004)
- [X] T007 [P] Implement one custom reference opponent for local evaluation in `evaluation/opponents/greedy_agent.py` (always plant/raise the best current `Yield/tile/day` × price option that's affordable, sell opportunistically) per research.md R3 — the `"random"` and `"starter"` opponents are already built into `kaggle_environments` and addressable by name, no custom file needed for those
- [X] T008 [P] Implement the local batch-evaluation harness in `evaluation/run_batch.py`: run N seasons of a given agent vs. a named opponent via `kaggle_environments.make("kaggriculture", ...)`, report win/loss/tie counts and mean/median end-of-season money, and append an `ExperimentLogEntry` (per data-model.md) to `experiments/log.jsonl`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Get a valid baseline agent on the leaderboard (Priority: P1) 🎯 MVP

**Goal**: A simple, legal, non-crashing rule-based agent exists, is proven to survive a full simulated season, and is bundled into a submittable single file.

**Independent Test**: Run quickstart.md steps 1–4 locally; the agent completes a full 720-turn season against the `random` opponent with no errors, illegal actions, or timeouts, and `evaluation/bundle_submission.py` produces a valid single-file bundle.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract tests in `tests/integration/test_agent_contract.py`: full-episode smoke test (agent vs. `random` completes all `episodeSteps` with no exception/illegal-action/timeout), never-empty response, bounded market orders — per contracts/agent-interface.md's three acceptance tests
- [X] T010 [P] [US1] Unit tests for observation parsing in `tests/unit/test_observation.py` (covers Tile variants: `None`, `"LOCKED"`, plant, weed, animal structure)

### Implementation for User Story 1

- [X] T011 [US1] Implement the baseline rule-based strategy in `src/kaggriculture_agent/strategy.py` per research.md R4: prioritize land/labor purchases only with clear affordable ROI, plant/raise the best current `Yield/tile/day` × market-price option that fits the budget, always water/feed/care for everything owned, sell opportunistically without crashing a single good's price (depends on T004, T005)
- [X] T012 [US1] Wire the strategy into `src/kaggriculture_agent/agent.py`'s entry point, replacing the default PASS-only behavior (depends on T006, T011)
- [X] T013 [US1] Implement `evaluation/bundle_submission.py`: inline/concatenate `src/kaggriculture_agent/` modules into a single self-contained `submissions/<version>/main.py` with one `agent(obs)` entry point and no local imports, per research.md R2
- [X] T014 [US1] Run quickstart.md steps 1–4 against the baseline strategy; record the resulting `ExperimentLogEntry` in `experiments/log.jsonl` (depends on T008, T012, T013)
- [X] T015 [US1] Produce `submissions/v1/main.py` as the first submission candidate, ready for human review/upload — actually uploading to Kaggle is a separate, human-approved action per spec FR-010 and is out of scope for this task (depends on T013, T014)

**Checkpoint**: User Story 1 is fully functional and independently testable — a valid baseline agent exists and is ready for the competitor to review and submit.

---

## Phase 4: User Story 2 - Climb the leaderboard through validated iteration (Priority: P2)

**Goal**: Every strategy change is evaluated locally against a trustworthy opponent pool (including the previous submitted version) before it costs a submission, with results and disagreements recorded.

**Independent Test**: Run two competing strategy versions through `evaluation/run_batch.py`, confirm the better-performing one locally also doesn't regress vs. the `previous` opponent, and confirm both runs are logged in `experiments/log.jsonl`.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit tests for batch-evaluation aggregation/statistics in `tests/unit/test_run_batch.py` (win/loss/tie counting, mean/median money calculation)
- [ ] T017 [P] [US2] Integration test for self-play comparison in `tests/integration/test_self_play.py`: evaluating a candidate strategy against a frozen `submissions/v1/main.py` copy as the `previous` opponent

### Implementation for User Story 2

- [ ] T018 [US2] Extend `evaluation/run_batch.py` to support a `previous` opponent that loads the most recent `submissions/<version>/main.py` (depends on T008, T013)
- [ ] T019 [US2] Implement a local-vs-leaderboard divergence check (in `evaluation/run_batch.py` or a small `evaluation/divergence.py` helper) that compares a submission's local win-rate against its recorded leaderboard result once known, and flags a warning per spec's Edge Cases when they disagree sharply
- [ ] T020 [US2] Implement a second strategy iteration in `src/kaggriculture_agent/strategy.py`: improve crop/animal prioritization and market-timing/batching of sells based on `evaluation/run_batch.py` results against the `greedy` and `previous` opponents (depends on T011, T018)
- [ ] T021 [US2] Record the iteration's hypothesis, evaluation results, and adopt/reject/investigate decision as a new `ExperimentLogEntry` in `experiments/log.jsonl` (depends on T020)

**Checkpoint**: User Stories 1 AND 2 both work — strategies can now be iterated with a trustworthy local signal, self-play comparison, and a full experiment history.

---

## Phase 5: User Story 3 - Lock in the best final submission before the deadline (Priority: P3)

**Goal**: A deliberate, evidence-backed process exists for choosing which logged submission is final.

**Independent Test**: Given multiple `experiments/log.jsonl` entries with local and (where available) leaderboard results, the selection tool identifies the best-supported candidate and the competitor can confirm it as final.

### Tests for User Story 3

- [ ] T022 [P] [US3] Unit test for the final-selection ranking logic in `tests/unit/test_select_final.py` (ranks by local score, then leaderboard score when present; handles ties and missing data)

### Implementation for User Story 3

- [ ] T023 [US3] Implement `evaluation/select_final.py`: reads `experiments/log.jsonl`, ranks candidate submissions by local evaluation result (and leaderboard result when known), and prints the recommended final submission(s) with supporting rationale (depends on T008, T021)
- [ ] T024 [US3] Add a `mark_final` helper (in `evaluation/select_final.py`) that updates the chosen entry's `decision` field to `"adopt"` and flags it as the final selection in `experiments/log.jsonl`, to be invoked only after the competitor's own review (depends on T023)

**Checkpoint**: All user stories are independently functional — baseline, validated iteration, and deliberate final selection.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Write a short `README.md` pointing at `specs/001-win-kaggriculture/quickstart.md` for how to run/evaluate/bundle the agent
- [ ] T026 Run the full quickstart.md validation end-to-end (steps 1–4) after all user stories are implemented, confirming nothing regressed
- [ ] T027 [P] Add a per-turn timing assertion to `tests/integration/test_agent_contract.py` confirming the agent's decision time stays within research.md R1's internal ≤50ms budget

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational only
- **User Story 2 (Phase 4)**: Depends on Foundational; builds on US1's strategy module (T011) and bundling script (T013), but is independently testable via `evaluation/run_batch.py`
- **User Story 3 (Phase 5)**: Depends on Foundational; consumes the experiment log that US1/US2 populate (T008, T021), but its own ranking/selection logic is independently testable against any log data
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### Within Each User Story

- Tests before implementation (contract/unit tests are written to fail first, per the checklist entries)
- Observation/constants (Foundational) before strategy (US1)
- Strategy before agent wiring before bundling
- Story complete before moving to the next priority

### Parallel Opportunities

- T004, T005 (Foundational) in parallel
- T007, T008 (Foundational) in parallel, and in parallel with T004/T005 once each's own dependencies (none) are met
- T009, T010 (US1 tests) in parallel
- T016, T017 (US2 tests) in parallel with each other, and with T009/T010 if US1 and US2 are staffed simultaneously
- T025, T027 (Polish) in parallel

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together:
Task: "Contract tests in tests/integration/test_agent_contract.py"
Task: "Unit tests for observation parsing in tests/unit/test_observation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: run quickstart.md steps 1–4; confirm the contract tests pass
5. Prepare `submissions/v1/main.py` for the competitor's review and first Kaggle upload (human-approved step, FR-010)

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. User Story 1 → validate independently → first submission candidate ready (MVP)
3. User Story 2 → validate independently → trustworthy iteration loop in place
4. User Story 3 → validate independently → deliberate final-selection process in place
5. Each story adds value without breaking the previous ones

---

## Notes

- [P] tasks touch different files with no unmet dependencies
- [Story] labels map every user-story-phase task back to spec.md
- Every task that touches `experiments/log.jsonl` MUST append, never overwrite, prior entries (constitution Principle III)
- Actually uploading a submission to Kaggle is never a task here — per spec FR-010 and constitution Principle VI, it always requires the competitor's own explicit action
