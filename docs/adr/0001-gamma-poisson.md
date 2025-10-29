# ADR-0001: Use Gamma–Poisson for per-minute stat rates
Context: Need explainable, conjugate priors for fast updates and credible intervals.
Decision: Gamma prior on per-minute rate; posterior predictive NegBin for totals.
Consequences: Transparent updates, easy to debug; tails may be conservative for streaky players.
Status: Accepted.
