# espn_lookup.py
from __future__ import annotations

import datetime as dt
import re
from typing import Optional

import requests

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def _eq(a: str, b: str) -> bool:
    return _norm(a) == _norm(b)


def _fetch_scoreboard(date_yyyymmdd: str) -> dict:
    r = requests.get(ESPN_SCOREBOARD,
                     params={"dates": date_yyyymmdd},
                     timeout=20)
    r.raise_for_status()
    return r.json()


def find_game_id(away: str, home: str,
                 kalshi_close_dt: Optional[dt.datetime]) -> Optional[str]:
    """
    Find ESPN events[].id by matching normalized away/home on the scoreboard
    for kalshi_close_dt ± 2 days (robust to time zone and schedule drift).
    """
    if kalshi_close_dt:
        base = kalshi_close_dt.date()
    else:
        base = dt.date.today()

    candidates = [base + dt.timedelta(days=i) for i in (-2, -1, 0, 1, 2)]
    a_norm = _norm(away)
    h_norm = _norm(home)

    for d in candidates:
        sb = _fetch_scoreboard(d.strftime("%Y%m%d"))
        for ev in sb.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            comps = comp.get("competitors", []) or []
            if len(comps) < 2:
                continue
            t_away = next((c for c in comps if c.get("homeAway") == "away"),
                          comps[0])
            t_home = next((c for c in comps if c.get("homeAway") == "home"),
                          comps[-1])
            name_away = t_away.get("team", {}).get("displayName", "")
            name_home = t_home.get("team", {}).get("displayName", "")
            if _norm(name_away) == a_norm and _norm(name_home) == h_norm:
                return ev.get("id")
    return None
