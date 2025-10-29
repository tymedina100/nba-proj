# NBA Betting Projection Engine (minutes-first, explainable)

MVP: ingest -> priors -> simulate -> price edges. Focus on PTS/REB/AST with Gamma–Poisson posterior predictive and minutes-first logic.

## Quickstart
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .

# Run tracer-bullet (dummy data)
make etl DATE=2025-10-28
make simulate DATE=2025-10-28
# sample odds CSV is prefilled at data/parquet/odds_user/odds_2025-10-28.csv
make edges DATE=2025-10-28
make diag DATE=2025-10-28
make api
```
Artifacts land in `runs/YYYY-MM-DD/`.
