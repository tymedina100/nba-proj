# src/core/pricing.py
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import re

def _slug(s: str) -> str:
    s = (str(s) or "").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s

def _load_predictions(run_date: str) -> pd.DataFrame:
    pred_path = Path(f"runs/{run_date}/predictions.csv")
    if not pred_path.exists():
        raise SystemExit(f"[pricing] missing predictions: {pred_path}")
    df = pd.read_csv(pred_path)
    # Expect columns: date, player_id, stat, minutes, mean, median, p10, p90, sigma
    return df

def _load_odds(odds_csv: str) -> pd.DataFrame:
    odds = pd.read_csv(odds_csv)
    # normalize headers
    odds.columns = [c.strip().lower() for c in odds.columns]
    # canonical columns: player_id or player, market, side, line, decimal_odds
    need_any = {"market","side","line","decimal_odds"}
    if not need_any.issubset(set(odds.columns)):
        raise SystemExit(f"[pricing] odds missing columns; need at least {need_any}, got {odds.columns.tolist()}")
    # standardize types
    odds["market"] = odds["market"].str.upper()
    odds["side"]   = odds["side"].str.upper()
    odds["line"]   = pd.to_numeric(odds["line"], errors="coerce")
    odds["decimal_odds"] = pd.to_numeric(odds["decimal_odds"], errors="coerce")
    return odds

def _load_name_map() -> pd.DataFrame:
    p = Path("data/mappings/name_map.csv")
    if not p.exists():
        # empty frame with expected columns
        return pd.DataFrame(columns=["sportsbook_name","player_id","notes"])
    m = pd.read_csv(p)
    m.columns = [c.strip().lower() for c in m.columns]
    if "sportsbook_name" not in m.columns or "player_id" not in m.columns:
        raise SystemExit("[pricing] name_map.csv must have columns: sportsbook_name, player_id")
    m["key"] = m["sportsbook_name"].astype(str).str.strip().str.lower()
    return m[["key","player_id"]]

