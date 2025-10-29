param([string]$Date)
python -m src.etl.ingest_boxscores --date $Date
python -m src.core.priors --update --date $Date
python -m src.core.simulator --date $Date
python -m src.core.pricing --odds data\parquet\odds_user\odds_$Date.csv --date $Date
python -m src.core.evals --date $Date
