from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
import time, json, requests, pandas as pd
from .base import Provider, FetchContext

def _session(headers: Dict[str, str] | None = None) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "nba-proj/0.1 (+tymedina100)",
        "Accept": "application/json",
        "Connection": "keep-alive",
    })
    if headers:
        s.headers.update(headers)
    return s

class JsonApiProvider(Provider):
    """
    Generic JSON provider. You supply a transform(payload, ctx) -> DataFrame.
    Config:
      base_url: str
      endpoint: str (can use {date})
      params: dict (optional)
      headers: dict (optional)
    """
    def __init__(self, cfg: Dict[str, Any], transform):
        self.cfg = cfg
        self.transform = transform
        self.s = _session(cfg.get("headers"))

    def fetch_boxscores(self, ctx: FetchContext) -> pd.DataFrame:
        url = self.cfg["base_url"].rstrip("/") + "/" + self.cfg["endpoint"].format(date=ctx.date)
        params = (self.cfg.get("params") or {}).copy()

        raw_dir = Path(f"data/raw/{ctx.date}")
        raw_dir.mkdir(parents=True, exist_ok=True)

        for attempt in range(4):
            r = self.s.get(url, params=params, timeout=30)
            if r.status_code == 200:
                payload = r.json()
                (raw_dir / "boxscores.json").write_text(json.dumps(payload)[:1_000_000], encoding="utf-8")
                return self.transform(payload, ctx)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            raise SystemExit(f"[etl/json] HTTP {r.status_code} @ {url} -> {r.text[:300]}")
        raise SystemExit("[etl/json] exhausted retries")
