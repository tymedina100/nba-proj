# src/core/pricing.py
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
from typing import Optional, Iterable

import numpy as np
import pandas as pd


# ---------- math utils ----------

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _normal_over_prob(mean: float, sigma: float, line: float) -> float:
    if sigma <= 1e-8:
        return float(mean > line)
    z = (line - mean) / sigma
    return 1.0 - _norm_cdf(z)


def _normal_under_prob(mean: float, sigma: float, line: float) -> float:
    if sigma <= 1e-8:
        return float(mean < line)
    z = (line - mean) / sigma
    return _norm_cdf(z)


def _decimal_to_prob(decimal_odds: float) -> Optional[float]:
    try:
        d = float(decimal_odds)
        if d <= 1.0:
            return None
        return 1.0 / d
    except Exception:
        return None


# ---------- rationale ----------

def _rationale(
    role: Optional[str],
    min_mult: Optional[float],
    rate_mult: Optional[float],
    minutes: Optional[float],
    mean: Optional[float],
    *,
    market: str,
    side: Optional[str],
    line: Optional[float],
    sigma: Optional[float],
) -> str:
    parts = []
    if role:
        try:
            parts.append(f"role={role} (min×{float(min_mult):.2f}, rate×{float(rate_mult):.2f})")
        except Exception:
            parts.append(f"role={role}")
    if minutes is not None and np.isfinite(minutes):
        parts.append(f"proj_min≈{float(minutes):.1f}")
    if mean is not None and np.isfinite(mean):
        parts.append(f"sim_mean={float(mean):.2f}")
    if (mean is not None) and (line is not None) and np.isfinite(line):
        d = float(mean) - float(line)
        parts.append(f"Δvs_{market}({line})={d:+.2f}")
    if sigma is not None and np.isfinite(sigma):
        parts.append(f"method=Normal(σ={float(sigma):.2f})")
    elif sigma is not None:
        parts.append("method=Normal")
    return "; ".join(parts) if parts else "n/a"


# ---------- predictions loading & repair ----------

_PCTL_TO_SIGMA = 2.0 * 1.2815515655446004  # p90 - p10 ≈ 2.563103… sigmas


def _repair_mean_sigma(df: pd.DataFrame) -> pd.DataFrame:
    """Back-fill mean/sigma from available columns."""
    df = df.copy()
    if "mean" not in df.columns:
        df["mean"] = np.nan
    if "sigma" not in df.columns:
        df["sigma"] = np.nan

    # mean fallback: median > (p10+p90)/2
    if "median" in df.columns:
        df["mean"] = df["mean"].where(df["mean"].notna(), df["median"])
    if "p10" in df.columns and "p90" in df.columns:
        mid = (pd.to_numeric(df["p10"], errors="coerce") + pd.to_numeric(df["p90"], errors="coerce")) / 2.0
        df["mean"] = df["mean"].where(df["mean"].notna(), mid)

    # sigma from percentiles
    if "p10" in df.columns and "p90" in df.columns:
        spread = pd.to_numeric(df["p90"], errors="coerce") - pd.to_numeric(df["p10"], errors="coerce")
        est_sigma = spread / _PCTL_TO_SIGMA
        df["sigma"] = df["sigma"].where(df["sigma"].notna(), est_sigma)

    return df


def _load_predictions(run_date: str) -> pd.DataFrame:
    p = Path(f"runs/{run_date}/predictions.csv")
    if not p.exists():
        raise SystemExit(f"[pricing] predictions not found: {p}")
    df = pd.read_csv(p)

    # rename 'stat' -> 'market'
    if "stat" in df.columns and "market" not in df.columns:
        df = df.rename(columns={"stat": "market"})

    # ensure helpful columns exist
    for c in ["minutes", "role", "min_mult", "rate_mult", "p10", "p90", "median"]:
        if c not in df.columns:
            df[c] = np.nan

    # repair mean/sigma if missing
    df = _repair_mean_sigma(df)

    # build composites if missing (PA, RA, PRA)
    df = _with_composites(df, composites=["PA", "RA", "PRA"])

    return df


