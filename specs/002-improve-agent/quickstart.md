# Quickstart: Improve Agent Beyond v18 Baseline

Validation guide for this feature's process — run through this each time a
new round of strategy improvement starts. Assumes the `001-win-kaggriculture`
environment is already set up (`make install`, per its own quickstart.md).

## Already-settled ideas (check here before step 2's lookup)

The most likely repeat-offenders as of this writing — don't re-spend a
batch on these without a stated reason the situation changed:

- **PLOT_WORKERS != 3** (wheat-plot crew size): 2 workers loses clearly
  (17%); 4 workers looked promising in a weak-town-only slice at n=100
  (68%) but that did not survive a 260-season confirmation (52%
  overall/56% weak) — noise. See
  `specs/001-win-kaggriculture/research.md`, "constant re-sweep" section
  near the end (search `PLOT_WORKERS vs 3`).
- **ROI-based late animal-buy cutoff** (`ANIMAL_ROI_MARGIN` replacing the
  plain reachability check, `BUY_CUTOFF_MARGIN`): every margin tested
  (0.5-2.0) underperformed the simple reachability check; rejected,
  `BUY_CUTOFF_MARGIN=2` stands. Same research.md section (search
  `ANIMAL_ROI_MARGIN`).
- **REINVEST_RESERVE/LAND_RESERVE_MULT/HIRE_COST_CEILING re-sweeps against
  v18**: all re-tested values were neutral or losing; the v17-era values
  (1.0 / 1.2 / 55) stand. Same section.

These live in `research.md` prose, not `experiments/log.jsonl` — they were
negative/rejected results from a re-sweep, not a promoted version, so
step 2's log-only lookup would miss them.

## 1. Find the current best version

```bash
make select
# or: .venv/bin/python evaluation/select_final.py
```

Confirms spec FR-001/SC-005: this MUST print exactly one recommended
version — that is "current best" for this round (research.md R1). If the
caution added by this feature (research.md R2/data-model.md) prints for the
top result, treat that result as unconfirmed and get a larger-sample run
before relying on it further, per FR-003.

## 2. Before investigating a new idea, check it hasn't already been settled

**Check both places** — not every settled idea gets its own
`experiments/log.jsonl` entry. Several (e.g. the PLOT_WORKERS weak-town
re-sweep, the rejected ROI-based animal cutoff) were recorded as prose in
`research.md` instead, once the finding was a rejection/negative result
rather than a promoted version:

```bash
# 1. The structured experiment log (per-attempt records):
grep -i "<keyword-for-the-idea>" experiments/log.jsonl | \
  .venv/bin/python -c "import sys, json; [print(json.dumps({k: e[k] for k in ('agent_version','hypothesis','decision')}, indent=2)) for e in map(json.loads, sys.stdin)]"

# 2. The prose research record (negative results / rejections often live only here):
grep -in "<keyword-for-the-idea>" specs/001-win-kaggriculture/research.md specs/002-improve-agent/research.md
```

(Or `jq` for step 1 if installed: `grep -i "<keyword>" experiments/log.jsonl | jq '{agent_version, hypothesis, decision}'`.)

Confirms spec FR-005/SC-003: if a matching entry shows `"decision":
"reject"`, or `research.md` documents the idea as tested and rejected (or
as a confirmation batch that showed the initial promising result was
noise, per research.md's own "Bench noise" section), do not re-run that
idea from scratch without a stated reason the situation changed.

## 3. Prefer a candidate that targets an observed weakness

```bash
.venv/bin/python evaluation/demand_bench.py \
  --agent submissions/<current-best>/main.py \
  --opponent submissions/<previous-or-reference>/main.py \
  --games 120
```

Confirms spec FR-008/SC-004: review the stratified output (and/or recent
`experiments/log.jsonl` hypotheses) for a specific losing pattern before
picking an unrelated idea to try next.

## 4. Screen the candidate with an initial batch

Apply the candidate change directly to `src/kaggriculture_agent/agent.py`'s
strategy module (`make evaluate` always evaluates that file — it has no
`AGENT=` override), then:

```bash
make evaluate SEASONS=20
```

(Or directly, to screen against one specific opponent rather than the
whole reference pool: `evaluation/run_batch.py --agent src/kaggriculture_agent/agent.py --opponents previous --seasons 20 --agent-version <candidate-label> --hypothesis "<what this targets>"`.)

Confirms spec FR-002: a win-rate/money result is produced before any
promotion decision. A clear loss here (per research.md's existing "20
seasons screens out clear losers" guidance) ends the investigation with
`decision: "reject"` — no confirmation batch needed for a clear loser.

## 5. Confirm a promising result at scale before promoting it

```bash
evaluation/run_batch.py --agent ... --opponents previous \
  --seasons 100 --agent-version <candidate-label> \
  --hypothesis "confirmation run for <candidate-label>"
```

Confirms spec FR-003/SC-001: only if the pooled result across the initial
and confirmation batches still favors the candidate does it get
`decision: "adopt"`. Re-run `make select` afterward — the new version
should now be the recommended current best, with no unconfirmed-sample
caution.

## 6. Regression-check against the full reference pool before finalizing

```bash
make evaluate SEASONS=40  # runs against random, starter, greedy, previous
```

Confirms spec FR-004/SC-002: the promoted candidate must not lose ground
against any reference opponent the previous current best already beat. Any
regression here MUST be explicitly and deliberately accepted (with a
recorded reason in the log entry's `hypothesis`) rather than silently
promoted anyway.

## Expected outcome

At the end of a round: either a new, confirmed current-best version exists
(steps 1-6 all pass, `make select` recommends it without a caution), or the
round ends with the existing current best unchanged and every attempted
idea recorded with a `reject`/`investigate` decision — both are valid,
successful outcomes of an investigation round (spec Edge Cases).
