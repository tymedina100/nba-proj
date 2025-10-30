from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import json
import pandas as pd

app = FastAPI(title="nba-proj API", version="0.1.0")

class Edge(BaseModel):
    date: str
    player_id: str
    market: str
    side: str
    line: float
    decimal_odds: float
    fair_p: float
    fair_odds: float
    ev: float
    mean: float
    median: float
    p10: float
    p90: float
    sigma: float
    corr_group: str | None = None
    corr_reason: str | None = None
    rationale: str | None = None

def _edges_path(date: str) -> Path:
    p = Path(f"runs/{date}/edges.csv")
    if not p.exists():
        raise HTTPException(404, f"edges not found for {date}")
    return p

def _latest_date() -> str:
    runs = sorted([p.name for p in Path("runs").glob("*") if p.is_dir()])
    if not runs:
        raise HTTPException(404, "no runs yet")
    return runs[-1]

@app.get("/edges", response_model=list[Edge])
def get_edges(
    date: Optional[str] = Query(None, description="YYYY-MM-DD (defaults to latest run)"),
    min_ev: float = Query(-1.0, description="only rows with ev >= min_ev"),
    top: int = Query(50, ge=1, le=500),
    market: Optional[str] = Query(None, description="filter by market, e.g. PTS/REB/AST"),
    player_id: Optional[str] = Query(None, description="filter by player_id"),
    pretty: bool = Query(False, description="return pretty-printed JSON"),
):
    date = date or _latest_date()
    df = pd.read_csv(_edges_path(date))
    if market:
        df = df[df["market"] == market]
    if player_id:
        df = df[df["player_id"] == player_id]
    df = df[df["ev"] >= min_ev].sort_values("ev", ascending=False).head(top)
    records = df.to_dict(orient="records")
    if pretty:
        return PlainTextResponse(json.dumps(records, indent=2) + "\n", media_type="application/json")
    return records