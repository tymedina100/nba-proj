# Configuration Guide

This guide explains how to configure NBA-Proj for your specific needs.

## Configuration File

The main configuration is stored in `config.yaml` at the project root.

## Example Configuration

```yaml
# Data Sources
data:
  provider: "nba_stats"  # Data provider (nba_stats, balldontlie, custom)
  cache_dir: "data/cache"
  parquet_dir: "data/parquet"
  update_frequency: "daily"  # How often to refresh data
  
  # API credentials (if required)
  api_key: "${NBA_API_KEY}"  # Use environment variable
  
  # Historical data settings
  lookback_days: 180  # Days of history to use for priors
  min_games_threshold: 10  # Minimum games for reliable estimates

# Simulation Parameters
simulation:
  n_simulations: 10000  # Number of Monte Carlo simulations
  random_seed: 42  # For reproducibility
  
  # Bayesian model settings
  model:
    type: "gamma_poisson"
    
    # Prior parameters
    prior:
      pts:
        shape_prior_weight: 0.3  # Weight given to league-wide prior
        recency_decay: 0.95  # Exponential decay for older games
      reb:
        shape_prior_weight: 0.3
        recency_decay: 0.95
      ast:
        shape_prior_weight: 0.3
        recency_decay: 0.95
    
    # Minutes modeling
    minutes:
      method: "gaussian"  # gaussian, empirical, or fixed
      injury_adjustment: true
      blowout_adjustment: true
      back_to_back_penalty: 0.92
  
  # Adjustments
  adjustments:
    home_court_advantage: 1.05
    pace_normalization: true
    matchup_difficulty: true
    rest_days: true

# Edge Detection
edges:
  min_expected_value: 0.03  # Minimum 3% edge
  min_confidence: "medium"  # low, medium, high
  kelly_criterion: true
  max_kelly_fraction: 0.25  # Never bet more than 25% Kelly
  
  # Market efficiency assumptions
  market:
    vig_assumption: 0.045  # Typical sportsbook vig (4.5%)
    sharp_threshold: 0.08  # Don't bet if edge < 8% at sharp books

# Output Settings
output:
  runs_dir: "runs"
  save_format: ["parquet", "csv"]  # Output formats
  
  # Artifacts to generate
  artifacts:
    - "projections"
    - "simulations"
    - "edges"
    - "diagnostics"
    - "plots"
  
  # Visualization
  plots:
    - "calibration"
    - "roi_by_stat"
    - "edge_distribution"
    - "hit_rate"
  
  # Logging
  logging:
    level: "INFO"  # DEBUG, INFO, WARNING, ERROR
    file: "logs/nba_proj.log"
    console: true

# API Settings
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["http://localhost:3000"]
  
  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60

# Performance
performance:
  parallel: true
  n_workers: 4  # Number of parallel workers, null for auto
  chunk_size: 100  # Players per chunk in parallel processing

# Validation and Testing
validation:
  enable_backtesting: true
  backtest_window_days: 30
  validation_split: 0.2  # Hold out 20% for validation
  
  # Alerts
  alerts:
    calibration_threshold: 0.85  # Alert if calibration drops below 85%
    roi_threshold: -0.05  # Alert if ROI drops below -5%
```

## Environment Variables

Set sensitive data via environment variables:

```bash
# .env file
NBA_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:password@localhost/nba_proj
REDIS_URL=redis://localhost:6379
```

Load environment variables:

```bash
# Using direnv
direnv allow

# Or export manually
export NBA_API_KEY=your_api_key_here
```

## Configuration by Component

### ETL Configuration

Control data ingestion and preprocessing:

```yaml
etl:
  sources:
    - name: "game_logs"
      enabled: true
    - name: "injury_reports"
      enabled: true
    - name: "lineups"
      enabled: true
  
  transformations:
    normalize_stats: true
    calculate_advanced_metrics: true
    outlier_detection: true
    
  quality_checks:
    - "no_null_player_ids"
    - "valid_date_ranges"
    - "stat_bounds"
```

### Prior Calculation

Customize how priors are calculated:

```yaml
priors:
  # Weighting scheme
  weights:
    recent_games: 0.4  # Last 10 games
    season_to_date: 0.3
    previous_season: 0.2
    career: 0.1
  
  # Regression targets
  regression:
    league_average: true
    position_average: true
    team_system: true
  
  # Special cases
  rookies:
    use_college_stats: false
    use_draft_position: true
    strong_regression: true
```

### Simulation Settings

Fine-tune simulation behavior:

```yaml
simulation:
  # Performance vs accuracy tradeoff
  mode: "balanced"  # fast, balanced, accurate
  
  # Fast mode: 1000 simulations
  # Balanced mode: 10000 simulations
  # Accurate mode: 100000 simulations
  
  # Advanced options
  advanced:
    antithetic_variates: true  # Variance reduction
    control_variates: false
    importance_sampling: false
```

### Edge Detection

Configure betting edge identification:

```yaml
edges:
  # Filters
  filters:
    min_ev: 0.05
    min_confidence: "medium"
    max_bet_size: 100  # Max units
    sports_books: ["draftkings", "fanduel", "betmgm"]
  
  # Risk management
  risk:
    max_daily_exposure: 500
    max_player_exposure: 100
    diversification_required: true
  
  # Edge categories
  tiers:
    - name: "strong"
      min_ev: 0.10
      confidence: "high"
    - name: "medium"
      min_ev: 0.05
      confidence: "medium"
    - name: "weak"
      min_ev: 0.03
      confidence: "medium"
```

## Override Configuration

### Command Line

Override config values via CLI:

