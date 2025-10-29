# src/etl/ingest_boxscores.py
import argparse, pathlib, pandas as pd
from src.utils.io import write_csv

def main(run_date: str):
    d = pd.DataFrame({
        "game_id": ["G1","G1","G1"],
        "player_id": ["P_A","P_B","P_C"],
        "team_id": ["T_H","T_H","T_A"],
        "opp_id": ["T_A","T_A","T_H"],
        "date": [run_date]*3,
        "minutes": [34.0, 28.0, 31.0],
        "PTS": [24, 16, 19],
        "REB": [8, 5, 7],
        "AST": [6, 4, 3],
    })
    out = pathlib.Path("data/parquet/boxscores")/f"box_{run_date}.csv"
    write_csv(d, out)
    print(f"[ingest] wrote {out} ({len(d)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    main(args.date)
