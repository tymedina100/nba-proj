# NBA Statistical Simulation & Edge Finder

A statistical simulation pipeline for NBA player performance that uses Bayesian methods (Gamma-Poisson posterior predictive) with minutes-first logic to identify betting edges.

## Overview

This project implements an end-to-end pipeline that:
1. **Ingests** NBA player statistics and game data
2. **Calculates priors** using historical performance
3. **Simulates** player performance using Bayesian posterior predictive distributions
4. **Prices edges** by comparing simulations against market odds

The focus is on core counting stats: **Points (PTS)**, **Rebounds (REB)**, and **Assists (AST)**.

## Features

- **Bayesian Simulation**: Gamma-Poisson conjugate prior for robust player performance modeling
- **Minutes-First Logic**: Incorporates playing time as a critical factor in projections
- **Edge Detection**: Identifies positive expected value betting opportunities
- **Modular Pipeline**: Clean separation of ETL, modeling, and analysis stages
- **Date-Based Workflows**: Reproducible runs organized by date
- **API Interface**: Serve predictions and analysis via REST API

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/tymedina100/nba-proj.git
cd nba-proj

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .[dev]
```

### Running the Pipeline

The project uses a Makefile for easy workflow execution:

```bash
# 1. Run ETL (Extract, Transform, Load)
make etl DATE=2025-10-28

# 2. Run simulation
make simulate DATE=2025-10-28

# 3. Calculate edges (requires odds data in data/parquet/odds_user/odds_YYYY-MM-DD.csv)
make edges DATE=2025-10-28

# 4. Generate diagnostics
make diag DATE=2025-10-28

# 5. Start API server
make api
```

### Tracer Bullet Test

Run the complete pipeline with dummy data to verify installation:

```bash
make etl DATE=2025-10-28
make simulate DATE=2025-10-28
make edges DATE=2025-10-28
make diag DATE=2025-10-28
```

A sample odds CSV is pre-filled at `data/parquet/odds_user/odds_2025-10-28.csv`.

## Project Structure

```
nba-proj/
├── data/
│   └── parquet/
│       └── odds_user/          # User-provided odds data
├── runs/
│   └── YYYY-MM-DD/             # Date-organized output artifacts
├── src/
│   └── nba_proj/               # Main package
├── Makefile                     # Pipeline commands
├── README.md
└── setup.py
```

## Workflow

### 1. ETL Stage
Ingests and preprocesses NBA data:
- Player game logs
- Team schedules
- Injury reports
- Historical statistics

### 2. Prior Calculation
Computes Bayesian priors for each player:
- Historical performance distributions
- Trend adjustments
- Home/away splits
- Matchup factors

### 3. Simulation
Runs Monte Carlo simulations using Gamma-Poisson posterior predictive:
- Minutes-adjusted projections
- Distribution over possible outcomes
- Confidence intervals

### 4. Edge Pricing
Compares simulations against market odds:
- Identifies positive EV opportunities
- Calculates Kelly criterion bet sizes
- Risk-adjusted recommendations

### 5. Diagnostics
Generates analysis artifacts:
- Calibration plots
- Backtesting results
- Performance metrics

## Output

All artifacts land in `runs/YYYY-MM-DD/`:
- Simulation results (distributions, quantiles)
- Edge analysis (recommended bets, EV calculations)
- Diagnostic plots and metrics
- Logs and metadata

## API Usage

Start the API server:

```bash
make api
```

The API provides endpoints for:
- Retrieving player projections
- Querying identified edges
- Accessing historical performance
- Running custom simulations

See [API.md](docs/API.md) for detailed endpoint documentation.

## Methodology

### Gamma-Poisson Model

The project uses a conjugate Gamma-Poisson model for count statistics:

- **Prior**: Gamma distribution based on historical rates
- **Likelihood**: Poisson distribution for in-game outcomes
- **Posterior Predictive**: Negative Binomial distribution

This approach naturally handles:
- Overdispersion in player performance
- Regression to the mean
- Uncertainty quantification

### Minutes-First Logic

Playing time is incorporated as a primary factor:
1. Predict minutes distribution
2. Calculate per-minute rates
3. Convolve distributions for final projections

This avoids biases from lineup changes and coaching decisions.

## Configuration

Configure data sources, model parameters, and output options in `config.yaml` (see [Configuration Guide](docs/CONFIGURATION.md)).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Code style
- Testing requirements
- Pull request process
- Development setup

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src/nba_proj
```

## License

[MIT License](LICENSE)

## Acknowledgments

- NBA data sourced from [data provider]
- Statistical methods based on Bayesian hierarchical models
- Inspired by modern sports analytics literature

## Support

For questions or issues:
- Open a [GitHub Issue](https://github.com/tymedina100/nba-proj/issues)
- Check [documentation](docs/)
- Review [FAQ](docs/FAQ.md)

## Roadmap

- [ ] Additional player props (3PM, STL, BLK, TO)
- [ ] Live in-game updates
- [ ] Multi-sport expansion
- [ ] Web dashboard
- [ ] Automated bet placement (for supported books)

---

**Disclaimer**: This tool is for research and educational purposes. Sports betting involves risk. Always gamble responsibly and within your means.