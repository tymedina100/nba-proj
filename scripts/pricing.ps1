param([string]$Date)
param([string]$OddsPath = "data\parquet\odds_user\odds_$Date.csv")
python -m src.core.pricing --odds $OddsPath --date $Date
