<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first concrete version, replacing placeholder template)
- Added sections:
  - Core Principles: I. Leaderboard-Driven Iteration, II. Trustworthy Validation
    (NON-NEGOTIABLE), III. Full Reproducibility, IV. Rules & Legal Compliance
    (NON-NEGOTIABLE), V. Time-Boxed Simplicity
  - Competition Constraints
  - Workflow & Submission Discipline
  - Governance
- Removed sections: none (template placeholders replaced with concrete content)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (generic "Constitution Check" gate reads
    this file directly; no hardcoded principle names to change)
  - ✅ .specify/templates/spec-template.md (no constitution-specific references)
  - ✅ .specify/templates/tasks-template.md (no constitution-specific references)
  - ✅ .claude/skills/speckit-*/SKILL.md (generic references only, no changes needed)
- Follow-up TODOs:
  - TODO(COMPETITION_NAME): confirm exact Kaggle competition title/URL once entered
  - TODO(COMPETITION_DEADLINE): confirm submission deadline
  - TODO(COMPETITION_METRIC): confirm official leaderboard evaluation metric
-->

# Kaggriculture Contest Constitution

## Core Principles

### I. Leaderboard-Driven Iteration

Every technical decision MUST be justified by its expected effect on the
competition's official evaluation metric. Prioritize experiments by expected
score improvement per unit of effort/compute, not by novelty or personal
interest. Maintain a running experiment log (config, CV score, public
leaderboard score if submitted, wall-clock/compute cost) so the highest-value
next step is always visible.

**Rationale**: The sole objective is winning the contest; effort spent on
work that does not plausibly move the leaderboard score is waste.

### II. Trustworthy Validation (NON-NEGOTIABLE)

A local cross-validation scheme that correlates with the competition metric
and leaderboard MUST be established before any modeling work is trusted.
Every submission MUST be justified by CV score, not public leaderboard score
alone. Any divergence between CV and public leaderboard MUST be investigated
before further tuning continues. Data leakage (target leakage, temporal
leakage, group leakage across folds) is treated as a critical bug.

**Rationale**: Optimizing against an untrustworthy or leaked validation
signal produces models that look good locally but lose on the final
leaderboard — the single most common way competitions are lost.

### III. Full Reproducibility

Every submission MUST be traceable to the exact code commit, data version,
configuration, and random seed(s) that produced it. Notebooks/scripts MUST
run end-to-end from raw data to submission file without undocumented manual
steps. No submission is made from uncommitted or untracked code.

**Rationale**: Winning entries must be defensible and reproducible for
competition verification, and reproducibility is also what lets past
experiments be trusted and reused rather than re-run from guesswork.

### IV. Rules & Legal Compliance (NON-NEGOTIABLE)

All work MUST comply with the competition's official rules, terms of
service, data licensing terms, and applicable law. Explicitly prohibited at
all times:

- Using data, code, or pretrained models excluded or disallowed by the
  competition rules.
- Multiple accounts, team-size violations, or any form of leaderboard
  manipulation.
- Sharing or soliciting private information about the answer/test set
  outside sanctioned competition forums.
- Plagiarizing other participants' code/writeups without required
  attribution where reuse is permitted.
- Any action that violates the law (e.g., unauthorized access to systems,
  scraping in violation of a site's terms, IP infringement).

Every legal, rules-compliant technique — including permitted external data,
public leaked-but-rules-sanctioned resources, ensembling, pseudo-labeling,
and aggressive but honest hyperparameter/architecture search — is in scope.
"Any legal means possible" describes the ceiling of aggressiveness allowed,
not permission to skip this principle.

**Rationale**: A win obtained by breaking rules or law is void, reputationally
costly, and not actually a win; this project optimizes hardest within a
strictly legal and rules-compliant envelope.

### V. Time-Boxed Simplicity

Prefer the simplest approach that can plausibly reach a competitive score
before reaching for complexity (exotic architectures, elaborate pipelines,
large ensembles). Escalate complexity only when a simpler baseline has been
tried and its ceiling understood. All work MUST be time-boxed against the
competition deadline; effort estimates and remaining time budget MUST be
reviewed before starting any multi-day experiment.

**Rationale**: Competitions have hard deadlines; unbounded complexity or
open-ended exploration is the main way a promising approach fails to ship a
final submission in time.

## Competition Constraints

- Competition identity, deadline, and official metric: TODO(COMPETITION_NAME),
  TODO(COMPETITION_DEADLINE), TODO(COMPETITION_METRIC) — MUST be filled in
  and kept current as soon as the specific Kaggle competition is confirmed.
- External data/models are permitted only when the competition rules
  explicitly allow them; when in doubt, the more restrictive reading of the
  rules applies until clarified.
- Submission budget (daily/total submission caps set by the competition)
  MUST be tracked and spent deliberately — reserve late submissions for
  validated improvements, not speculative probing.

## Workflow & Submission Discipline

- Baseline first: establish a simple, fully reproducible end-to-end
  pipeline and submission before optimizing any component.
- Every experiment is logged with its hypothesis, result, and decision
  (adopt/reject/investigate further).
- Final submission selection MUST be made deliberately (e.g., best-CV and a
  hedged second choice), not left to whichever run happened to run last.
- Code and experiment logs are committed regularly; uncommitted work is not
  considered part of the project's trusted state.

## Governance

This constitution supersedes ad-hoc practice for this project. All specs,
plans, and task lists MUST be checked against these principles (see
Constitution Check in the plan template); any violation MUST be justified in
writing or the approach revised.

**Amendment procedure**: Propose the change (what and why), update this
file via `/speckit-constitution` (or direct edit), bump the version per the
policy below, and update the Sync Impact Report at the top of this file.

**Versioning policy** (semantic versioning for this document):

- MAJOR: Backward-incompatible governance changes or removal/redefinition
  of a principle.
- MINOR: A new principle or materially expanded guidance is added.
- PATCH: Clarifications, wording, or non-semantic refinements.

**Compliance review**: Before `/speckit-plan` and before any submission,
confirm the work is consistent with Principles II and IV in particular
(validation trustworthiness and rules/legal compliance); these are
non-negotiable regardless of time pressure.

**Version**: 1.0.0 | **Ratified**: 2026-09-19 | **Last Amended**: 2026-09-19
