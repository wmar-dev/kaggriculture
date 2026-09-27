# Phase 0 Research: Improve Agent Beyond v18 Baseline

No `[NEEDS CLARIFICATION]` markers were left in the Technical Context —
every decision below was resolvable from this project's own prior work
(constitution Principle VI). Each entry follows Decision / Rationale /
Alternatives considered.

## R1: What "current best" means mechanically

**Decision**: "Current best" (spec's Current Best Version entity) is the
top-ranked, submittable candidate returned by
`evaluation/select_final.py`'s `rank_candidates()` — the same tool already
used for final-submission selection (spec 001 User Story 3). In today's
history this also happens to be the highest-numbered `submissions/vN/`
directory, which is what `run_batch.py`'s `"previous"` opponent alias
resolves to (`_latest_submission_path()`); that equivalence is convention,
not a coincidence to rely on blindly — it holds only because every adopted
version so far has also gotten the next sequential version number in
order. If a future promotion is ever adopted out of numeric order (e.g., a
fix is adopted as `v18b` rather than `v19`), `"previous"` and
`select_final.py`'s top rank would diverge; this MUST be treated as a bug
in versioning discipline to fix immediately, not as two legitimately
different "current best" concepts.

**Rationale**: Building a second, separate "current best" pointer (a file,
a config value) would duplicate logic `select_final.py` already implements
correctly (including the real-leaderboard-vs-local tiebreak logic
documented in its own docstring) — a violation of Time-Boxed Simplicity for
no added trustworthiness.

**Alternatives considered**: A dedicated `CURRENT_BEST` marker file,
updated on every promotion. Rejected: it is a second source of truth that
can drift from what the log actually supports, exactly the class of bug
`select_final.py`'s own docstring already warns about (the v7-dev/v7
tiebreak-noise incident).

## R2: How to mechanically enforce the confirmation-batch requirement (FR-003)

**Decision**: Extend `evaluation/select_final.py`'s existing
`rank_candidates()`/`format_recommendation()` path with one additive
check on the **head-to-head (self-play) result**, not the fixed-reference
bench. Re-reading `select_final.py` closely: once every candidate already
beats the fixed reference opponents (random/starter/greedy) at or near
100% — which is the normal, saturated state by this point in the project —
`_reference_win_rate` stops discriminating and the ranking actually
resolves on `_earned_promotion`/`_self_play_win_rate`: a binary "did it
beat the version it was built to replace, head-to-head" signal. That
head-to-head number is exactly the quantity that flipped from 65% to 53%
in research.md's own "Bench noise" finding. So the caution is: when the
top-ranked candidate has **no self-play evaluation result at all**, or its
pooled self-play season count is below the confirmation threshold, print a
caution line rather than silently recommending it. Use **100 seasons** as
the threshold, taken directly from that same "Bench noise" finding in
`specs/001-win-kaggriculture/research.md` (a 65% edge over 20 seasons fell
to 53%, indistinguishable from a coin flip, pooled over 120 seasons;
guidance there already states "a true 55-60% edge needs roughly 100+
seasons to separate from 50%"). The "no self-play result at all" case is
worth flagging in its own right: `_earned_promotion` currently defaults to
`1` (treated as having earned its promotion) when `_self_play_win_rate` is
`None`, so a candidate tested only against the weak fixed bench and never
head-to-head against the version it would replace can otherwise rank #1
without ever having been directly compared to it.

**Rationale**: This is the cheapest possible enforcement — no new script,
no new log field, reuses the pooling `_merge_results()` already computes.
It cannot block adoption (that stays a human/agent judgment call per
Principle VI), but it makes the unconfirmed case visible instead of silent,
which is the actual failure mode observed historically (a promising
20-season result being trusted without anyone re-running it larger).

**Alternatives considered**: (a) A hard gate that refuses to rank an
under-sampled candidate first at all — rejected, because a large true
effect is sometimes obvious well under 100 seasons (v13 vs v12: 93% at 60
seasons) and a hard-coded seasons floor would be a worse proxy for
confidence than a human glancing at the caution and the actual win-rate.
(b) A statistical significance test (e.g., a binomial/two-proportion test)
instead of a fixed season count — rejected for this round as unnecessary
complexity (Principle V): the fixed-threshold heuristic already matches
this project's own documented empirical finding and is far simpler to
implement, read, and trust than introducing a hypothesis-testing dependency
for one caution line.

## R3: How to mechanically enforce "don't re-test rejected ideas" (FR-005)

**Decision**: No new tool. Document a one-line workflow step in
`quickstart.md`: before starting a new evaluation batch, search
`experiments/log.jsonl` for the candidate's keywords in the `hypothesis`
field (e.g. `grep -i "<keyword>" experiments/log.jsonl | jq '{agent_version, hypothesis, decision}'`)
and read any matching prior entry's `decision` before proceeding.

**Rationale**: `experiments/log.jsonl` is already line-delimited JSON
specifically so it is greppable/`jq`-able without tooling
(`specs/001-win-kaggriculture/data-model.md`'s ExperimentLogEntry is one
object per line by design). Building a dedicated lookup script for a
one-line `grep`/`jq` command would be complexity with no capability gain —
against Principle V.

**Alternatives considered**: A `evaluation/check_prior.py <keyword>` search
script. Rejected as unneeded ceremony for what a documented shell one-liner
already does exactly as reliably.

## R4: How to mechanically enforce "target observed weaknesses first" (FR-008)

**Decision**: No new tool. `evaluation/demand_bench.py` already exists for
exactly this purpose — it stratifies head-to-head results by the town's
shop-demand draw specifically because plain self-play win rate was shown to
hide a change that fixes one regime while breaking another (its own
docstring, and the "PLOT_WORKERS re-sweep: 4 workers' weak-town edge was
noise" / "neutral care-gating and hand-slack tests against v18" recent
history are exactly this workflow already in use). This feature's
contribution is procedural, not technical: before proposing a new candidate
change, first check whether `demand_bench.py` (or the existing experiment
log) already points at a specific losing pattern for the current best
version, and prefer investigating that over undirected exploration.

**Rationale**: The tool already does the hard part (splitting results by
the condition that actually predicts the outcome). No gap exists here to
close with new code.

**Alternatives considered**: A dedicated "weakness tracker" document.
Rejected: `experiments/log.jsonl` entries already carry enough hypothesis
text to serve this role, and a second document would be one more place to
keep in sync (risking the exact "two sources of truth" problem R1 avoided).

## R5: Where confirmation-batch and prior-lookup guidance is recorded for future use

**Decision**: `quickstart.md` (this feature) is the single place a
competitor/agent re-reads before starting a new round of candidate
evaluation; it links to, rather than duplicates, the underlying data
(`specs/001-win-kaggriculture/research.md`'s "Bench noise" section, and
`experiments/log.jsonl` itself).

**Rationale**: Matches this project's existing pattern (`quickstart.md` as
a runbook, `research.md` as the evidence/decision record) rather than
inventing a new artifact type.

**Alternatives considered**: Folding this guidance into the `Makefile`
comments only. Rejected as insufficient on its own — the `Makefile`
already carries a related comment (the `SEASONS` default rationale) but a
plan-level quickstart is needed to also cover the prior-lookup and
weakness-first steps, which have no natural home in a `Makefile` comment.
