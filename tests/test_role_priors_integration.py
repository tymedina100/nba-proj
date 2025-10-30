import os
import pandas as pd
from pathlib import Path

def test_update_priors_writes_role_and_multipliers(tmp_path, monkeypatch):
    # Arrange: fake project layout under tmp_path
    root = tmp_path
    box_dir = root / "data" / "parquet" / "boxscores"
    box_dir.mkdir(parents=True)

    # Three players with identical raw minutes/production so only role multipliers matter
    rows = [
        # starter_guy
        {"game_id": "G1","player_id":"starter_guy","minutes":32,"PTS":16,"REB":6,"AST":5,"role":"starter","date":"2025-10-25"},
        {"game_id": "G2","player_id":"starter_guy","minutes":34,"PTS":18,"REB":7,"AST":6,"role":"starter","date":"2025-10-26"},
        {"game_id": "G3","player_id":"starter_guy","minutes":30,"PTS":15,"REB":5,"AST":5,"role":"starter","date":"2025-10-27"},
        # sixth_guy
        {"game_id": "G1","player_id":"sixth_guy","minutes":32,"PTS":16,"REB":6,"AST":5,"role":"sixth","date":"2025-10-25"},
        {"game_id": "G2","player_id":"sixth_guy","minutes":34,"PTS":18,"REB":7,"AST":6,"role":"sixth","date":"2025-10-26"},
        {"game_id": "G3","player_id":"sixth_guy","minutes":30,"PTS":15,"REB":5,"AST":5,"role":"sixth","date":"2025-10-27"},
        # bench_guy
        {"game_id": "G1","player_id":"bench_guy","minutes":32,"PTS":16,"REB":6,"AST":5,"role":"bench","date":"2025-10-25"},
        {"game_id": "G2","player_id":"bench_guy","minutes":34,"PTS":18,"REB":7,"AST":6,"role":"bench","date":"2025-10-26"},
        {"game_id": "G3","player_id":"bench_guy","minutes":30,"PTS":15,"REB":5,"AST":5,"role":"bench","date":"2025-10-27"},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(box_dir / "box_2025-10-27.csv", index=False)

    # Act: chdir to tmp project, then run priors.update_priors
    os.chdir(root)
    from src.core import priors
    priors.update_priors("2025-10-27")

    # Assert: priors file exists & contains role/multipliers
    pri_path = Path("data/parquet/priors/priors_players.csv")
    assert pri_path.exists(), "priors_players.csv not written"
    pri = pd.read_csv(pri_path)

    # Only check PTS rows for clarity
    pts = pri[pri["stat"] == "PTS"].set_index("player_id")

    # Sanity: columns present
    for col in ["role","min_mult","rate_mult","alpha","beta"]:
        assert col in pts.columns

    # Role assignment persisted
    assert pts.loc["starter_guy","role"] == "starter"
    assert pts.loc["sixth_guy","role"] == "sixth"
    assert pts.loc["bench_guy","role"] == "bench"

    # Multipliers monotonic as defined (starter >= sixth >= bench for min_mult)
    assert pts.loc["starter_guy","min_mult"] >= pts.loc["sixth_guy","min_mult"] >= pts.loc["bench_guy","min_mult"]

    # Sixth man should have a slightly higher rate_mult than starter/bench per defaults
    assert pts.loc["sixth_guy","rate_mult"] >= pts.loc["starter_guy","rate_mult"]
    assert pts.loc["starter_guy","rate_mult"] >= pts.loc["bench_guy","rate_mult"]
