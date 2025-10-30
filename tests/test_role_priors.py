import numpy as np
import pandas as pd

from src.core.priors import build_player_priors, ROLE_WEIGHTS

def _df():
    # Two players, obvious role split; minutes identical to isolate role effects
    rows = [
        # starter player: higher role weighting on minutes (1.00) and neutral rate
        {"player_id": "starter_guy", "date": "2025-10-25", "minutes": 32, "PTS": 16, "REB": 6, "AST": 5, "role": "starter"},
        {"player_id": "starter_guy", "date": "2025-10-26", "minutes": 34, "PTS": 18, "REB": 7, "AST": 6, "role": "starter"},
        {"player_id": "starter_guy", "date": "2025-10-27", "minutes": 30, "PTS": 15, "REB": 5, "AST": 5, "role": "starter"},
        # bench player: same raw minutes/production but bench role should reduce minutes/rates slightly
        {"player_id": "bench_guy", "date": "2025-10-25", "minutes": 32, "PTS": 16, "REB": 6, "AST": 5, "role": "bench"},
        {"player_id": "bench_guy", "date": "2025-10-26", "minutes": 34, "PTS": 18, "REB": 7, "AST": 6, "role": "bench"},
        {"player_id": "bench_guy", "date": "2025-10-27", "minutes": 30, "PTS": 15, "REB": 5, "AST": 5, "role": "bench"},
    ]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df

def test_role_influences_priors_minutes_and_rates():
    pri = build_player_priors(_df(), lookback_games=3)
    s = pri["starter_guy"]
    b = pri["bench_guy"]

    # minutes mean should be scaled by role min_mult
    # since raw minutes are same, starter >= bench due to multipliers
    assert s["minutes_mean"] > b["minutes_mean"]

    # per-minute rates: bench rate_mult < starter rate_mult (~1.0)
    # base per-minute is identical; expect starter >= bench after role scaling
    for key in ["pts_per_min", "reb_per_min", "ast_per_min"]:
        assert s[key] >= b[key]

    # sanity: resolved roles present
    assert s["role"] == "starter"
    assert b["role"] == "bench"