```bash
# Override single value
make simulate DATE=2025-10-28 N_SIMS=50000

# Override multiple values
make simulate DATE=2025-10-28 N_SIMS=50000 SEED=123
```

### Python API

Override when using as a library:

```python
from nba_proj import Simulator
from nba_proj.config import load_config

config = load_config("config.yaml")
config.simulation.n_simulations = 50000

simulator = Simulator(config)
results = simulator.run(date="2025-10-28")
```

## Profile-Based Configuration

Use different profiles for different scenarios:

```yaml
# config.yaml
default: &default
  simulation:
    n_simulations: 10000

development:
  <<: *default
  simulation:
    n_simulations: 1000  # Faster for dev

production:
  <<: *default
  simulation:
    n_simulations: 100000  # More accurate

testing:
  <<: *default
  simulation:
    n_simulations: 100  # Fast tests
```

Load specific profile:

```bash
export CONFIG_PROFILE=production
make simulate DATE=2025-10-28
```

## Validation

Validate your configuration:

```bash
# Check config syntax
make validate-config

# Test with sample data
make test-config
```

## Best Practices

1. **Version Control**: Commit `config.yaml`, use `.env` for secrets
2. **Documentation**: Comment non-obvious settings
3. **Testing**: Test config changes with historical data
4. **Monitoring**: Track performance metrics when tuning
5. **Backups**: Keep working configurations saved

## Troubleshooting

### Common Issues

**Problem**: Simulations are too slow
```yaml
# Solution: Reduce simulations or enable parallel processing
simulation:
  n_simulations: 5000
performance:
  parallel: true
  n_workers: 8
```

**Problem**: Poor calibration
```yaml
# Solution: Adjust prior weights or lookback window
data:
  lookback_days: 365  # Use more history
simulation:
  prior:
    pts:
      shape_prior_weight: 0.5  # Stronger regression to mean
```

**Problem**: Too few edges found
```yaml
# Solution: Relax edge detection criteria
edges:
  min_expected_value: 0.02  # Lower threshold
  min_confidence: "low"
```

**Problem**: Out of memory errors
```yaml
# Solution: Reduce chunk size or disable parallel processing
performance:
  parallel: false
  chunk_size: 50
```

## Advanced Topics

### Custom Priors

Define sport-specific or custom priors:

```yaml
simulation:
  model:
    custom_priors:
      pts:
        type: "hierarchical"
        levels: ["league", "position", "player"]
      reb:
        type: "conditional"
        conditions: ["height", "position"]
```

### Feature Engineering

Configure feature transformations:

```yaml
features:
  engineering:
    - name: "rolling_average"
      window: 10
      stats: ["pts", "reb", "ast"]
    - name: "trend"
      window: 20
      method: "linear"
    - name: "opponent_strength"
      metric: "defensive_rating"
```

### Database Configuration

Configure database connections for persistent storage:

```yaml
database:
  type: "postgresql"  # postgresql, sqlite, mysql
  host: "${DB_HOST}"
  port: 5432
  name: "nba_proj"
  user: "${DB_USER}"
  password: "${DB_PASSWORD}"
  
  # Connection pool
  pool:
    min_size: 2
    max_size: 10
```

### Caching Configuration

Configure caching for performance:

```yaml
cache:
  enabled: true
  backend: "redis"  # redis, memory, disk
  ttl: 3600  # Time to live in seconds
  
  redis:
    host: "${REDIS_HOST}"
    port: 6379
    db: 0
```

## Configuration Reference

### Data Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | string | "nba_stats" | Data source provider |
| `cache_dir` | string | "data/cache" | Cache directory path |
| `lookback_days` | int | 180 | Days of historical data |
| `min_games_threshold` | int | 10 | Min games for estimates |

### Simulation Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_simulations` | int | 10000 | Number of simulations |
| `random_seed` | int | 42 | Random seed |
| `model.type` | string | "gamma_poisson" | Model type |

### Edges Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_expected_value` | float | 0.03 | Minimum EV (3%) |
| `min_confidence` | string | "medium" | Min confidence level |
| `kelly_criterion` | bool | true | Use Kelly sizing |
| `max_kelly_fraction` | float | 0.25 | Max Kelly fraction |

### Output Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `runs_dir` | string | "runs" | Output directory |
| `save_format` | list | ["parquet", "csv"] | Output formats |
| `logging.level` | string | "INFO" | Log level |

### API Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | string | "0.0.0.0" | API host |
| `port` | int | 8000 | API port |
| `debug` | bool | false | Debug mode |

### Performance Section

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parallel` | bool | true | Enable parallel processing |
| `n_workers` | int | 4 | Number of workers |
| `chunk_size` | int | 100 | Items per chunk |

## Configuration Examples

### Conservative Settings (Higher Accuracy)

```yaml
simulation:
  n_simulations: 100000
  model:
    prior:
      pts:
        shape_prior_weight: 0.5  # More regression

edges:
  min_expected_value: 0.08  # Only strong edges
  min_confidence: "high"
  kelly_criterion: true
  max_kelly_fraction: 0.10  # Conservative sizing
```

### Aggressive Settings (More Edges)

```yaml
simulation:
  n_simulations: 10000
  model:
    prior:
      pts:
        shape_prior_weight: 0.2  # Less regression

edges:
  min_expected_value: 0.02  # Lower threshold
  min_confidence: "low"
  max_kelly_fraction: 0.50  # Aggressive sizing
```

### Fast Development Settings

```yaml
simulation:
  n_simulations: 1000

performance:
  parallel: true
  n_workers: 8

output:
  artifacts:
    - "projections"  # Only essentials
```

## Support

For configuration questions, see the [documentation](docs/) or open an issue on GitHub.