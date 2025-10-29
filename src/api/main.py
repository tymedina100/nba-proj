# src/api/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import pandas as pd
from pathlib import Path

app = FastAPI()

class EdgeReq(BaseModel):
    player_id: str
    market: str
    side: str
    line: float
    decimal_odds: float
    date: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/edges")
def edges(reqs: List[EdgeReq]):
    date = reqs[0].date if reqs else "1970-01-01"
    edges_path = Path(f"runs/{date}/edges.csv")
    if not edges_path.exists():
        return {"error": f"edges not found for {date}. Run pricing first."}
    df = pd.read_csv(edges_path)
    out = []
    for r in reqs:
        m = df[(df.player_id==r.player_id)&(df.market==r.market)&(df.side==r.side)&(df.line==r.line)]
        if not m.empty:
            out.append(m.iloc[0].to_dict())
    return out
