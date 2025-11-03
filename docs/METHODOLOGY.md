# Methodology

This document explains the statistical and mathematical foundations of the NBA-Proj simulation system.

## Overview

The system uses Bayesian inference combined with Monte Carlo simulation to generate probabilistic projections for NBA player performance. The approach is grounded in three core principles:

1. **Conjugate Priors**: Use of Gamma-Poisson conjugacy for efficient, closed-form posteriors
2. **Minutes-First Logic**: Treating playing time as the primary uncertainty
3. **Hierarchical Modeling**: Incorporating multiple levels of information (league, position, player)

## The Gamma-Poisson Model

### Why Gamma-Poisson?

Count statistics (points, rebounds, assists) are naturally modeled as Poisson processes, but with player-specific rates that themselves vary. The Gamma-Poisson conjugate model elegantly handles this:

- **Poisson likelihood**: Models the counting process within a game
- **Gamma prior**: Represents uncertainty about the player's true rate
- **Negative Binomial posterior predictive**: Natural overdispersion

### Mathematical Framework

#### Prior Distribution

For a player's stat rate λ (e.g., points per minute):

```
λ ~ Gamma(α, β)

where:
  α = shape parameter (captures consistency)
  β = rate parameter (inverse scale)
  
Expected value: E[λ] = α/β
Variance: Var[λ] = α/β²
```

#### Likelihood

Given λ, observed stat X follows:

```
X | λ ~ Poisson(λ × minutes)
```

#### Posterior

After observing data x₁, x₂, ..., xₙ over m₁, m₂, ..., mₙ minutes:

```
λ | data ~ Gamma(α + Σxᵢ, β + Σmᵢ)
```

This is a key advantage: the posterior is in the same family as the prior, allowing for efficient recursive updates.

#### Posterior Predictive

For a future game with projected minutes M:

```
X* ~ NegativeBinomial(α*, p*)

where:
  α* = α + Σxᵢ (updated shape)
  p* = β / (β + Σmᵢ + M)
  
Expected value: E[X*] = α* × M × (1-p*) / p*
```

## Prior Construction

### Information Sources

We construct priors by combining multiple information sources with appropriate weights:

1. **Recent Performance** (40%)
   - Last 10 games with exponential decay
   - Captures current form and momentum

2. **Season-to-Date** (30%)
   - Full season statistics
   - Stabilizes against small sample noise

3. **Previous Season** (20%)
   - Adjusted for aging curves
   - Provides baseline for regression

4. **Career Statistics** (10%)
   - Shrinkage target for extreme estimates
   - Especially important for players with limited data

### Weighting Formula

```
α_prior = w₁α_recent + w₂α_season + w₃α_previous + w₄α_career
β_prior = w₁β_recent + w₂β_season + w₃β_previous + w₄β_career

where Σwᵢ = 1
```

### Regression to the Mean

To prevent overconfidence in small samples, we incorporate regression:

```
α_final = (1 - ω)α_prior + ω × α_league
β_final = (1 - ω)β_prior + ω × β_league

where ω = regression weight based on sample size
```

For players with n games:
```
ω = k / (k + n)

where k ≈ 20 (effective sample size needed for full weight)
```

## Minutes-First Approach

### Rationale

Playing time is the dominant source of uncertainty. A player who averages 30 points in 35 minutes but only plays 20 minutes will score significantly less, regardless of their per-minute rate.

### Two-Stage Model

1. **Minutes Distribution**
   ```
   M ~ Gaussian(μₘ, σₘ²)
   
   Adjusted for:
   - Injury probability
   - Back-to-back games
   - Blowout risk
   - Coach tendencies
   ```

2. **Per-Minute Rate**
   ```
   λ ~ Gamma(α, β)  # As described above
   ```

3. **Final Projection**
   ```
   For each simulation i:
     Sample mᵢ ~ Minutes distribution
     Sample xᵢ ~ NegativeBinomial(α, β, mᵢ)
   
   Return distribution of {x₁, x₂, ..., xₙ}
   ```

### Minutes Modeling

We model minutes as a truncated Gaussian:

```
M ~ TruncatedNormal(μ, σ², 0, 48)

μ = μ_baseline × Πⱼ adjustment_factorⱼ

Adjustments include:
- Home/away: ×0.98 for away
- Back-to-back: ×0.92
- Blowout risk: ×0.95 (high variance games)
- Injury report: ×0.85 (questionable) or ×0.50 (doubtful)
```

## Contextual Adjustments

### Pace Adjustment

NBA teams play at different paces (possessions per 48 minutes). We normalize:

```
λ_adjusted = λ_baseline × (pace_game / pace_league)

where pace_game = (pace_team + pace_opponent) / 2
```

### Matchup Difficulty

Defensive strength affects player production:

```
λ_adjusted = λ_baseline × matchup_factor

matchup_factor for points:
  Strong defense (top 5): 0.92
  Average defense (6-25): 1.00
  Weak defense (26-30): 1.08
```

### Home Court Advantage

Historical data shows a small but consistent home advantage:

```
λ_adjusted = λ_baseline × 1.05 (home) or ×0.95 (away)
```

## Simulation Process

### Monte Carlo Algorithm

```
For simulation i = 1 to N:
  1. Sample minutes mᵢ from minutes distribution
  2. Apply contextual adjustments to get λ_adjusted
  3. Sample stat from NegBinom(α, β, mᵢ, λ_adjusted)
  4. Store result
  
Return:
  - Full distribution
  - Summary statistics (mean, median, std)
  - Percentiles (5, 10, 25, 50, 75, 90, 95)
  - Probabilities for common betting lines
```

