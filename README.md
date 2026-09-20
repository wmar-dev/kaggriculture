# Kaggriculture Agent

An agent for the [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture)
Kaggle Simulations competition (see [CONTEST.md](CONTEST.md) for the game
rules).

Built with [Spec Kit](https://github.com/github/spec-kit); the full spec,
plan, research, and task history live under
[specs/001-win-kaggriculture/](specs/001-win-kaggriculture/).

## Quickstart

See [specs/001-win-kaggriculture/quickstart.md](specs/001-win-kaggriculture/quickstart.md)
for how to set up the environment, run the agent, run the test suite, run
local batch evaluation, and bundle a submission.

## Layout

- `src/kaggriculture_agent/` — the agent (`agent.py` is the Kaggle
  submission entry point)
- `evaluation/` — local batch-evaluation harness, reference opponents,
  submission bundler, final-selection tool (dev tooling, not submitted)
- `tests/` — unit and integration tests
- `experiments/log.jsonl` — append-only log of every evaluated/submitted
  agent version
- `submissions/vN/main.py` — frozen, submittable bundles
