---

description: "Task list for Improve Agent Beyond v18 Baseline"
---

# Tasks: Improve Agent Beyond v18 Baseline

**Input**: Design documents from `/specs/002-improve-agent/`

**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required for user stories), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md)

**Tests**: Included — `evaluation/select_final.py` already has direct unit coverage in `tests/unit/test_select_final.py`, and the one code change in this feature (T005-T006) extends that existing suite, matching this codebase's established practice.

**Organization**: Tasks are grouped by user story (see [spec.md](./spec.md)) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Single project, unchanged from `specs/001-win-kaggriculture`: `src/kaggriculture_agent/`, `evaluation/`, `tests/`, `experiments/`, `submissions/` at the repository root.

---

## Phase 1: Setup

**Purpose**: Confirm the existing toolchain this feature builds on is in a working, known-good state before changing anything.

- [X] T001 Run `make test` from the repo root and confirm the full existing suite passes before any change (baseline sanity check; no file changes) — 69 passed
- [X] T002 Run `make select` (`evaluation/select_final.py`) against the real `experiments/log.jsonl` and note the current top-ranked candidate and its evaluation results, as the starting "current best" for this round (per research.md R1; no file changes, this is a recorded observation only) — current best is `v18`, 100% vs random/starter/greedy, 14W/6L (70%) vs `v17` over only 20 seasons

**Checkpoint**: Toolchain confirmed working; current best version identified.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None of this feature's three user stories share a code-level blocking dependency — Setup above (a working toolchain, a known current best) is the only true prerequisite. This phase is intentionally empty; proceed directly to Phase 3.

**Checkpoint**: N/A — user story work can begin immediately after Setup.

---

## Phase 3: User Story 1 - Ratchet the current-best agent forward with confirmed wins (Priority: P1) 🎯 MVP

**Goal**: `evaluation/select_final.py` never lets an unconfirmed, small-sample result stand as the recommended current best without saying so — closing the exact gap research.md's "Bench noise" finding exposed (a 65% edge over 20 seasons that was 53%, i.e. noise, pooled over 120).

**Independent Test**: Feed `rank_candidates()`/`format_recommendation()` a fabricated top candidate with (a) no self-play evaluation result, (b) a self-play result under 100 pooled seasons, and (c) a self-play result at or above 100 pooled seasons, and confirm a caution prints for (a) and (b) but not (c).

### Tests for User Story 1

> Write these tests FIRST; confirm they fail before T005/T006.

- [X] T003 [P] [US1] Add unit tests to `tests/unit/test_select_final.py`: `test_format_recommendation_cautions_when_top_candidate_has_no_self_play_result` and `test_format_recommendation_cautions_when_self_play_seasons_below_threshold` — both asserting the caution text appears in `format_recommendation()`'s output for a fabricated entry built with the file's existing `_entry_with_opponents` helper
- [X] T004 [P] [US1] Add a third unit test to `tests/unit/test_select_final.py`: `test_format_recommendation_no_caution_when_self_play_seasons_meet_threshold` — asserting no caution text appears when the top candidate's pooled self-play seasons total ≥ 100 (build the fixture with multiple `seasons`-bearing self-play result dicts summing to ≥100, mirroring the pooling pattern in `test_rank_candidates_pools_every_entry_for_a_version`)

### Implementation for User Story 1

- [X] T005 [US1] In `evaluation/select_final.py`, add a `CONFIRMATION_SEASONS = 100` module-level constant (cite research.md R2 in a one-line comment) and a `_self_play_seasons(entry) -> int` helper that sums `r.get("seasons") or (r.get("wins",0)+r.get("losses",0)+r.get("ties",0))` over the same path-shaped-opponent result set `_self_play_win_rate()` already isolates (depends on T003/T004 existing and failing)
- [X] T006 [US1] In `evaluation/select_final.py`'s `format_recommendation()`, after the existing win-rate/opponent lines, append a caution line when `_self_play_seasons(entry) < CONFIRMATION_SEASONS` (covering the zero-result case too, since 0 < 100): e.g. `"  CAUTION: only N head-to-head season(s) recorded against a prior version (< 100) -- this promotion is unconfirmed; see research.md R2 before trusting it."`; run `pytest tests/unit/test_select_final.py -q` and confirm T003/T004 now pass and no prior test in that file regressed (depends on T005) — 17/17 passed
- [X] T007 [US1] Run `make select` against the real `experiments/log.jsonl` again and confirm the caution's actual behavior against real data matches expectations — it correctly flagged `v18` itself as unconfirmed (only 20 pooled seasons vs `v17`, 70%); ran an 80-season confirmation batch (`evaluation/run_batch.py --agent submissions/v18/main.py --opponents submissions/v17/main.py --seasons 80 --agent-version v18 ...`), pooling to 100 seasons at 75W/25L (75%) — the edge holds, it was not noise. `make select` now shows no caution for `v18`

