# src/core/priors.py
import argparse
import pathlib
import pandas as pd
from src.utils.io import read_csv_glob

# Legacy global fallback (kept for non-PTS/REB/AST or as ultimate default)
PRIOR_ALPHA = 5.0
PRIOR_BETA = 120.0

# Seed priors per stat (pseudo-minutes strength via beta)
# mean rate ≈ alpha / beta (per-minute); example targets produce realistic early-season outputs
PRIOR_BY_STAT = {
    # ~0.45 pts/min → ~13.5 @30m with light prior strength (beta=200)
    "PTS": {"alpha": 0.45 * 200.0, "beta": 200.0},
    # ~0.12 reb/min → ~3.6 @30m
    "REB": {"alpha": 0.12 * 200.0, "beta": 200.0},
    # ~0.09 ast/min → ~2.7 @30m
    "AST": {"alpha": 0.09 * 200.0, "beta": 200.0},
}

# --- Role weighting (conservative defaults) ---
ROLE_WEIGHTS = {
    "starter": {"min_mult": 1.00, "rate_mult": 1.00},
    "sixth":   {"min_mult": 0.88, "rate_mult": 1.02},
    "bench":   {"min_mult": 0.70, "rate_mult": 0.98},
}
DEFAULT_ROLE = "bench"


def _resolve_role(series: pd.Series, window: int = 5) -> str:
    """
    Resolve a single role string from a per-game 'role' series.
    Uses mode over the last `window` entries, falls back to most recent, else DEFAULT_ROLE.
    """
    if series is None or series.empty:
        return DEFAULT_ROLE
    window_roles = series.tail(window).dropna()
    if window_roles.empty:
        last = series.dropna().iloc[-1] if not series.dropna().empty else DEFAULT_ROLE
        return last if last in ROLE_WEIGHTS else DEFAULT_ROLE
    mode = window_roles.mode()
    role = (mode.iloc[0] if not mode.empty else window_roles.iloc[-1])
    return role if role in ROLE_WEIGHTS else DEFAULT_ROLE


def build_player_priors(boxscores_df: pd.DataFrame, lookback_games: int = 10):
    """
    Returns dict[player_id] -> prior dict with minutes/rate params (role-weighted).
    Expects columns: ['player_id','date','minutes','PTS','REB','AST', 'role'(optional)]
    """
    import numpy as np

    df = boxscores_df.copy()
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass

    priors = {}
    for pid, g in df.groupby("player_id"):
        g = g.sort_values("date") if "date" in g.columns else g
        g = g.tail(lookback_games)
        if g.empty:
            continue

        mins = pd.to_numeric(g["minutes"], errors="coerce").fillna(0).clip(lower=0)

        with np.errstate(divide="ignore", invalid="ignore"):
            mp = mins.replace(0, np.nan)
            pts_pm = (g["PTS"] / mp).fillna(0).clip(lower=0)
            reb_pm = (g["REB"] / mp).fillna(0).clip(lower=0)
            ast_pm = (g["AST"] / mp).fillna(0).clip(lower=0)

        role = _resolve_role(g["role"]) if "role" in g.columns else DEFAULT_ROLE
        rweights = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS[DEFAULT_ROLE])

        minutes_mean = float(mins.mean())
        minutes_std = float(mins.std(ddof=1)) if len(mins) > 1 else 0.0
        pts_pm_mean = float(pts_pm.mean())
        reb_pm_mean = float(reb_pm.mean())
        ast_pm_mean = float(ast_pm.mean())

        # Apply role scaling
        minutes_mean *= rweights["min_mult"]
        minutes_std *= rweights["min_mult"]
        pts_pm_mean *= rweights["rate_mult"]
        reb_pm_mean *= rweights["rate_mult"]
        ast_pm_mean *= rweights["rate_mult"]

        priors[pid] = {
            "minutes_mean": minutes_mean,
            "minutes_std": minutes_std,
            "pts_per_min": pts_pm_mean,
            "reb_per_min": reb_pm_mean,
            "ast_per_min": ast_pm_mean,
            "n_games": int(len(g)),
            "role": role,
            "min_mult": rweights["min_mult"],
            "rate_mult": rweights["rate_mult"],
        }

    return priors


def update_priors(run_date: str):
    priors_path = pathlib.Path("data/parquet/priors/priors_players.csv")
    pri = pd.read_csv(priors_path) if priors_path.exists() else pd.DataFrame(
        columns=[
            "player_id", "stat", "alpha", "beta", "minutes_scale",
            "n_games", "last_update", "role", "min_mult", "rate_mult"
        ]
    )
    df = read_csv_glob("data/parquet/boxscores/box_*.csv")
    if df.empty:
        print("[priors] no boxscores found; seeding defaults")
        return

    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"])
        except Exception:
            pass

    # Build per-player role map from most recent window
    role_map = {}
    if "role" in df.columns:
        if "date" in df.columns:
            df = df.sort_values(["player_id", "date"])
        for pid, g in df.groupby("player_id"):
            role = _resolve_role(g["role"])
            rw = ROLE_WEIGHTS.get(role, ROLE_WEIGHTS[DEFAULT_ROLE])
            role_map[pid] = (role, rw["min_mult"], rw["rate_mult"])

    agg = df.groupby("player_id").agg(
        minutes=("minutes", "sum"),
        PTS=("PTS", "sum"),
        REB=("REB", "sum"),
        AST=("AST", "sum"),
        n_games=("game_id", "count"),
    ).reset_index()

    rows = []
    for _, r in agg.iterrows():
        role, min_mult, rate_mult = role_map.get(
            r.player_id,
            (DEFAULT_ROLE, ROLE_WEIGHTS[DEFAULT_ROLE]["min_mult"], ROLE_WEIGHTS[DEFAULT_ROLE]["rate_mult"])
        )
        for stat in ["PTS", "REB", "AST"]:
            old = pri[(pri.player_id == r.player_id) & (pri.stat == stat)]
            if len(old) == 1:
                a0, b0 = float(old.alpha.iloc[0]), float(old.beta.iloc[0])
                n0 = int(old.n_games.iloc[0])
            else:
                base = PRIOR_BY_STAT.get(stat)
                if base:
                    a0, b0 = float(base["alpha"]), float(base["beta"])
                else:
                    a0, b0 = PRIOR_ALPHA, PRIOR_BETA
                n0 = 0
            x, m = float(r[stat]), float(r["minutes"])
            a1, b1 = a0 + x, b0 + m
            rows.append(dict(
                player_id=r.player_id,
                stat=stat,
                alpha=a1,
                beta=b1,
                minutes_scale=36.0,  # kept for compatibility
                n_games=n0 + int(r.n_games),
                last_update=run_date,
                role=role,
                min_mult=min_mult,
                rate_mult=rate_mult,
            ))

    out = pd.DataFrame(rows)
    priors_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(priors_path, index=False)
    print(f"[priors] updated priors -> {priors_path} ({len(out)} rows)")


__all__ = [
    "ROLE_WEIGHTS",
    "DEFAULT_ROLE",
    "_resolve_role",
    "build_player_priors",
    "update_priors",
    "PRIOR_BY_STAT",
    "PRIOR_ALPHA",
    "PRIOR_BETA",
]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--date", required=False, default="1970-01-01")
    args = ap.parse_args()
    if args.update:
        update_priors(args.date)
