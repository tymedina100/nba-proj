# src/etl/providers/bref_boxscores.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from pathlib import Path
from io import StringIO
import re, time

import time, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import pandas as pd
import requests
from bs4 import BeautifulSoup


@dataclass
class FetchContext:
    date: str  # YYYY-MM-DD
    season: str | None = None


def _mmss_to_minutes(s: str) -> float:
    """Convert 'MM:SS' to float minutes. Handles NaN/None/'Did Not Play' etc."""
    if not isinstance(s, str):
        return 0.0
    if ":" not in s:
        return 0.0
    m, sec = s.split(":", 1)
    try:
        m_i = int(m)
        s_i = int(sec)
        return float(m_i) + (s_i / 60.0)
    except ValueError:
        return 0.0


def _slug(s: str) -> str:
    """Simple player_id slug: lowercase alnum with underscores."""
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _rows_from_basic_table(tb, team_id: str, game_id: str) -> list[dict]:
    """
    Parse one BRef 'box-XXX-game-basic' table using data-stat attributes.
    Returns list of dicts with game_id, player, minutes, PTS, REB, AST, team_id and a
    temporary 'section' flag to help derive roles.
    """
    out = []
    tbody = tb.find("tbody")
    if not tbody:
        return out

    in_starters_block = True  # flips to False after the 'Reserves' divider

    for tr in tbody.find_all("tr", recursive=False):
        # header-ish or divider rows have class thead
        if "thead" in (tr.get("class") or []):
            # Detect the “Reserves” switch; BRef puts the word in a <th>
            hdr = tr.find("th")
            if hdr and hdr.get_text(strip=True) == "Reserves":
                in_starters_block = False
            continue

        # Player cell is a <th data-stat="player">
        th = tr.find(["th"], attrs={"data-stat": "player"})
        if not th:
            continue
        player_name = (th.get_text(strip=True) or "")
        if not player_name or player_name in {"Team Totals", "Reserves", "Starters"}:
            continue

        # Minutes
        td_mp = tr.find("td", attrs={"data-stat": "mp"})
        mp_txt = td_mp.get_text(strip=True) if td_mp else "0:00"
        minutes = _mmss_to_minutes(mp_txt)

        # Numeric helper
        def _num(stat: str) -> float:
            td = tr.find("td", attrs={"data-stat": stat})
            if not td:
                return 0.0
            return float(pd.to_numeric(td.get_text(strip=True), errors="coerce") or 0)

        out.append({
            "game_id": game_id,
            "player": player_name,
            "team_id": team_id,
            "minutes": minutes,
            "PTS": _num("pts"),
            "REB": _num("trb"),
            "AST": _num("ast"),
            "section": "starters" if in_starters_block else "reserves",
        })
    return out


