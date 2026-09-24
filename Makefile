.PHONY: install test evaluate bundle select submit status leaderboard clean

VENV    := .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
KAGGLE  := $(VENV)/bin/kaggle

# 20 seasons screens out clear losers, but is NOT enough to adopt a
# marginal winner: a hiring change measured 65% over 20 seasons and 53%
# over 120 (see research.md, "Bench noise"). Use SEASONS=100+ before
# adopting anything that measures under ~70%.
SEASONS ?= 20

# Kaggle allows 5 submissions per day for this competition (spec FR-004
# requires tracking this). The counter below matches submissions by UTC
# date, since Kaggle's day boundary is UTC, not local time. Unused slots
# do not carry over.
DAILY_SUBMISSION_CAP ?= 5
RECOMMENDED := $(shell $(PY) evaluation/select_final.py 2>/dev/null | sed -n 's/^Recommended final: \([^ ]*\).*/\1/p')
VERSION ?= $(RECOMMENDED)
MSG     ?= $(VERSION) -- see experiments/log.jsonl for evaluation results

## Set up the venv and install the project (incl. dev/test deps).
install:
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -e ".[dev]"

## Run the unit + integration test suite.
test:
	$(PY) -m pytest tests/ -q

## Locally evaluate the current agent vs. the reference opponent pool.
## Override seasons with: make evaluate SEASONS=50
evaluate:
	$(PY) evaluation/run_batch.py \
		--agent src/kaggriculture_agent/agent.py \
		--opponents random starter greedy previous \
		--seasons $(SEASONS)

## Bundle src/kaggriculture_agent/ into the next submissions/vN/main.py.
bundle:
	$(PY) evaluation/bundle_submission.py

## Show the best-evidenced candidate from experiments/log.jsonl.
select:
	$(PY) evaluation/select_final.py

## Submit a bundle to Kaggle -- the one irreversible, human-approved step.
## Defaults to whatever `select` currently recommends; override with:
##   make submit VERSION=v2 MSG="short description"
submit:
	@if [ -z "$(VERSION)" ]; then \
		echo "No evaluated version found -- run 'make evaluate' and 'make bundle' first, or pass VERSION=vN."; \
		exit 1; \
	fi
	@if [ ! -f submissions/$(VERSION)/main.py ]; then \
		echo "submissions/$(VERSION)/main.py not found."; \
		exit 1; \
	fi
	@$(PIP) show kaggle >/dev/null 2>&1 || $(PIP) install --quiet kaggle
	@echo "About to submit: submissions/$(VERSION)/main.py"
	@echo "Message: $(MSG)"
	@used=$$($(KAGGLE) competitions submissions kaggriculture 2>/dev/null | grep -c "$$(date -u +%Y-%m-%d)" || true); \
		left=$$(( $(DAILY_SUBMISSION_CAP) - $$used )); \
		echo "Daily budget: $$used/$(DAILY_SUBMISSION_CAP) used today (UTC), $$left remaining"; \
		if [ "$$used" -ge "$(DAILY_SUBMISSION_CAP)" ]; then \
			echo "  WARNING: daily cap appears to be reached -- Kaggle will likely reject this."; \
		elif [ "$$left" -le 1 ]; then \
			echo "  NOTE: this is your last submission today. Unused slots do not carry over."; \
		fi
	@read -p "Submit to Kaggle now? [y/N] " ans; \
		case "$$ans" in [yY]) ;; *) echo "Aborted."; exit 1;; esac
	$(KAGGLE) competitions submit kaggriculture -f submissions/$(VERSION)/main.py -m "$(MSG)"

## Check submission status.
status:
	$(KAGGLE) competitions submissions kaggriculture

## Check the leaderboard.
leaderboard:
	$(KAGGLE) competitions leaderboard kaggriculture -s

## Remove Python caches.
clean:
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .pytest_cache
