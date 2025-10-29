# src/core/priors.py
import argparse, pathlib, pandas as pd
from src.utils.io import read_csv_glob

PRIOR_ALPHA = 5.0
PRIOR_BETA  = 120.0

def update_priors(run_date: str):
    priors_path = pathlib.Path("data/parquet/priors/priors_players.csv")
    pri = pd.read_csv(priors_path) if priors_path.exists() else pd.DataFrame(
        columns=["player_id","stat","alpha","beta","minutes_scale","n_games","last_update"]
    )
    df = read_csv_glob("data/parquet/boxscores/box_*.csv")
    if df.empty:
        print("[priors] no boxscores found; seeding defaults")
        return

    agg = df.groupby("player_id").agg(minutes=("minutes","sum"),
                                      PTS=("PTS","sum"),
                                      REB=("REB","sum"),
                                      AST=("AST","sum"),
                                      n_games=("game_id","count")).reset_index()
    rows = []
    for _, r in agg.iterrows():
        for stat in ["PTS","REB","AST"]:
            old = pri[(pri.player_id==r.player_id)&(pri.stat==stat)]
            if len(old)==1:
                a0, b0 = float(old.alpha.iloc[0]), float(old.beta.iloc[0])
                n0 = int(old.n_games.iloc[0])
            else:
                a0, b0, n0 = PRIOR_ALPHA, PRIOR_BETA, 0
            x, m = float(r[stat]), float(r["minutes"])
            a1, b1 = a0 + x, b0 + m
            rows.append(dict(player_id=r.player_id, stat=stat,
                             alpha=a1, beta=b1, minutes_scale=36.0,
                             n_games=n0+int(r.n_games), last_update=run_date))
    out = pd.DataFrame(rows)
    priors_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(priors_path, index=False)
    print(f"[priors] updated priors -> {priors_path} ({len(out)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--date", required=False, default="1970-01-01")
    args = ap.parse_args()
    if args.update:
        update_priors(args.date)