**Checkpoint**: User Story 1 is independently complete — running `make select` at any time from now on always makes an unconfirmed promotion visible instead of silent.

---

## Phase 4: User Story 2 - Avoid re-investigating already-rejected ideas (Priority: P2)

**Goal**: A documented, repeatable lookup step (quickstart.md step 2) reliably surfaces a prior attempt at a candidate idea before a new evaluation batch is spent on it.

**Independent Test**: Run the quickstart.md step-2 lookup command for at least two hypotheses already known to be settled in `experiments/log.jsonl` (the `PLOT_WORKERS` weak-town-edge noise result and the rejected ROI-based animal cutoff) and confirm both are surfaced with their recorded `decision`.

### Implementation for User Story 2

- [X] T008 [P] [US2] Run the `grep`/`jq` lookup command from `specs/002-improve-agent/quickstart.md` step 2 against the real `experiments/log.jsonl` for the keyword `PLOT_WORKERS` and confirm the prior "noise" finding's entry (and its `decision`) is returned (validation task; no file change unless the command needs a fix, in which case fix it in `specs/002-improve-agent/quickstart.md`) — **finding**: the `experiments/log.jsonl` grep alone returned nothing; the PLOT_WORKERS re-sweep result lives only as prose in `specs/001-win-kaggriculture/research.md` (a rejected/noise finding, not a promoted version, so it was never a log entry). Fixed quickstart.md step 2 to search both sources.
- [X] T009 [P] [US2] Repeat T008 for a keyword matching the rejected ROI-based animal cutoff hypothesis, confirming that entry and its `decision` are also returned — **finding**: same gap; `ROI` in `experiments/log.jsonl` only matches unrelated older entries (`v14-dev`, `v16-goose-roi`), not the actual rejected `ANIMAL_ROI_MARGIN` finding, which is also research.md-only prose. Confirmed the two-source lookup (log + both research.md files) now surfaces it correctly.
- [X] T010 [US2] Add a short "Already-settled ideas" list to the top of `specs/002-improve-agent/quickstart.md` (before step 1), naming the specific hypotheses confirmed as rejected/noise so far (from T008/T009 and any others already visible in the log, e.g. the PLOT_WORKERS weak-town edge and the ROI-based animal cutoff) with a one-line pointer to their log entries, so a competitor sees the most common repeat-offenders without needing to grep first (depends on T008, T009)

**Checkpoint**: User Story 2 is independently complete — the lookup step is verified against real settled ideas and the most likely repeat-offenders are visible up front.

---

## Phase 5: User Story 3 - Target specific, already-observed weaknesses first (Priority: P3)

**Goal**: The next candidate strategy change is chosen because it targets a concrete, evidence-backed weakness of the current best version (`v18`), not undirected exploration — and that change is actually evaluated through to an adopt/reject decision.

**Independent Test**: `evaluation/demand_bench.py` run against the current best version produces a specific stratified losing pattern; a candidate change naming that pattern in its hypothesis is evaluated via the quickstart.md workflow and reaches a recorded `adopt` or `reject` decision.

### Implementation for User Story 3

- [X] T011 [US3] Run `evaluation/demand_bench.py --agent submissions/v18/main.py --opponent submissions/v17/main.py --games 120` (or the current top-ranked pair from T002/T007) and record the stratified weak-town-vs-strong-town result as a new `"investigate"` entry in `experiments/log.jsonl` (via the script's own logging, or a manual append matching the `ExperimentLogEntry` shape) whose `hypothesis` states the specific losing pattern found, per spec FR-008 — **finding**: 96% win-rate in weak-demand towns (n=28) vs 74% in strong-demand towns (n=92), 79% overall; matches the same weak/strong gap already visible in v18's own feeding-ratio sweep table in research.md, never closed
- [X] T012 [US3] Based on T011's finding, implement one candidate strategy change in `src/kaggriculture_agent/strategy.py` whose change explicitly targets that named weakness (not an unrelated idea), depends on T011 — checked research.md first (per US2 discipline) and confirmed a *uniform* MAX_STRUCTURES raise is already repeatedly rejected (18/21/22/26 all lost badly, in weak towns it gluts the market); implemented a demand-gated ceiling instead (`_structure_ceiling`/`_town_demand`: 15 base, 18 only when town MILK+WOOL demand ≥ 4, matching demand_bench.py's own weak/strong boundary) — untried variant, not a repeat
- [X] T013 [US3] Evaluate the T012 candidate using `specs/002-improve-agent/quickstart.md` steps 4-6 (initial batch → confirmation batch if promising → full reference-pool regression check) and append the resulting `investigate`/`adopt`/`reject` decision to `experiments/log.jsonl`, depends on T012 — **result**: 4W/13L/3T (20%) over 20 seasons vs v18, a clear loser (no confirmation batch needed per the existing 20-seasons-screens-out-losers rule); logged `decision: "reject"` with a note on plausible causes for a future round, and reverted the `strategy.py` change (`git checkout --`) so `src/` stays at the confirmed v18 baseline
- [X] T014 [US3] If T013 resulted in `adopt`, bundle the new version with `evaluation/bundle_submission.py` into `submissions/<next-version>/main.py` and re-run `make select` to confirm it is now the recommended current best with no caution from T006, depends on T013 — **skipped**: T013 was a reject, not an adopt; this task's precondition was not met. `v18` remains the current best (per T007, confirmed at 100 self-play seasons, no caution)

