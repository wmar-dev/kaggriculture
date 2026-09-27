# Phase 1 Data Model: Improve Agent Beyond v18 Baseline

This feature does not change the wire format or the core
`ExperimentLogEntry` schema defined in
`specs/001-win-kaggriculture/data-model.md` — it clarifies how existing
fields are used and adds two conceptual (non-schema) entities from the
spec's Key Entities section.

## ExperimentLogEntry — clarified conventions (no schema change)

Reusing `specs/001-win-kaggriculture/data-model.md`'s
`{timestamp, agent_version, commit_sha, hypothesis, evaluation_results,
kaggle_result, decision}` shape as-is. This feature adds two conventions
for *how* entries are written, not new fields:

| Convention | Rule |
| --- | --- |
| Confirmation entries | When an initial small-sample batch (`decision: "investigate"`) looks promising, the follow-up larger-sample batch for the same candidate MUST reuse the same `agent_version` label (or a clearly-linked one, e.g. `<version>-confirm`, matching the existing `v18-unified-v3-confirm` pattern already in `experiments/log.jsonl`) so `select_final.py`'s per-version pooling (`_merge_results`) correctly combines them into one confidence-weighted total. |
| Promotion marker | `decision: "adopt"` on an entry for a version whose `evaluation_results` (pooled across all its log entries) reach the confirmation threshold (research.md R2, 100 seasons) against the deciding opponent is what "promoted to current best" means (spec FR-007) — no separate promotion record is introduced. `evaluation/select_final.py --mark-final` remains reserved for the distinct, later act of choosing the final Kaggle submission (spec 001 User Story 3), not for this round's internal promotions. |

## Current Best Version *(spec Key Entity — computed, not stored)*

Not a new stored entity. Defined operationally (research.md R1) as: the
top entry returned by `evaluation/select_final.py`'s `rank_candidates()`
among versions with an existing `submissions/<version>/main.py` bundle.
Consumers (a competitor, or this agent in a future session) always
re-derive it by running `make select` / `evaluation/select_final.py`
rather than reading a cached pointer.

## Candidate Change *(spec Key Entity — computed, not stored)*

Not a new stored entity. Represented as the set of `experiments/log.jsonl`
entries sharing one `agent_version` label: an initial entry
(`decision: "investigate"`) and, for promising results, one or more
confirmation entries per the convention above, ending in a final
`decision` of `"adopt"` or `"reject"`.

## Weakness *(spec Key Entity — computed, not stored)*

Not a new stored entity. Represented as either (a) a stratified result from
`evaluation/demand_bench.py` showing a specific losing regime (e.g., "weak
town demand: 1W/7L"), or (b) a specific losing/near-losing pattern already
described in an `experiments/log.jsonl` `hypothesis` string or in
`specs/001-win-kaggriculture/research.md`. No new storage: a weakness is a
finding to cite, not a record to maintain separately (research.md R4).

## select_final.py — one additive check (implementation detail, not schema)

`rank_candidates()`'s top result gains one derived, computed-on-read value:
whether its pooled **self-play (head-to-head)** season count — the
`evaluation_results` entries whose `opponent` is path-shaped, the same set
`_self_play_win_rate()` already isolates — is ≥ 100 (research.md R2), or
whether no such result exists at all. This is a presentation-layer caution
in `format_recommendation()`'s output, not a stored field — re-running the
tool always recomputes it from the current log contents. It is deliberately
about self-play, not the fixed-reference-opponent pool: once the fixed
bench (random/starter/greedy) is saturated at ~100%, it is the head-to-head
result against the version being replaced that actually decides the
ranking (`_earned_promotion`), and that is exactly where research.md's
"Bench noise" finding showed a result flip.
