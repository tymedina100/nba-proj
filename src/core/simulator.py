# src/core/simulator.py
import argparse
import os
import pathlib
import numpy as np
import pandas as pd
from numpy.random import default_rng


def posterior_samples(alpha: float, beta: float, minutes: float, draws: int, rng: np.random.Generator, rate_mult: float = 1.0):
    """
    Conjugate Gamma–Poisson: lambda ~ Gamma(alpha, beta); X ~ Poisson(lambda * minutes).
    We parameterize Gamma with shape=alpha and scale=1/beta.
    Role-based rate adjustments multiply lambda by `rate_mult`.
    """
    lam = rng.gamma(shape=float(alpha), scale=1.0 / float(beta), size=draws)
    lam = lam * float(rate_mult)
    return rng.poisson(lam * float(minutes))


def summarize(samples: np.ndarray) -> dict:
    s = np.asarray(samples, dtype=float)
    return {
        "mean": float(s.mean()),
        "median": float(np.quantile(s, 0.50)),
        "p10": float(np.quantile(s, 0.10)),
        "p90": float(np.quantile(s, 0.90)),
        "sigma": float(s.std(ddof=1)),
    }


def main(run_date: str, draws: int = 5000):
    pri_path = "data/parquet/priors/priors_players.csv"
    if not os.path.exists(pri_path):
        raise SystemExit("[simulate] priors missing; run `python -m src.core.priors --update --date YYYY-MM-DD` first")
    pri = pd.read_csv(pri_path)
    if pri.empty:
        raise SystemExit("[simulate] priors table is empty; check ETL/priors steps")

    # Default minutes table: everyone at 30±4 as a baseline (overrides can change this)
    players = pri["player_id"].unique()
    minutes = pd.DataFrame({"player_id": players, "min_proj": 30.0, "min_sd": 4.0})

    # Optional hand-edited overrides: data/minutes_overrides.csv with columns:
    # player_id,min_proj,min_sd[,note]
    ovr_path = "data/minutes_overrides.csv"
    if os.path.exists(ovr_path):
        ovr = pd.read_csv(ovr_path)
        keep_cols = [c for c in ["player_id", "min_proj", "min_sd"] if c in ovr.columns]
        if "player_id" not in keep_cols:
            raise SystemExit("[simulate] minutes_overrides.csv must include a 'player_id' column")
        ovr = ovr[keep_cols].drop_duplicates("player_id")
        minutes = minutes.merge(ovr, on="player_id", how="left", suffixes=("", "_ovr"))
        # prefer overrides where provided
        minutes["min_proj"] = minutes["min_proj_ovr"].fillna(minutes["min_proj"])
        minutes["min_sd"] = minutes["min_sd_ovr"].fillna(minutes["min_sd"])
        minutes = minutes.drop(columns=[c for c in minutes.columns if c.endswith("_ovr")])

        # Warn on override player_ids not in priors (typos)
        missing = set(ovr["player_id"]) - set(players)
        if missing:
            print(f"[simulate] WARNING: {len(missing)} override player_id(s) not in priors: {sorted(list(missing))[:10]}...")

    # Date-stable randomness so the same --date yields identical results
    rng = default_rng(abs(hash(run_date)) % (2**32))

    # Shared pace shock (multiplicative on counts); 5% sd tracer-bullet
    pace_shock = rng.normal(loc=1.0, scale=0.05)

    # --- NEW: cache a single minutes draw per player across all stats for coherence ---
    minutes_draws: dict[str, float] = {}

    out_rows = []
    # Iterate one prior row per (player_id, stat)
    for _, row in pri.iterrows():
        pid = row["player_id"]
        stat = row["stat"]

        # Minutes params
        m_row = minutes.loc[minutes["player_id"] == pid]
        if m_row.empty:
            m_mu, m_sd = 30.0, 4.0
        else:
            m_mu = float(m_row.iloc[0]["min_proj"])
            m_sd = float(m_row.iloc[0]["min_sd"])

        # Apply role-based multipliers if present
        min_mult = float(row["min_mult"]) if "min_mult" in row else 1.0
        rate_mult = float(row["rate_mult"]) if "rate_mult" in row else 1.0

        m_mu_adj = m_mu * min_mult
        m_sd_adj = m_sd * min_mult

        # Draw minutes ONCE per player, reuse for PTS/REB/AST (and thus composites)
        if pid not in minutes_draws:
            minutes_draws[pid] = float(np.clip(rng.normal(m_mu_adj, m_sd_adj), 6.0, 44.0))
        m_draw = minutes_draws[pid]

        # Posterior predictive samples and summary (apply shared pace and role-based rate multiplier)
        samples = posterior_samples(
            alpha=float(row["alpha"]),
            beta=float(row["beta"]),
            minutes=m_draw,
            draws=draws,
            rng=rng,
            rate_mult=rate_mult
        )
        samples = samples * pace_shock  # apply shared game-level scaling
        summ = summarize(samples)

        out_rows.append({
            "date": run_date,
            "player_id": pid,
            "stat": stat,
            "minutes": m_draw,
            "role": row["role"] if "role" in row else None,
            "min_mult": min_mult,
            "rate_mult": rate_mult,
            **summ,
        })

    pred = pd.DataFrame(out_rows)
    out_path = pathlib.Path(f"runs/{run_date}/predictions.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pred.to_csv(out_path, index=False)
    print(f"[simulate] wrote {out_path} ({len(pred)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--draws", type=int, default=5000)
    args = ap.parse_args()
    main(args.date, args.draws)
