from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import requests, pandas as pd
from .base import Provider, FetchContext

class HtmlTableProvider(Provider):
    """
    Fetch an HTML page and parse a table via pandas.read_html.
    Config:
      base_url, endpoint, table_index (default 0), rename (optional)
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def fetch_boxscores(self, ctx: FetchContext) -> pd.DataFrame:
        url = self.cfg["base_url"].rstrip("/") + "/" + self.cfg["endpoint"].format(date=ctx.date)
        r = requests.get(url, headers={"User-Agent": "nba-proj/0.1"}, timeout=30)
        r.raise_for_status()
        raw_dir = Path(f"data/raw/{ctx.date}")
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "source.html").write_text(r.text[:1_000_000], encoding="utf-8")
        tables = pd.read_html(r.text)
        idx = int(self.cfg.get("table_index", 0))
        df = tables[idx]
        rename = self.cfg.get("rename", {})
        if rename:
            df = df.rename(columns=rename)
        return df
