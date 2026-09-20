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

Common commands are also wrapped in the `Makefile`:

```bash
make install     # create .venv and install the project + dev deps
make test        # run the test suite
make evaluate    # local batch evaluation vs. the reference opponent pool
make bundle      # bundle src/kaggriculture_agent/ into the next submissions/vN/main.py
make select      # show the best-evidenced candidate from experiments/log.jsonl
make submit      # review + confirm, then submit the recommended (or VERSION=vN) bundle to Kaggle
make status      # check submission status
make leaderboard # check the leaderboard
```

`make submit` is the one command that actually spends a Kaggle submission —
it shows you what it's about to do and asks for confirmation first.

## Layout

- `src/kaggriculture_agent/` — the agent (`agent.py` is the Kaggle
  submission entry point)
- `evaluation/` — local batch-evaluation harness, reference opponents,
  submission bundler, final-selection tool (dev tooling, not submitted)
- `tests/` — unit and integration tests
- `experiments/log.jsonl` — append-only log of every evaluated/submitted
  agent version
- `submissions/vN/main.py` — frozen, submittable bundles