### Variance Reduction

To improve efficiency, we use **antithetic variates**:

For each random sample u ~ Uniform(0,1), also use 1-u. This reduces variance by inducing negative correlation between paired simulations.

### Correlation Modeling

For multi-stat simulations (e.g., points + rebounds), we model correlation:

```
ρ_pts_reb ≈ -0.2  (negative correlation)
ρ_pts_ast ≈ 0.1   (slight positive)
ρ_reb_ast ≈ -0.3  (negative correlation)

Use Gaussian copula to preserve marginal distributions
while inducing appropriate correlation structure
```

## Edge Detection

### Expected Value Calculation

```
EV = P(win) × payout - P(lose) × stake

For a bet at odds O with probability p:
  American odds: EV = p × O/100 - (1-p)  [if O > 0]
                 EV = p - (1-p) × 100/|O|  [if O < 0]
```

### Kelly Criterion

Optimal bet size given edge:

```
f* = (p × (b+1) - 1) / b

where:
  f* = fraction of bankroll
  p = true probability
  b = net odds received (decimal - 1)
```

We use **fractional Kelly** for safety:

```
f_actual = f* / 4  (quarter Kelly)

Never bet more than max_kelly_fraction = 0.25
```

### Edge Thresholds

We classify edges by strength:

- **Strong**: EV > 10%, confidence = high
- **Medium**: EV > 5%, confidence ≥ medium  
- **Weak**: EV > 3%, confidence ≥ medium

Only bet on medium or strong edges.

## Model Validation

### Calibration

We assess calibration using:

```
For each decile d of predicted probability:
  Expected frequency: d
  Observed frequency: f_d
  
Calibration score: 1 - MSE({d}, {f_d})
```

Perfect calibration: score = 1.0

### Brier Score

Measures prediction accuracy:

```
BS = (1/N) × Σ(pᵢ - oᵢ)²

where:
  pᵢ = predicted probability
  oᵢ = outcome (0 or 1)
```

Lower is better. Random guessing: BS = 0.25

### Log Loss

Penalizes confident wrong predictions:

```
LogLoss = -(1/N) × Σ[oᵢ log(pᵢ) + (1-oᵢ) log(1-pᵢ)]
```

### ROI Tracking

Ultimate measure of success:

```
ROI = (total_profit / total_staked) × 100%

Track by:
- Overall
- By stat (PTS, REB, AST)
- By edge strength
- By confidence level
```

## Assumptions and Limitations

### Assumptions

1. **Independence**: Games are independent (no hot hand)
2. **Stationarity**: Player skill relatively stable within season
3. **Poisson Process**: Stats follow counting process dynamics
4. **Market Efficiency**: Books price odds reasonably well

### Limitations

1. **Injury Uncertainty**: Difficult to predict last-minute scratches
2. **Coaching Decisions**: Rotations can change unexpectedly  
3. **Garbage Time**: Blowouts distort statistics
4. **Correlation**: Multi-prop correlation not fully captured
5. **Sample Size**: Early season estimates less reliable

### Mitigation Strategies

- Conservative confidence levels for uncertain situations
- Real-time monitoring of injury reports
- Blowout adjustments in minutes modeling
- Regular backtesting and calibration checks

## Future Enhancements

### Advanced Modeling

1. **Time Series**: ARIMA or state-space models for temporal dynamics
2. **Hierarchical Bayes**: Full hierarchical model across players/teams
3. **Neural Networks**: Ensemble with deep learning for minutes prediction
4. **Causal Inference**: Isolate true matchup effects from confounders

### Data Integration

1. **Player Tracking**: Shot quality, defensive assignments
2. **Lineup Data**: On-court/off-court splits
3. **Rest Days**: Fatigue modeling
4. **Historical Matchups**: Head-to-head performance

## References

1. Albert, J. (2009). *Bayesian Computation with R*
2. Stern, H. (1991). "On the Probability of Winning a Football Game"
3. Glickman, M. & Stern, H. (1998). "A State-Space Model for National Football League Scores"
4. Boulier, B. & Stekler, H. (2003). "Predicting the Outcomes of NCAA Basketball Games"
5. Kelly, J. (1956). "A New Interpretation of Information Rate"

## Appendix: Code Examples

### Gamma-Poisson Simulation

```python
import numpy as np
from scipy.stats import gamma, nbinom

def simulate_gamma_poisson(alpha, beta, minutes, n_sims=10000):
    """Simulate from Gamma-Poisson posterior predictive."""
    # Shape and probability for negative binomial
    r = alpha
    p = beta / (beta + minutes)
    
    # Sample from negative binomial
    samples = nbinom.rvs(r, p, size=n_sims)
    
    return samples

# Example: Player averages 25 points on 75 observed points in 3 games × 35 min
alpha_prior, beta_prior = 10, 0.5
alpha_post = alpha_prior + 75
beta_post = beta_prior + 3 * 35

# Simulate next game with 36 projected minutes
samples = simulate_gamma_poisson(alpha_post, beta_post, 36)

print(f"Mean: {samples.mean():.1f}")
print(f"Median: {np.median(samples):.1f}")
print(f"P(>25.5): {(samples > 25.5).mean():.3f}")
```

---

**For implementation details, see the source code in `src/nba_proj/simulation/`**