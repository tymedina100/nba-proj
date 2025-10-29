param([string]$Date)
python -m src.etl.ingest_boxscores --date $Date
