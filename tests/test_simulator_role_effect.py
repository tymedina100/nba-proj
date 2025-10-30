import os
import pandas as pd
from pathlib import Path

def test_simulator_reflects_role_effects(tmp_path):
    root = tmp_path
    pri_dir = root / "data" / "parquet" / "priors"
    pri_dir.mkdir(parents=True)

    # Small priors table for 3 players, stat=PTS only, with different role multipliers
    # Keep alpha/beta identical so differences come from min_mult/rate_mult + minutes draw
    pri = pd.DataFrame([
        {"player_id":"starter_guy","stat":"PTS","alpha":50.0,"beta":1800.0,"minutes_scale":36.0,"n_games":10,"last_update":"2025-10-27","role":"starter","min_mult":1.00,"rate_mult":1.00},
        {"player_id":"sixth_guy",  "stat":"PTS","alpha":50.0,"beta":1800.0,"minutes_scale":36.0,"n_games":10,"last_update":"2025-10-27","role":"sixth","min_mult":0.88,"rate_mult":1.02},
        {"player_id":"bench_guy",  "stat":"PTS","alpha":50.0,"beta":1800.0,"minutes_scale":36.0,"n_games":10,"last_update":"2025-10-27","role":"bench","min_mult":0.70,"rate_mult":0.98},
    ])
    pri.to_csv(pri_dir / "priors_players.csv", index=False)

    # Optional: minutes overrides to keep baseline equal (same mean/sd before multipliers)
    ov = pd.DataFrame([
        {"player_id":"starter_guy","min_proj":30.0,"min_sd":0.0},
        {"player_id":"sixth_guy","min_proj":30.0,"min_sd":0.0},
        {"player_id":"bench_guy","min_proj":30.0,"min_sd":0.0},
    ])

    os.chdir(root)
    from src.core import simulator
    simulator.main(run_date="2025-10-27", draws=5000)

    out = pd.read_csv(Path("runs/2025-10-27/predictions.csv"))
    pts = out[out["stat"] == "PTS"].set_index("player_id")

    # With same base priors & minutes, ordering should follow multipliers:
    # starter ≳ sixth > bench
    assert pts.loc["starter_guy", "mean"] >= pts.loc["sixth_guy", "mean"]
    assert pts.loc["sixth_guy", "mean"] > pts.loc["bench_guy", "mean"]
