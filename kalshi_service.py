# kalshi_service.py
import re
from datetime import datetime
from difflib import get_close_matches
from typing import Dict, List, Optional, Tuple

import requests


class KalshiService:
    """
    Unauthenticated access to Kalshi NFL markets.

    Output per event:
      - ONE primary Winner market row: `winner_primary`
        • subject_team: which team the "YES" applies to (HOME preferred)
        • yes_bid / yes_ask (for that team)
        • no_bid / no_ask (for the opposite outcome; complements using the *other* team if available)
        • ticker
      - open_interest_sum / volume_24h_sum (event aggregates)
      - all_contracts (raw normalized)
    """

    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    SERIES_TICKER_GAME = "KXNFLGAME"

    TEAM_MAP: Dict[str, str] = {
        "ARI": "Arizona Cardinals",
        "ATL": "Atlanta Falcons",
        "BAL": "Baltimore Ravens",
        "BUF": "Buffalo Bills",
        "CAR": "Carolina Panthers",
        "CHI": "Chicago Bears",
        "CIN": "Cincinnati Bengals",
        "CLE": "Cleveland Browns",
        "DAL": "Dallas Cowboys",
        "DEN": "Denver Broncos",
        "DET": "Detroit Lions",
        "GB": "Green Bay Packers",
        "HOU": "Houston Texans",
        "IND": "Indianapolis Colts",
        "JAX": "Jacksonville Jaguars",
        "KC": "Kansas City Chiefs",
        "LAC": "Los Angeles Chargers",
        "LAR": "Los Angeles Rams",
        "LV": "Las Vegas Raiders",
        "MIA": "Miami Dolphins",
        "MIN": "Minnesota Vikings",
        "NE": "New England Patriots",
        "NO": "New Orleans Saints",
        "NYG": "New York Giants",
        "NYJ": "New York Jets",
        "PHI": "Philadelphia Eagles",
        "PIT": "Pittsburgh Steelers",
        "SEA": "Seattle Seahawks",
        "SF": "San Francisco 49ers",
        "TB": "Tampa Bay Buccaneers",
        "TEN": "Tennessee Titans",
        "WAS": "Washington Commanders",
    }
    TEAM_ABBRS = set(TEAM_MAP.keys())
    TEAM_NAMES = list(TEAM_MAP.values())

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ---------------- HTTP ----------------

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        url = f"{self.BASE_URL}{path}"
        r = self.session.get(url, params=params or {}, timeout=20)
        r.raise_for_status()
        return r.json()

    # ---------------- Utilities ----------------

    @staticmethod
    def _cents_to_dollars(v: Optional[float]) -> Optional[float]:
        try:
            return round(float(v) / 100.0, 2) if v is not None else None
        except Exception:
            return None

    @staticmethod
    def _parse_close_time(m: Dict) -> Optional[datetime]:
        ts = m.get("close_time")
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None

    @classmethod
    def _normalize_team_name(cls, s: str) -> Optional[str]:
        raw = (s or "").strip()
        if not raw:
            return None
        t = raw.lower()
        # abbr
        for ab, full in cls.TEAM_MAP.items():
            if t == ab.lower():
                return full
        # contains city or nickname
        for full in cls.TEAM_NAMES:
            if " " in full:
                city, nick = full.split(" ", 1)
                if city.lower() in t or nick.lower() in t:
                    return full
        # close match
        cand = get_close_matches(raw, cls.TEAM_NAMES, n=1, cutoff=0.6)
        return cand[0] if cand else None

    @classmethod
    def _extract_event_name_from_text(
            cls, markets: List[Dict]) -> Optional[Tuple[str, str, str]]:
        for m in markets:
            head = (m.get("title") or "").split(":", 1)[0]
            sub = (m.get("subtitle") or "")
            text = " ".join([head, sub])
            mobj = re.search(r"(.+?)\s+at\s+(.+)", text, flags=re.I)
            if not mobj:
                continue
            away_raw, home_raw = mobj.group(1), mobj.group(2)
            away = cls._normalize_team_name(away_raw) or away_raw.strip()
            home = cls._normalize_team_name(home_raw) or home_raw.strip()
            return away, home, f"{away} at {home}"
        return None

    @classmethod
    def _decode_home_away_from_event_ticker(
            cls, event_ticker: str) -> Optional[Tuple[str, str]]:
        if not event_ticker:
            return None
        codes = re.findall(r"[A-Z]{2,3}", event_ticker.upper())
        valid = [c for c in codes if c in cls.TEAM_ABBRS]
        if len(valid) >= 2:
            away3, home3 = valid[-2], valid[-1]
            return cls.TEAM_MAP[away3], cls.TEAM_MAP[home3]
        return None

    def _subject_from_ticker_suffix(self,
                                    ticker: Optional[str]) -> Optional[str]:
        if not ticker:
            return None
        m = re.search(r"-([A-Z]{2,3})$", ticker.upper())
        if not m:
            return None
        return self.TEAM_MAP.get(m.group(1))

    def _subject_from_text(self, title: str, subtitle: str, away_name: str,
                           home_name: str) -> Optional[str]:
        text = " ".join(filter(None, [title, subtitle])).lower()
        scores = {away_name: 0, home_name: 0}
        for team in (away_name, home_name):
            for tok in team.lower().split():
                if tok and tok in text:
                    scores[team] += 1
        if scores[away_name] == scores[home_name] == 0:
            return None
        return away_name if scores[away_name] >= scores[
            home_name] else home_name

    # ---------------- Fetch & combine ----------------

    def get_nfl_game_markets(self,
                             limit: int = 500,
                             cursor: Optional[str] = None) -> Dict:
        params = {
            "series_ticker": self.SERIES_TICKER_GAME,
            "status": "open",
            "limit": max(1, min(limit, 1000))
        }
        if cursor:
            params["cursor"] = cursor
        data = self._get("/markets", params=params)
        return {
            "markets": data.get("markets", []),
            "cursor": data.get("cursor")
        }

    def get_all_open_games(self, max_pages: int = 20) -> List[Dict]:
        out, cursor, pages = [], None, 0
        while pages < max_pages:
            page = self.get_nfl_game_markets(limit=500, cursor=cursor)
            out.extend(page["markets"])
            cursor = page["cursor"]
            pages += 1
            if not cursor:
                break
        return out

    def group_by_event(self, markets: List[Dict]) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {}
        for m in markets:
            et = m.get("event_ticker") or "UNKNOWN_EVENT"
            grouped.setdefault(et, []).append(m)
        return grouped

    def normalize_market(self, m: Dict) -> Dict:
        return {
            "ticker": m.get("ticker"),
            "event_ticker": m.get("event_ticker"),
            "series_ticker": m.get("series_ticker"),
            "title": m.get("title"),
            "subtitle": m.get("subtitle"),
            "market_type": m.get("market_type"),
            "close_time": m.get("close_time"),
            "close_dt": self._parse_close_time(m),
            "yes_bid": self._cents_to_dollars(m.get("yes_bid")),
            "yes_ask": self._cents_to_dollars(m.get("yes_ask")),
            "open_interest": m.get("open_interest"),
            "volume_24h": m.get("volume_24h"),
        }

    def combine_event_contracts(self, event_markets: List[Dict]) -> Dict:
        """
        Build a combined record with ONE primary Winner market (HOME preferred).
        We compute the NO side using the *opposite* team when possible.
        """
        em = [self.normalize_market(m) for m in event_markets]
        et = em[0].get("event_ticker")

        names = self._decode_home_away_from_event_ticker(et or "")
        if names:
            away_name, home_name = names
            pretty = f"{away_name} at {home_name}"
        else:
            parsed = self._extract_event_name_from_text(em)
            if parsed:
                away_name, home_name, pretty = parsed
            else:
                away_name, home_name, pretty = "Away", "Home", (
                    em[0].get("title") or et or "Unknown matchup")

        away_win, home_win = None, None
        for m in em:
            title = m.get("title") or ""
            if "winner" not in title.lower():
                continue
            subject = self._subject_from_ticker_suffix(m.get("ticker"))
            if subject is None:
                subject = self._subject_from_text(title,
                                                  m.get("subtitle") or "",
                                                  away_name, home_name)
            if subject == away_name:
                away_win = m
            elif subject == home_name:
                home_win = m

        # choose primary (home preferred), keep secondary for complements
        primary = home_win or away_win
        secondary = away_win if primary is home_win else home_win

        # fabricate safe empty
        if primary is None:
            primary = {
                "yes_bid": None,
                "yes_ask": None,
                "ticker": None,
                "title": "",
                "subtitle": ""
            }

        subject_team = home_name if primary is home_win else (
            away_name if primary is away_win else home_name)

        yes_bid = primary.get("yes_bid")
        yes_ask = primary.get("yes_ask")

        # Best-effort NO price: use opposite team’s ask/bid first; fallback to own complements.
        def comp(v: Optional[float]) -> Optional[float]:
            return round(1 - v, 2) if v is not None else None

        sec_yes_bid = secondary.get("yes_bid") if secondary else None
        sec_yes_ask = secondary.get("yes_ask") if secondary else None

        no_bid = comp(sec_yes_ask) if sec_yes_ask is not None else comp(
            yes_ask)
        no_ask = comp(sec_yes_bid) if sec_yes_bid is not None else comp(
            yes_bid)

        close_dt = min([x["close_dt"] for x in em if x.get("close_dt")],
                       default=None)
        oi_sum = sum([x.get("open_interest") or 0 for x in em])
        vol_sum = sum([x.get("volume_24h") or 0 for x in em])

        return {
            "event_ticker": et,
            "pretty_event": pretty,
            "away_team": away_name,
            "home_team": home_name,
            "close_dt": close_dt,
            "open_interest_sum": oi_sum,
            "volume_24h_sum": vol_sum,
            "winner_primary": {
                "label": f"{subject_team} — Winner?",
                "subject_team": subject_team,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "no_bid": no_bid,
                "no_ask": no_ask,
                "ticker": primary.get("ticker"),
            },
            "all_contracts": em,
        }

    def fetch_and_group_open_games(self) -> List[Dict]:
        all_markets = self.get_all_open_games()
        groups = self.group_by_event(all_markets)
        combined: List[Dict] = []
        for _, markets in groups.items():
            combined.append(self.combine_event_contracts(markets))
        combined.sort(key=lambda g: (g["close_dt"] or datetime.max))
        return combined

    # ---------------- Historical Data ----------------

    def get_market_candlesticks(
            self,
            series_ticker: str,
            ticker: str,
            period_interval: int = 60,
            days_back: int = 7) -> Optional[List[Dict]]:
        """
        Fetch historical price data (OHLC candlesticks).
        
        Args:
            series_ticker: Series ticker (e.g., 'KXNFLGAME')
            ticker: Market ticker
            period_interval: Time period in minutes (1, 60, or 1440)
            days_back: How many days of history to fetch
        
        Returns:
            List of candlestick dicts with simplified structure or None on error
        """
        try:
            import time
            
            # Calculate timestamps
            end_ts = int(time.time())
            start_ts = end_ts - (days_back * 24 * 60 * 60)
            
            path = f"/series/{series_ticker}/markets/{ticker}/candlesticks"
            params = {
                "period_interval": period_interval,
                "start_ts": start_ts,
                "end_ts": end_ts
            }
            print(f"[DEBUG] Fetching candlesticks: {self.BASE_URL}{path} with params {params}")
            data = self._get(path, params=params)
            candlesticks_raw = data.get("candlesticks", [])
            print(f"[DEBUG] Got {len(candlesticks_raw)} candlesticks")
            
            # Transform to simplified structure
            candlesticks = []
            for candle in candlesticks_raw:
                # Use the 'price' object which contains the market price
                price_data = candle.get("price", {})
                candlesticks.append({
                    "timestamp": datetime.fromtimestamp(candle.get("end_period_ts", 0), tz=datetime.now().astimezone().tzinfo).isoformat(),
                    "open": self._cents_to_dollars(price_data.get("open")),
                    "high": self._cents_to_dollars(price_data.get("high")),
                    "low": self._cents_to_dollars(price_data.get("low")),
                    "close": self._cents_to_dollars(price_data.get("close")),
                    "volume": candle.get("volume", 0),
                })
            
            return candlesticks
        except Exception as e:
            print(f"[ERROR] Failed to fetch candlesticks for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_market_orderbook(self, ticker: str) -> Optional[Dict]:
        """
        Fetch current orderbook for a market.
        
        Args:
            ticker: Market ticker
        
        Returns:
            Orderbook dict or None on error
        """
        try:
            path = f"/markets/{ticker}/orderbook"
            print(f"[DEBUG] Fetching orderbook: {self.BASE_URL}{path}")
            data = self._get(path, params={})
            
            # Convert cents to dollars for all orders
            if "yes" in data:
                for order in data["yes"]:
                    order["price"] = self._cents_to_dollars(order.get("price"))
            if "no" in data:
                for order in data["no"]:
                    order["price"] = self._cents_to_dollars(order.get("price"))
            
            print(f"[DEBUG] Got orderbook with {len(data.get('yes', []))} YES orders and {len(data.get('no', []))} NO orders")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to fetch orderbook for {ticker}: {e}")
            return None