def _map_player_ids(odds: pd.DataFrame, name_map: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (odds_with_ids, name_map_todo). Robust to merge-created columns."""
    odds = odds.copy()

    # Find a human-name column if present
    name_col = None
    for cand in ["player", "name", "player_name"]:
        if cand in odds.columns:
            name_col = cand
            break

    # Ensure a player_id column exists *before* merge
    if "player_id" not in odds.columns:
        odds["player_id"] = pd.NA

    todo = pd.DataFrame(columns=["sportsbook_name"]).astype({"sportsbook_name": "string"})

    if name_col:
        # exact map key
        odds["_key"] = odds[name_col].astype(str).str.strip().str.lower()

        if len(name_map):
            # merge on key; this may create player_id_x / player_id_y
            odds = odds.merge(name_map, how="left", left_on="_key", right_on="key")

            # Combine player_id_x (from odds) with player_id_y (from name_map)
            pid_x = odds.get("player_id_x", pd.Series([pd.NA] * len(odds)))
            pid_y = odds.get("player_id_y", pd.Series([pd.NA] * len(odds)))
            combined = pid_x.fillna(pid_y)

            # Write back to a single 'player_id' and drop auxiliaries
            odds["player_id"] = combined
            odds.drop(columns=[c for c in ["player_id_x", "player_id_y", "key"] if c in odds.columns],
                      inplace=True)

        # fallback: slug the name when still missing
        needs_slug = odds["player_id"].isna() | (odds["player_id"].astype(str).str.len() == 0)
        odds.loc[needs_slug, "player_id"] = odds.loc[needs_slug, name_col].map(_slug)

        # TODO list: anything that still failed to map (rare)
        mask_todo = odds["player_id"].isna() | (odds["player_id"].astype(str) == "")
        if mask_todo.any():
            todo = pd.DataFrame({"sportsbook_name": odds.loc[mask_todo, name_col].astype(str).unique()})

        odds.drop(columns=["_key"], errors="ignore", inplace=True)

    return odds, todo


def _norm_market(stat: str) -> str:
    x = stat.upper()
    return {"POINTS":"PTS","PTS":"PTS","ASSISTS":"AST","AST":"AST","REB":"REB","REBOUNDS":"REB"}.get(x, x)

def _price_row(mu: float, sigma: float, side: str, line: float) -> tuple[float,float]:
    """
    Normal approximation: compute P(stat > line) or P(stat < line).
    """
    if not np.isfinite(mu) or not np.isfinite(sigma) or sigma <= 0:
        return 0.0, np.inf
    z = (line - mu) / sigma
    from math import erf, sqrt
    cdf = 0.5 * (1.0 + erf(z / sqrt(2.0)))
    if side == "OVER":
        p = 1.0 - cdf
    else:
        p = cdf
    p = min(max(p, 1e-9), 1 - 1e-9)
    fair_odds = 1.0 / p
    return p, fair_odds

def main(odds_csv: str, run_date: str):
    runs_dir = Path(f"runs/{run_date}")
    runs_dir.mkdir(parents=True, exist_ok=True)

    preds = _load_predictions(run_date)
    preds["market"] = preds["stat"].map(_norm_market)

    odds = _load_odds(odds_csv)
    name_map = _load_name_map()
    odds, name_todo = _map_player_ids(odds, name_map)

    # join predictions <-> odds
    join_cols = ["player_id","market"]
    merged = odds.merge(
        preds[["player_id","market","mean","median","p10","p90","sigma"]],
        how="left", on=join_cols
    )

    # diagnostics: unmatched odds (no prediction match)
    unmatched_odds = merged[merged["mean"].isna()].copy()
    if not unmatched_odds.empty:
        unmatched_odds.to_csv(runs_dir / "unmatched_odds.csv", index=False)

    # diagnostics: players not covered by any odds row
    covered = merged.dropna(subset=["mean"])[["player_id","market"]].drop_duplicates()
    pred_keys = preds[["player_id","market"]].drop_duplicates()
    uncovered_players = pred_keys.merge(covered, on=["player_id","market"], how="left", indicator=True)
    uncovered_players = uncovered_players[uncovered_players["_merge"] == "left_only"].drop(columns=["_merge"])
    if not uncovered_players.empty:
        uncovered_players.to_csv(runs_dir / "uncovered_players.csv", index=False)

    # diagnostics: name-map TODOs
    if not name_todo.empty:
        name_todo.to_csv(runs_dir / "name_map_todo.csv", index=False)

    # compute prices for matched rows only
    matched = merged.dropna(subset=["mean","sigma","line","decimal_odds"]).copy()
    ps, fair_odds = [], []
    for _, r in matched.iterrows():
        p, f = _price_row(mu=r["mean"], sigma=r["sigma"], side=r["side"], line=float(r["line"]))
        ps.append(p); fair_odds.append(f)
    matched["fair_p"] = ps
    matched["fair_odds"] = fair_odds
    matched["ev"] = (matched["decimal_odds"] * matched["fair_p"]) - 1.0
    matched["corr_group"] = "GAME_G1"
    matched["corr_reason"] = "Shared pace shock (MVP)"
    matched["rationale"] = (
        "Minutes{:.1f}; Normal approx; EV vs odds".format(
            preds.groupby("player_id")["minutes"].mean().reindex(matched["player_id"]).fillna(0).values[0]
            if len(preds) else 0.0
        )
    )

    out_cols = [
        "date","player_id","market","side","line","decimal_odds",
        "fair_p","fair_odds","ev","mean","median","p10","p90","sigma",
        "corr_group","corr_reason","rationale"
    ]
    matched["date"] = run_date
    edges = matched[out_cols].sort_values("ev", ascending=False)
    edges.to_csv(runs_dir / "edges.csv", index=False)
    print(f"[pricing] wrote {runs_dir/'edges.csv'} ({len(edges)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--odds", required=True)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    main(args.odds, args.date)
