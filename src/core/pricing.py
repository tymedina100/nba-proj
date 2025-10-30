# src/core/pricing.py
import argparse, pathlib, pandas as pd
from math import erf, sqrt
from src.core.odds import validate_odds

def cdf_norm(x, mu, sigma):
    if sigma <= 1e-9:
        return 1.0 if x >= mu else 0.0
    from math import erf, sqrt
    z = (x - mu) / (sigma * sqrt(2))
    return 0.5 * (1.0 + erf(z))

def main(odds_path: str, run_date: str):
    preds = pd.read_csv(f"runs/{run_date}/predictions.csv")
    if preds.empty:
        raise SystemExit("[pricing] predictions missing; run simulate first")

    odds = pd.read_csv(odds_path)
    odds = validate_odds(odds)
    out = []
    for _, r in odds.iterrows():
        pid, market, side, line, d = r.player_id, r.market, r.side, float(r.line), float(r.decimal_odds)
        row = preds[(preds.player_id==pid) & (preds.stat==market)]
        if row.empty:
            continue

        #  Use dataframe columns, not the .mean() method
        mu    = float(row.iloc[0]["mean"])
        sd    = float(row.iloc[0]["sigma"])
        med   = float(row.iloc[0]["median"])
        p10   = float(row.iloc[0]["p10"])
        p90   = float(row.iloc[0]["p90"])
        mins  = float(row.iloc[0]["minutes"])

        p_over = 1.0 - cdf_norm(line, mu, sd)
        p = p_over if side.upper()=="OVER" else (1.0 - p_over)
        p = max(min(p, 1-1e-9), 1e-9)
        fair = 1.0 / p
        ev = p*(d-1.0) - (1.0-p)

        out.append(dict(
            date=run_date, player_id=pid, market=market, side=side, line=line,
            decimal_odds=d, fair_p=p, fair_odds=fair, ev=ev,
            mean=mu, median=med, p10=p10, p90=p90, sigma=sd,
            corr_group="GAME_G1", corr_reason="Shared pace shock (MVP)",
            rationale=f"Minutes{mins:.1f}; Normal approx; EV vs odds"
        ))

    edges = pd.DataFrame(out).sort_values("ev", ascending=False)
    out_path = pathlib.Path(f"runs/{run_date}/edges.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    edges.to_csv(out_path, index=False)
    if not edges.empty:
        print(edges.head(5).to_string(index=False))
    print(f"[pricing] wrote {out_path} ({len(edges)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--odds", required=True)
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    main(args.odds, args.date)
