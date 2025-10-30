from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any, Dict, Callable
import pandas as pd
import yaml

from .providers.base import FetchContext, Provider
from .providers.csv_provider import CsvProvider
from .providers.json_api import JsonApiProvider
from .providers.html_table import HtmlTableProvider
from .providers.bref_boxscores import BrefProvider

def _load_cfg() -> Dict[str, Any]:
    with open("config/providers.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _build_provider(name: str, pcfg: Dict[str, Any]) -> Provider:
    kind = pcfg["kind"]
    if kind == "csv":
        return CsvProvider(pcfg)
    if kind == "json_api":
        def transform(payload, _ctx):
            df = pd.DataFrame(payload["rows"])
            return df
        return JsonApiProvider(pcfg, transform)
    if kind == "html_table":
        return HtmlTableProvider(pcfg)
    if kind == "bref":                       # <-- add this
        return BrefProvider(pcfg)
    raise SystemExit(f"[fetch_daily] unknown provider kind: {kind}")


def _normalize(df: pd.DataFrame, date: str) -> pd.DataFrame:
    # Expect at least these columns (rename via provider if needed)
    need = ["game_id","player_id","team_id","opp_id","minutes","PTS","REB","AST"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"[normalize] missing columns: {missing}")
    out = pd.DataFrame({
        "game_id":  df["game_id"].astype(str),
        "player_id":df["player_id"].astype(str),
        "team_id":  df["team_id"].astype(str),
        "opp_id":   df["opp_id"].astype(str),
        "minutes":  pd.to_numeric(df["minutes"], errors="coerce").fillna(0.0),
        "PTS":      pd.to_numeric(df["PTS"], errors="coerce").fillna(0.0),
        "REB":      pd.to_numeric(df["REB"], errors="coerce").fillna(0.0),
        "AST":      pd.to_numeric(df["AST"], errors="coerce").fillna(0.0),
    })
    out["date"] = date
    return out[["game_id","player_id","team_id","opp_id","date","minutes","PTS","REB","AST"]]

def main(run_date: str, provider_name: str):
    cfg = _load_cfg()
    pcfg = cfg["providers"][provider_name]
    ctx = FetchContext(date=run_date, season=cfg.get("season"))

    provider = _build_provider(provider_name, pcfg)
    df_raw = provider.fetch_boxscores(ctx)
    df_norm = _normalize(df_raw, run_date)

    out = Path(f"data/parquet/boxscores/box_{run_date}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df_norm.to_csv(out, index=False)
    print(f"[fetch_daily] wrote {out} ({len(df_norm)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--provider", required=True, help="key in config/providers.yaml")
    args = ap.parse_args()
    main(args.date, args.provider)
