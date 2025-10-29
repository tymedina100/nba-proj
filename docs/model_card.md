# Model Card (MVP)
- Targets: PTS/REB/AST (per player)
- Priors: Gamma–Poisson per-minute rates with exponential decay
- Minutes: role-based rules + CSV overrides
- Matchup: simple pace and defense scalers
- Simulation: posterior predictive (NegBin); shared game pace shock
- Pricing: fair odds, EV, Top-N report
- Validation: CLV (later), calibration buckets (later)
Known limitations: placeholder ETL; dummy data until wired to real sources.
