# src/metrics/calibration_bins.py
from __future__ import annotations
import argparse, os
from pathlib import Path
import pandas as pd

def bin_calibration(edges: pd.DataFrame, outcomes: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    """
    edges:    columns must include ['player_id','market','side','line','fair_p']
    outcomes: columns must include ['player_id','market','side','line','hit'] where hit ∈ {0,1}
    Returns a DataFrame with per-bin counts, predicted prob mean, empirical hit rate, and gap.
    """
    key = ["player_id","market","side","line"]
    for col in key + ["fair_p"]:
        if col not in edges.columns:
            raise SystemExit(f"[cal] edges missing required column: {col}")
    for col in key + ["hit"]:
        if col not in outcomes.columns:
            raise SystemExit(f"[cal] outcomes missing required column: {col}")

    df = edges[key + ["fair_p"]].merge(outcomes[key + ["hit"]], on=key, how="inner")
    df = df.dropna(subset=["fair_p","hit"]).copy()
    if df.empty:
        return pd.DataFrame(columns=["bin","count","p_mean","hit_rate","gap"])

    # robust qcut (handles few unique fair_p values)
    try:
        df["bin"] = pd.qcut(df["fair_p"], q=n_bins, duplicates="drop")
    except Exception:
        uniq = max(2, min(n_bins, df["fair_p"].nunique()))
        df["bin"] = pd.qcut(df["fair_p"], q=uniq, duplicates="drop")

    out = df.groupby("bin", observed=True).agg(
        count=("hit","size"),
        p_mean=("fair_p","mean"),
        hit_rate=("hit","mean"),
    ).reset_index()
    out["gap"] = out["hit_rate"] - out["p_mean"]
    return out

def main(run_date: str, outcomes_csv: str, bins: int = 10, edges_csv: str | None = None) -> None:
    edges_path = Path(edges_csv) if edges_csv else Path(f"runs/{run_date}/edges.csv")
    if not edges_path.exists():
        raise SystemExit(f"[cal] edges not found: {edges_path}")
    edges = pd.read_csv(edges_path)

    outcomes = pd.read_csv(outcomes_csv)
    cal = bin_calibration(edges, outcomes, n_bins=bins)

    out_path = Path(f"runs/{run_date}/calibration_bins.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cal.to_csv(out_path, index=False)
    print(f"[cal] wrote {out_path} ({len(cal)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--outcomes", required=True, help="CSV with realized results: player_id,market,side,line,hit")
    ap.add_argument("--bins", type=int, default=10, help="Number of probability bins (default 10)")
    ap.add_argument("--edges", required=False, help="Optional path to edges.csv (defaults to runs/{date}/edges.csv)")
    args = ap.parse_args()
    os.makedirs("runs", exist_ok=True)
    main(args.date, args.outcomes, args.bins, args.edges)