class BrefProvider:
    """
    Scrapes Basketball-Reference daily box score index and per-game basic box tables.
    Produces: game_id, player_id, team_id, opp_id, minutes, PTS, REB, AST, role
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.base_url = (cfg.get("base_url") or "https://www.basketball-reference.com").rstrip("/")
        self.endpoint = cfg.get("endpoint") or "/boxscores/?month={month}&day={day}&year={year}"
        self.max_retries = int(cfg.get("retries", 4))
        self.backoff = float(cfg.get("backoff", 1.25))
        self.raw_dump = bool(cfg.get("raw_dump", True))

        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "nba-proj/0.1 (+tymedina100)",
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "keep-alive",
        })

    def _date_parts(self, yyyy_mm_dd: str) -> tuple[int, int, int]:
        y, m, d = yyyy_mm_dd.split("-")
        return int(y), int(m), int(d)

    def _index_url(self, d: str) -> str:
        y, m, day = self._date_parts(d)
        ep = self.endpoint.format(year=y, month=m, day=day).lstrip("/")
        return f"{self.base_url}/{ep}"

    def _get(self, url: str, **kwargs) -> requests.Response:
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                r = self.s.get(url, timeout=30, **kwargs)
                if r.status_code == 200:
                    return r
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(self.backoff * (attempt + 1))
                    continue
                r.raise_for_status()
            except Exception as e:
                last_exc = e
                time.sleep(self.backoff * (attempt + 1))
        if last_exc:
            raise last_exc
        raise RuntimeError(f"failed to GET {url}")

    def _game_urls(self, date: str) -> List[str]:
        idx_url = self._index_url(date)
        r = self._get(idx_url)
        html = r.text

        if self.raw_dump:
            raw_dir = Path(f"data/raw/{date}")
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / "bref_index.html").write_text(html, encoding="utf-8")

        hrefs = set(re.findall(r'/boxscores/\d{9}[A-Z]{3}\.html', html))
        return [f"{self.base_url}{h}" for h in sorted(hrefs)]

    def _parse_game(self, date: str, game_url: str) -> pd.DataFrame:
        r = self._get(game_url)
        html = r.text
        game_id = re.search(r'/boxscores/(\d{9}[A-Z]{3})\.html', game_url).group(1)

        if self.raw_dump:
            raw_dir = Path(f"data/raw/{date}")
            raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{game_id}.html").write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "lxml")

        # Basic player box tables have ids like 'box-PHX-game-basic'
        tables = soup.find_all("table", id=re.compile(r"^box-[A-Z]{3}-game-basic$"))
        frames: list[pd.DataFrame] = []

        for tb in tables:
            m = re.search(r"^box-([A-Z]{3})-game-basic$", tb.get("id", ""))
            if not m:
                continue
            team_id = m.group(1)
            rows = _rows_from_basic_table(tb, team_id, game_id)
            if rows:
                frames.append(pd.DataFrame(rows))

        if not frames:
            return pd.DataFrame(columns=["game_id","player_id","team_id","opp_id","minutes","PTS","REB","AST","role"])

        base = pd.concat(frames, ignore_index=True)

        # Role assignment: starters direct from section; among reserves, max minutes = sixth
        base["is_starter"] = base["section"].eq("starters")

        def assign_roles(group: pd.DataFrame) -> pd.Series:
            roles = pd.Series(index=group.index, dtype=object)
            roles.loc[group["is_starter"]] = "starter"
            bench_idx = group.index[~group["is_starter"]]
            if len(bench_idx) > 0:
                six_idx = group.loc[bench_idx, "minutes"].astype(float).idxmax()
                roles.loc[six_idx] = "sixth"
                roles.loc[bench_idx.difference([six_idx])] = "bench"
            return roles

        base["role"] = base.groupby(["game_id", "team_id"], group_keys=False).apply(assign_roles)
        base = base.drop(columns=["section", "is_starter"])

        # Add opp_id by pairing unique team entries per game
        teams = base[["game_id", "team_id"]].drop_duplicates()
        opp = teams.merge(teams, on="game_id")
        opp = opp[opp["team_id_x"] != opp["team_id_y"]].rename(
            columns={"team_id_x": "team_id", "team_id_y": "opp_id"}
        )
        out = base.merge(opp, on=["game_id", "team_id"], how="left")

        # Finalize IDs
        out["player_id"] = out["player"].apply(_slug)
        out = out[["game_id", "player_id", "team_id", "opp_id", "minutes", "PTS", "REB", "AST", "role"]]
        return out

    def fetch_boxscores(self, ctx: FetchContext) -> pd.DataFrame:
        urls = self._game_urls(ctx.date)
        if not urls:
            return pd.DataFrame(columns=["game_id","player_id","team_id","opp_id","minutes","PTS","REB","AST","role"])
        parts = [self._parse_game(ctx.date, u) for u in urls]
        if not parts:
            return pd.DataFrame(columns=["game_id","player_id","team_id","opp_id","minutes","PTS","REB","AST","role"])
        df = pd.concat(parts, ignore_index=True)
        return df