**Checkpoint**: All three user stories independently complete — the promotion signal is trustworthy (US1), settled ideas aren't re-litigated (US2), and at least one weakness-targeted candidate has been carried through to a recorded decision (US3).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency pass across the whole feature.

- [X] T015 [P] Run `make test` again and confirm the full suite (including the T003/T004 additions) passes with no regressions — 72 passed
- [X] T016 [P] Walk through `specs/002-improve-agent/quickstart.md` end-to-end once more against the post-T014 repo state and fix any command/path in it that no longer matches reality (e.g., an updated current-best version number) — **fix applied**: step 4's example called `make evaluate SEASONS=20 AGENT=src/kaggriculture_agent/agent.py`, but the `Makefile`'s `evaluate` target has no `AGENT=` override (it hardcodes that same path already); corrected the step to say so instead of implying a variable that doesn't exist
- [X] T017 Review `experiments/log.jsonl` entries added in T011/T013/(T014) for completeness against the `ExperimentLogEntry` shape in `specs/001-win-kaggriculture/data-model.md` (timestamp, agent_version, commit_sha, hypothesis, evaluation_results, kaggle_result, decision all present) — both entries (the T011 demand_bench finding, the T013 reject) carry all six fields; T014 added no entry (task was skipped, not applicable)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Empty — no blocking work
- **User Story 1 (Phase 3)**: Depends on Setup only
- **User Story 2 (Phase 4)**: Depends on Setup only; fully independent of US1's code change
- **User Story 3 (Phase 5)**: Depends on Setup only; independent of US1/US2, though T014 benefits from T006/T007's caution already existing to sanity-check the new promotion
- **Polish (Phase 6)**: Depends on all three user stories being complete

### Within Each User Story

- US1: tests (T003, T004) before implementation (T005, T006); T007 (real-data check) after
- US2: lookup validation (T008, T009) before the documentation update that depends on their findings (T010)
- US3: strictly sequential — each task's input is the previous task's output (weakness → change → evaluation → bundle)

### Parallel Opportunities

- T003, T004 (US1 tests) in parallel with each other
- T008, T009 (US2 lookups) in parallel with each other
- Phases 3, 4, and 5 (US1, US2, US3) can be worked in parallel by different people/sessions once Setup is done — they touch disjoint files (`evaluation/select_final.py` + its test file vs. `specs/002-improve-agent/quickstart.md` vs. `src/kaggriculture_agent/strategy.py` + `experiments/log.jsonl`)
- T015, T016 (Polish) in parallel

---

## Parallel Example: User Story 1

```bash
# Launch both new-behavior tests for User Story 1 together:
Task: "Add test_format_recommendation_cautions_when_top_candidate_has_no_self_play_result to tests/unit/test_select_final.py"
Task: "Add test_format_recommendation_cautions_when_self_play_seasons_below_threshold to tests/unit/test_select_final.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (T003-T007)
3. **STOP and VALIDATE**: `make select` now visibly cautions on any unconfirmed top candidate — this alone closes the highest-severity gap (spec FR-003, SC-001) and is safe to rely on even before US2/US3 are done

### Incremental Delivery

1. Setup → toolchain confirmed, current best known
2. User Story 1 → the promotion signal becomes trustworthy (MVP)
3. User Story 2 → wasted re-investigation becomes preventable
4. User Story 3 → produces this round's actual candidate improvement attempt, carried to a decision
5. Polish → whole feature re-verified together

## Notes

- [P] tasks touch different files with no unmet dependencies
- [Story] labels map every user-story-phase task back to spec.md
- This feature adds no new dependencies, schema fields, or subsystems (plan.md Summary) — nearly every task is either a small additive code change with tests (US1) or applying existing tooling per a documented workflow (US2, US3)
- Every task touching `experiments/log.jsonl` MUST append, never overwrite, prior entries (constitution Principle III, carried over from `specs/001-win-kaggriculture/tasks.md`)
- Actually uploading a submission to Kaggle is never a task here — per `specs/001-win-kaggriculture/spec.md` FR-010 and constitution Principle VI, it always requires the competitor's own explicit action