def _with_composites(df: pd.DataFrame, composites: Iterable[str]) -> pd.DataFrame:
    """Add composite markets from PTS/REB/AST if requested."""
    need = set(composites)
    # early exit if all present
    if need.issubset(set(df["market"].unique())):
        return df

    # pivot per player to get means/sigmas for base stats
    base = df[df["market"].isin(["PTS", "REB", "AST"])].copy()
    if base.empty:
        return df

    wide_mean = base.pivot_table(index="player_id", columns="market", values="mean", aggfunc="mean")
    wide_sig  = base.pivot_table(index="player_id", columns="market", values="sigma", aggfunc="mean")

    rows = []
    for pid in wide_mean.index:
        pts_m, reb_m, ast_m = wide_mean.get("PTS", np.nan).get(pid, np.nan), wide_mean.get("REB", np.nan).get(pid, np.nan), wide_mean.get("AST", np.nan).get(pid, np.nan)
        pts_s, reb_s, ast_s = wide_sig.get("PTS", np.nan).get(pid, np.nan), wide_sig.get("REB", np.nan).get(pid, np.nan), wide_sig.get("AST", np.nan).get(pid, np.nan)

        # assume zero correlation for simple composite variance
        def sum_sigma(*sigmas):
            sigmas = [float(s) for s in sigmas if pd.notna(s)]
            return float(np.sqrt(np.sum(np.square(sigmas)))) if sigmas else np.nan

        if "PA" in need:
            mean_pa = (pts_m if pd.notna(pts_m) else 0.0) + (ast_m if pd.notna(ast_m) else 0.0)
            sigma_pa = sum_sigma(pts_s, ast_s)
            rows.append({"player_id": pid, "market": "PA", "mean": mean_pa, "sigma": sigma_pa})
        if "RA" in need:
            mean_ra = (reb_m if pd.notna(reb_m) else 0.0) + (ast_m if pd.notna(ast_m) else 0.0)
            sigma_ra = sum_sigma(reb_s, ast_s)
            rows.append({"player_id": pid, "market": "RA", "mean": mean_ra, "sigma": sigma_ra})
        if "PRA" in need:
            mean_pra = sum(m for m in [pts_m, reb_m, ast_m] if pd.notna(m))
            sigma_pra = sum_sigma(pts_s, reb_s, ast_s)
            rows.append({"player_id": pid, "market": "PRA", "mean": mean_pra, "sigma": sigma_pra})

    if not rows:
        return df

    comp = pd.DataFrame(rows)
    # bring minutes/role multipliers from any one of the base rows (first match)
    keep_cols = ["minutes", "role", "min_mult", "rate_mult"]
    if any(c in df.columns for c in keep_cols):
        base_keep = (base.sort_values("market")
                         .drop_duplicates(subset=["player_id"])[["player_id"] + [c for c in keep_cols if c in base.columns]])
        comp = comp.merge(base_keep, on="player_id", how="left")

    # we don't have p10/p90/median for composites here
    comp["p10"] = np.nan
    comp["p90"] = np.nan
    comp["median"] = np.nan

    out = pd.concat([df, comp], ignore_index=True)
    return out


# ---------- odds & pricing ----------

def _load_odds(odds_csv: str) -> pd.DataFrame:
    df = pd.read_csv(odds_csv)
    needed = ["player_id", "market", "side", "line"]
    for c in needed:
        if c not in df.columns:
            raise SystemExit(f"[pricing] odds CSV missing required column: {c}")
    if ("decimal_odds" not in df.columns) and ("book_prob" not in df.columns):
        raise SystemExit("[pricing] odds CSV must include either 'decimal_odds' or 'book_prob'")
    return df


def _compute_fair_prob(row: pd.Series) -> Optional[float]:
    mean = row.get("mean", np.nan)
    sigma = row.get("sigma", np.nan)
    side = str(row.get("side", "")).lower()
    line = row.get("line", np.nan)

    if not (np.isfinite(mean) and np.isfinite(sigma) and np.isfinite(line)):
        return None
    if side not in ("over", "under"):
        return None

    return float(_normal_over_prob(mean, sigma, line) if side == "over"
                 else _normal_under_prob(mean, sigma, line))


def build_edges(odds: pd.DataFrame, preds: pd.DataFrame, run_date: str) -> pd.DataFrame:
    join_cols = ["player_id", "market"]

    # bring through helpful columns from predictions
    pred_keep = ["player_id", "market", "mean", "median", "p10", "p90", "sigma", "minutes", "role", "min_mult", "rate_mult"]
    for c in pred_keep:
        if c not in preds.columns:
            preds[c] = np.nan
    preds_slim = preds[pred_keep].drop_duplicates(subset=["player_id", "market"])

    merged = odds.merge(preds_slim, how="left", on=join_cols)

    if "book_prob" not in merged.columns:
        merged["book_prob"] = merged["decimal_odds"].apply(_decimal_to_prob)

    merged["fair_p"] = merged.apply(_compute_fair_prob, axis=1)

    if "decimal_odds" not in merged.columns:
        merged["decimal_odds"] = np.nan
    merged["ev"] = (merged["decimal_odds"] * merged["fair_p"]) - 1.0

    merged["rationale"] = merged.apply(
        lambda r: _rationale(
            role=r.get("role"),
            min_mult=r.get("min_mult"),
            rate_mult=r.get("rate_mult"),
            minutes=r.get("minutes"),
            mean=r.get("mean"),
            market=str(r.get("market")),
            side=str(r.get("side")),
            line=r.get("line"),
            sigma=r.get("sigma"),
        ),
        axis=1,
    )

    keep = [
        "player_id", "market", "side", "line",
        "decimal_odds", "book_prob", "fair_p", "ev",
        "mean", "sigma", "minutes", "role", "min_mult", "rate_mult",
        "rationale",
    ]
    for c in keep:
        if c not in merged.columns:
            merged[c] = np.nan

    out = merged[keep].copy()
    out.insert(0, "date", run_date)
    return out


# ---------- CLI ----------

def main(odds_csv: str, run_date: str) -> None:
    preds = _load_predictions(run_date)
    odds = _load_odds(odds_csv)
    edges = build_edges(odds, preds, run_date)

    out_path = Path(f"runs/{run_date}/edges.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    edges.to_csv(out_path, index=False)
    print(f"[pricing] wrote {out_path} ({len(edges)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--odds", required=True, help="CSV: player_id,market,side,line,(decimal_odds|book_prob)")
    ap.add_argument("--date", required=True, help="Run date, e.g., 2025-10-27")
    args = ap.parse_args()
    os.makedirs("runs", exist_ok=True)
    main(args.odds, args.date)
