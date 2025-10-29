.PHONY: etl simulate edges diag api test

DATE ?= $(shell date +%Y-%m-%d)

etl:
	python -m src.etl.ingest_boxscores --date $(DATE)
	python -m src.core.priors --update --date $(DATE)

simulate:
	python -m src.core.simulator --date $(DATE)

# Accept CSV for MVP (path override via ODDS)
ODDS ?= data/parquet/odds_user/odds_$(DATE).csv
edges:
	python -m src.core.pricing --odds $(ODDS) --date $(DATE)

diag:
	python -m src.core.evals --date $(DATE)

api:
	uvicorn src.api.main:app --reload --port 8000

test:
	pytest -q
