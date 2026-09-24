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

### Submission budget

Kaggle allows **5 submissions per day** for this competition, and unused
slots do not carry over. `make submit` reports how many you've used
before asking for confirmation (spec FR-004 requires tracking this).

The day boundary is **UTC, not local time** — which is easy to get
wrong: on a local evening the UTC day may already have rolled over, so
submissions that feel like "today" are counted against yesterday's
budget and you have more left than you think. The counter in
`make submit` uses UTC for this reason.

## Layout

- `src/kaggriculture_agent/` — the agent (`agent.py` is the Kaggle
  submission entry point)
- `evaluation/` — local batch-evaluation harness, reference opponents,
  submission bundler, final-selection tool (dev tooling, not submitted)
- `tests/` — unit and integration tests
- `experiments/log.jsonl` — append-only log of every evaluated/submitted
  agent version
- `submissions/vN/main.py` — frozen, submittable bundles
- `training/` — experimental: RL (PPO) training for the farmer's
  tile-tending policy specifically, holding the rest of the proven
  heuristic (crop choice, market orders, animal husbandry) fixed. See
  `specs/001-win-kaggriculture/research.md`'s RL section for the scoping
  rationale and results; `training/env.py`'s docstring for what is and
  isn't RL-controlled. Not part of the submitted agent unless/until a
  trained policy is shown to beat it.
