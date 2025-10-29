from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from .base import Provider, FetchContext

class CsvProvider(Provider):
    """
    Reads a local CSV by a path template (e.g., data/parquet/boxscores/box_{date}.csv)
    Optional 'rename' in cfg lets you map columns -> normalized names.
    """
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg

    def fetch_boxscores(self, ctx: FetchContext) -> pd.DataFrame:
        path_tpl = self.cfg["path"]
        path = Path(path_tpl.format(date=ctx.date))
        if not path.exists():
            raise SystemExit(f"[etl/csv] not found: {path}")
        df = pd.read_csv(path)
        # optional renames
        rename = self.cfg.get("rename", {})
        if rename:
            df = df.rename(columns=rename)
        return df
