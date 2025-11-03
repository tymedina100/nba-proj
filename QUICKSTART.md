# Quickstart Guide

Get up and running with NBA-Proj in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- 2GB free disk space
- Internet connection

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tymedina100/nba-proj.git
cd nba-proj
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -e .
```

## First Run - Tracer Bullet Test

Test the full pipeline with sample data:

```bash
# 1. Extract and transform data
make etl DATE=2025-10-28

# 2. Run simulations
make simulate DATE=2025-10-28

# 3. Calculate betting edges
make edges DATE=2025-10-28

# 4. Generate diagnostics
make diag DATE=2025-10-28
```

### What Just Happened?

1. **ETL**: Downloaded NBA game data and player stats
2. **Simulate**: Generated 10,000 Monte Carlo simulations
3. **Edges**: Compared simulations against betting odds
4. **Diag**: Created diagnostic plots and metrics

### Check Your Output

Results are in `runs/2025-10-28/`:

```bash
ls runs/2025-10-28/

# You should see:
# - projections.parquet
# - simulations.parquet
# - edges.csv
# - diagnostics.html
# - plots/
```

## View Your Results

### Projections

```bash
python -c "
import pandas as pd
df = pd.read_parquet('runs/2025-10-28/projections.parquet')
print(df.head(10))
"
```

### Edges

```bash
python -c "
import pandas as pd
df = pd.read_csv('runs/2025-10-28/edges.csv')
print(df.sort_values('expected_value', ascending=False).head())
"
```

### Diagnostics

Open `runs/2025-10-28/diagnostics.html` in your browser.

## Using Real Data

### Step 1: Configure Data Source

Edit `config.yaml`:

```yaml
data:
  provider: "nba_stats"
  api_key: "${NBA_API_KEY}"
```

### Step 2: Set API Key

```bash
echo "NBA_API_KEY=your_key" > .env
# OR
export NBA_API_KEY=your_key
```

### Step 3: Add Your Odds Data

```bash
cat > data/parquet/odds_user/odds_2025-10-28.csv << EOF
player_id,player_name,stat,line,over_odds,under_odds,book
203999,Nikola Jokic,pts,27.5,-110,-110,draftkings
2544,LeBron James,pts,24.5,-115,-105,fanduel
EOF
```

### Step 4: Run Today's Pipeline

```bash
TODAY=$(date +%Y-%m-%d)

make etl DATE=$TODAY
make simulate DATE=$TODAY
make edges DATE=$TODAY
make diag DATE=$TODAY
```

## Start the API

```bash
make api
```

Test it:

```bash
curl http://localhost:8000/api/v1/health

curl "http://localhost:8000/api/v1/projections/203999?date=2025-10-28&stat=pts"

curl "http://localhost:8000/api/v1/edges?date=2025-10-28&min_ev=0.05"
```

## Common Workflows

### Daily Betting Workflow

```bash
#!/bin/bash
TODAY=$(date +%Y-%m-%d)

make etl DATE=$TODAY
make simulate DATE=$TODAY
make edges DATE=$TODAY

python -c "
import pandas as pd
edges = pd.read_csv('runs/${TODAY}/edges.csv')
print(edges[edges['expected_value'] > 0.08])
"
```

### Backtest Historical Performance

```bash
for i in {0..29}; do
  DATE=$(date -d "$i days ago" +%Y-%m-%d)
  make etl DATE=$DATE
  make simulate DATE=$DATE
done

make backtest START=2025-10-01 END=2025-10-30
```

### Custom Simulation

```python
from nba_proj import Simulator
from nba_proj.config import load_config

config = load_config()
sim = Simulator(config)

results = sim.simulate_player(
    player_id="203999",
    date="2025-10-28",
    n_sims=50000,
    adjustments={
        "minutes_modifier": 1.1,
        "pace_modifier": 1.05,
    }
)

print(f"Mean: {results['mean']:.1f}")
print(f"P(>27.5): {results['prob_over_27_5']:.3f}")
```

## Troubleshooting

### Installation Issues

```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

### Data Download Fails

```bash
# Check API key
echo $NBA_API_KEY

# Verify connection
ping stats.nba.com
```

### No Edges Found

```bash
# Check odds data exists
cat data/parquet/odds_user/odds_YYYY-MM-DD.csv

# Lower threshold in config.yaml
# edges.min_expected_value: 0.01
```

### Simulations Too Slow

```yaml
# In config.yaml
simulation:
  n_simulations: 5000

performance:
  parallel: true
  n_workers: 8
```

## Next Steps

1. Read the [Methodology](docs/METHODOLOGY.md)
2. Explore [Configuration](docs/CONFIGURATION.md)
3. Check [API Documentation](docs/API.md)
4. Review [Contributing Guide](CONTRIBUTING.md)

## Getting Help

- Documentation in `docs/`
- Examples in `examples/`
- [GitHub Issues](https://github.com/tymedina100/nba-proj/issues)

## Commands Reference

```bash
make etl DATE=YYYY-MM-DD
make simulate DATE=YYYY-MM-DD
make edges DATE=YYYY-MM-DD
make diag DATE=YYYY-MM-DD
make api

make test
make lint
make clean
make help
```

Happy projecting! 🏀📊