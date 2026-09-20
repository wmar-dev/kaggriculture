# Quickstart: Validate the Kaggriculture Agent Locally

Proves the feature works end-to-end without touching Kaggle or spending
submission budget. See `contracts/agent-interface.md` for the interface
being validated and `data-model.md` for the shapes involved.

## Prerequisites

- Python 3.11
- `pip install kaggle_environments pytest numpy`
- Repository checked out on branch `001-win-kaggriculture`

## 1. Run a single episode and render it

Proves the agent implements the required interface and survives a full
season against a reference opponent (contract test 1).

```bash
python -c "
from kaggle_environments import make
from src.kaggriculture_agent.agent import agent as my_agent

env = make('kaggriculture', configuration={'episodeSteps': 720})
env.run([my_agent, 'random'])
print('Final money:', [f['money'] for f in env.state[-1].observation.farms])
"
```

**Expected outcome**: completes without an exception; prints two final
money values (one per player); no illegal-action or timeout errors in
`env.toJSON()['statuses']`.

## 2. Run the unit/contract test suite

```bash
pytest tests/unit tests/integration -q
```

**Expected outcome**: all tests pass, including the full-episode smoke
test and the "never-empty response" / "bounded market orders" contract
tests from `contracts/agent-interface.md`.

## 3. Run local batch evaluation (the trustworthy validation signal)

Proves FR-002/SC-002: a local result exists before any submission is
spent, against the opponent pool defined in `research.md` R3.

```bash
python evaluation/run_batch.py \
  --agent src/kaggriculture_agent/agent.py \
  --opponents random greedy previous \
  --seasons 50
```

**Expected outcome**: a report of win/loss/tie counts and average
end-of-season money per opponent, and a new line appended to
`experiments/log.jsonl` recording the run (FR-003).

## 4. Bundle a submittable file

Proves the single-file packaging approach from `research.md` R2.

```bash
python evaluation/bundle_submission.py --out submissions/<version>/agent.py
python -c "import ast; ast.parse(open('submissions/<version>/agent.py').read())"
```

**Expected outcome**: a single `agent.py` with no local imports that
parses cleanly and, re-run through step 1 in place of the package import,
behaves identically to the unbundled agent.

## 5. Submit (human-approved step only — not automated)

Per spec FR-010, this step always requires the competitor's own review
and action; it is intentionally not scripted end-to-end here. Once
`submissions/<version>/agent.py` has passed steps 1–4 and shown a
favorable result in step 3, the competitor reviews it and uploads it to
the competition themselves (or explicitly approves an upload).
