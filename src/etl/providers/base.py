from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import abc
import pandas as pd

@dataclass
class FetchContext:
    date: str            # YYYY-MM-DD
    season: str | None = None
    extra: Dict[str, Any] | None = None

class Provider(abc.ABC):
    """Uniform interface for any stats source."""
    @abc.abstractmethod
    def fetch_boxscores(self, ctx: FetchContext) -> pd.DataFrame:
        """
        Return columns at least:
        game_id, player_id, team_id, opp_id, minutes, PTS, REB, AST
        """
        raise NotImplementedError
