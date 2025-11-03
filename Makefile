# ===== NBA-PROJ Makefile =====
# Usage:
#   make etl DATE=2025-10-28
#   make simulate DATE=2025-10-28
#   make edges DATE=2025-10-28
#   make diag DATE=2025-10-28
#   make api

# Variables
DATE ?=
DRAWS ?= 25000
ODDS_FILE ?= data/parquet/odds_user/odds_$(DATE).csv
PORT ?= 8000

.PHONY: etl priors simulate edges diag api test fmt help

## Ingest & cache inputs for the date
etl:
	@if [ -z "$(DATE)" ]; then echo "ERROR: pass DATE=YYYY-MM-DD"; exit 1; fi
	python -m src.etl.fetch_daily --date $(DATE) --provider bref_boxscores

## Update minutes-first priors
priors:
	@if [ -z "$(DATE)" ]; then echo "ERROR: pass DATE=YYYY-MM-DD"; exit 1; fi
	python -m src.core.priors --date $(DATE) --update

## Run posterior simulation
simulate:
	@if [ -z "$(DATE)" ]; then echo "ERROR: pass DATE=YYYY-MM-DD"; exit 1; fi
	python -m src.core.simulator --date $(DATE) --draws $(DRAWS)

## Price edges from user odds CSV
edges:
	@if [ -z "$(DATE)" ]; then echo "ERROR: pass DATE=YYYY-MM-DD"; exit 1; fi
	@if [ ! -f "$(ODDS_FILE)" ]; then echo "ERROR: missing $(ODDS_FILE)"; exit 1; fi
	python -m src.core.pricing --date $(DATE) --odds $(ODDS_FILE)

## Diagnostics (requires outcomes and edges)
diag:
	@if [ -z "$(DATE)" ]; then echo "ERROR: pass DATE=YYYY-MM-DD"; exit 1; fi
	python -m src.metrics.calibration_bins --date $(DATE) \
	  --outcomes data/outcomes/$(DATE).csv \
	  --edges runs/$(DATE)/edges.csv \
	  --bins 10

## Run local API
api:
	uvicorn src.api.app:app --reload --port $(PORT)

## Tests & formatting
test:
	pytest -q

fmt:
	ruff check --fix .
	isort .
	black .

## Show this help
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' Makefile | awk -F':|##' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$3}'
