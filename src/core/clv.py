# src/core/clv.py
from __future__ import annotations
import argparse, os
from pathlib import Path
import pandas as pd
import numpy as np

def _decimal_to_prob(d: float | None) -> float | None:
    try:
        d = float(d)
        if d <= 1.0:
            return None
        return 1.0 / d
    except Exception:
        return None

def main(run_date: str, closing_csv: str, edges_csv: str | None = None) -> None:
    # 1) open = our edges (written by pricing)
    edges_path = Path(edges_csv) if edges_csv else Path(f"runs/{run_date}/edges.csv")
    if not edges_path.exists():
        raise SystemExit(f"[clv] edges not found: {edges_path}")
    e = pd.read_csv(edges_path)

    # 2) close = user-provided CSV of closing odds (same key fields)
    c = pd.read_csv(closing_csv)

    # normalize / fill implied probs
    if "book_prob" not in e.columns:
        e["book_prob"] = e["decimal_odds"].apply(_decimal_to_prob)
    if "book_prob" not in c.columns:
        if "decimal_odds" not in c.columns:
            raise SystemExit("[clv] closing CSV must include either 'book_prob' or 'decimal_odds'")
        c["book_prob"] = c["decimal_odds"].apply(_decimal_to_prob)

    key = ["player_id", "market", "side", "line"]
    for col in key:
        if col not in e.columns: raise SystemExit(f"[clv] edges.csv missing {col}")
        if col not in c.columns: raise SystemExit(f"[clv] closing.csv missing {col}")

    merged = e.merge(c[key + ["book_prob", "decimal_odds"]]
                       .rename(columns={"book_prob":"book_prob_close",
                                        "decimal_odds":"decimal_odds_close"}),
                     on=key, how="inner")

    # compute CLV relative to our fair prob at pricing time
    merged["clv_open"]  = merged["book_prob"]        - merged["fair_p"]
    merged["clv_close"] = merged["book_prob_close"]  - merged["fair_p"]

    out = merged[["player_id","market","side","line",
                  "fair_p","decimal_odds","book_prob",
                  "decimal_odds_close","book_prob_close",
                  "clv_open","clv_close"]].copy()
    out.insert(0, "date", run_date)

    out_path = Path(f"runs/{run_date}/clv_log.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # append-or-create
    if out_path.exists():
        prev = pd.read_csv(out_path)
        out = pd.concat([prev, out], ignore_index=True)

    out.to_csv(out_path, index=False)
    print(f"[clv] wrote {out_path} ({len(out)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--closing", required=True, help="CSV of closing odds (player_id,market,side,line,decimal_odds or book_prob)")
    ap.add_argument("--edges", required=False, help="Optional path to edges.csv (defaults to runs/{date}/edges.csv)")
    args = ap.parse_args()
    os.makedirs("runs", exist_ok=True)
    main(args.date, args.closing, args.edges)
