import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

class KalshiService:
    """Service for interacting with the unauthenticated Kalshi API."""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    MARKET_CATEGORY_MAP = {
        "GAME": "Games",
        "PASSYDS": "Passing Yards",
        "RSHYDS": "Rushing Yards",
        "RECYDS": "Receiving Yards",
        "ANYTD": "Anytime Touchdowns",
        "PASSTD": "Passing Touchdowns",
        "RSHTD": "Rushing Touchdowns",
        "RECTD": "Receiving Touchdowns",
        "SB": "Super Bowl",
        "MVPNFL": "NFL MVP",
        "PLAYOFF": "Playoffs",
        "MVE": "Same Game Parlays"
    }
    
    TEAM_NAMES = {
        "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
        "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
        "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
        "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
        "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
        "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
        "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
        "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
        "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
        "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
        "TEN": "Tennessee Titans", "WAS": "Washington Commanders"
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_nfl_markets(self, limit: int = 100, cursor: Optional[str] = None) -> Dict:
        """
        Fetch Professional Football Game markets from Kalshi API.
        
        Args:
            limit: Number of markets to fetch from API
            cursor: Pagination cursor for next page
            
        Returns:
            Dictionary containing game markets and cursor for next page
        """
        try:
            params = {
                "limit": limit,
                "series_ticker": "KXNFLGAME"  # Professional Football Game series
            }
            
            if cursor:
                params["cursor"] = cursor
            
            response = self.session.get(
                f"{self.BASE_URL}/markets",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            markets = data.get("markets", [])
            
            return {
                "markets": markets,
                "cursor": data.get("cursor")
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NFL markets: {e}")
            return {"markets": [], "cursor": None}
    
    def get_market_details(self, ticker: str) -> Optional[Dict]:
        """
        Get detailed information for a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Market details dictionary or None
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets/{ticker}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("market")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching market details for {ticker}: {e}")
            return None
    
    def get_market_history(self, ticker: str, limit: int = 100) -> List[Dict]:
        """
        Get historical trades for a market.
        
        Args:
            ticker: Market ticker symbol
            limit: Number of historical trades to fetch
            
        Returns:
            List of historical trade data
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets/{ticker}/history",
                params={"limit": limit},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("history", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching market history for {ticker}: {e}")
            return []
    
    def get_orderbook(self, ticker: str, depth: int = 10) -> Optional[Dict]:
        """
        Get current orderbook for a market.
        
        Args:
            ticker: Market ticker symbol
            depth: Depth of orderbook to fetch
            
        Returns:
            Orderbook dictionary with yes and no orders
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets/{ticker}/orderbook",
                params={"depth": depth},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("orderbook")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orderbook for {ticker}: {e}")
            return None
    
    def search_markets(self, query: str, limit: int = 100) -> List[Dict]:
        """
        Search for markets matching a query.
        
        Args:
            query: Search query string
            limit: Number of results to return
            
        Returns:
            List of matching markets
        """
        data = self.get_nfl_markets(limit=limit)
        markets = data.get("markets", [])
        
        if not query:
            return markets
        
        query_lower = query.lower()
        return [
            m for m in markets
            if query_lower in m.get("title", "").lower() or
               query_lower in m.get("event_ticker", "").lower() or
               query_lower in m.get("subtitle", "").lower()
        ]
    
    def group_markets_by_event(self, markets: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group markets by their event ticker.
        
        Args:
            markets: List of market dictionaries
            
        Returns:
            Dictionary mapping event tickers to lists of markets
        """
        grouped = {}
        for market in markets:
            event_ticker = market.get("event_ticker", "Unknown")
            if event_ticker not in grouped:
                grouped[event_ticker] = []
            grouped[event_ticker].append(market)
        
        return grouped
    
    def format_market_title(self, market: Dict) -> str:
        """Format a readable market title."""
        title = market.get("title", market.get("ticker", "Unknown Market"))
        return title
    
    def get_market_probability(self, market: Dict) -> float:
        """Get the current probability (last price) for a market."""
        return market.get("yes_bid", 0) / 100.0 if market.get("yes_bid") else 0.0
    
    def parse_event_ticker(self, event_ticker: str) -> Tuple[str, str, str, str]:
        """
        Parse event ticker to extract market type, date, and teams.
        Format: KXNFL{TYPE}-{DATE}{TEAM1}{TEAM2}
        
        Returns:
            (market_type, date, team1, team2)
        """
        if not event_ticker or not event_ticker.startswith("KXNFL"):
            return ("Unknown", "", "", "")
        
        if event_ticker.startswith("KXMVENFL"):
            return ("MVE", "", "", "")
        
        parts = event_ticker.split('-')
        if len(parts) < 2:
            return ("Unknown", "", "", "")
        
        type_part = parts[0].replace("KXNFL", "")
        
        suffix = parts[1]
        
        date_match = re.match(r'(\d{8})', suffix)
        if not date_match:
            return (type_part, "", "", "")
        
        date = date_match.group(1)
        team_suffix = suffix[8:]
        
        team1 = ""
        team2 = ""
        for team_code in sorted(self.TEAM_NAMES.keys(), key=len, reverse=True):
            if team_suffix.endswith(team_code):
                team2 = team_code
                team_suffix = team_suffix[:-len(team_code)]
                break
        
        if team_suffix:
            for team_code in sorted(self.TEAM_NAMES.keys(), key=len, reverse=True):
                if team_suffix == team_code:
                    team1 = team_code
                    break
        
        return (type_part, date, team1, team2)
    
    def get_category_name(self, market_type: str) -> str:
        """Get human-readable category name from market type code."""
        return self.MARKET_CATEGORY_MAP.get(market_type, "Other Markets")
    
    def get_team_name(self, team_code: str) -> str:
        """Get full team name from team code."""
        return self.TEAM_NAMES.get(team_code, team_code)
    
    def expand_team_abbreviations(self, text: str) -> str:
        """
        Replace abbreviated team names in text with full names.
        Handles cases like "Los Angeles C " → "Los Angeles Chargers "
        Only replaces when followed by space/comma/punctuation to avoid duplicates.
        """
        replacements = {
            r'\bLos Angeles C\b': 'Los Angeles Chargers',
            r'\bLos Angeles R\b': 'Los Angeles Rams',
            r'\bNew York G\b': 'New York Giants',
            r'\bNew York J\b': 'New York Jets'
        }
        
        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def parse_display_name(self, market: Dict) -> str:
        """
        Generate intuitive display name from market data.
        Uses title/subtitle from API, or parses ticker if needed.
        """
        title = market.get("title", "").strip()
        subtitle = market.get("subtitle", "").strip()
        
        if title and title != "":
            title = self.expand_team_abbreviations(title)
            if subtitle and subtitle != "":
                subtitle = self.expand_team_abbreviations(subtitle)
                return f"{title}: {subtitle}"
            return title
        
        ticker = market.get("ticker", "")
        if not ticker:
            return "Unknown Market"
        
        parts = ticker.split('-')
        if len(parts) >= 3:
            player_threshold = parts[-1]
            
            player_match = re.match(r'([A-Z]+)([A-Z][a-z]+)(\d+)-(\d+)', player_threshold)
            if player_match:
                team, last_name, jersey, threshold = player_match.groups()
                first_initial = player_threshold[len(team)]
                return f"{first_initial}. {last_name} #{jersey}: {threshold}+ yards"
        
        return ticker
    
    def normalize_market(self, market: Dict) -> Dict:
        """
        Normalize market data with calculated fields for display.
        Adds: category, matchup, display_name, display_probability, display_volume
        """
        event_ticker = market.get("event_ticker", "")
        market_type, date, team1_code, team2_code = self.parse_event_ticker(event_ticker)
        
        category = self.get_category_name(market_type)
        
        matchup = "General"
        if team1_code and team2_code:
            team1 = self.get_team_name(team1_code)
            team2 = self.get_team_name(team2_code)
            matchup = f"{team1} @ {team2}"
        
        yes_bid = market.get("yes_bid", 0)
        last_price = market.get("last_price", 0)
        mid_price = market.get("mid_price", 0)
        
        price = yes_bid if yes_bid > 0 else (last_price if last_price > 0 else mid_price)
        probability = price / 100.0
        
        volume = market.get("volume", market.get("volume_24h", market.get("liquidity", 0)))
        
        display_name = self.parse_display_name(market)
        
        normalized = market.copy()
        normalized.update({
            "category": category,
            "matchup": matchup,
            "display_name": display_name,
            "display_probability": probability,
            "display_probability_pct": f"{probability * 100:.0f}%",
            "display_volume": volume,
            "market_type_code": market_type
        })
        
        return normalized
    
    def combine_market_pair(self, markets: List[Dict]) -> Optional[Dict]:
        """
        Combine two opposing markets (same game, different teams) into one combined market.
        
        Args:
            markets: List of 2 markets representing opposite sides of the same game
            
        Returns:
            Combined market dictionary with both team contracts, or None if can't combine
        """
        if len(markets) != 2:
            return None
        
        m1, m2 = markets
        ticker1 = m1.get("ticker", "")
        ticker2 = m2.get("ticker", "")
        
        team1_code = ticker1.split('-')[-1] if '-' in ticker1 else ""
        team2_code = ticker2.split('-')[-1] if '-' in ticker2 else ""
        
        if not team1_code or not team2_code:
            return None
        
        team1_name = self.get_team_name(team1_code)
        team2_name = self.get_team_name(team2_code)
        
        event_ticker = m1.get("event_ticker", "")
        market_type, date, away_code, home_code = self.parse_event_ticker(event_ticker)
        
        away_market = m1 if team1_code == away_code else m2
        home_market = m2 if team1_code == away_code else m1
        away_name = self.get_team_name(away_code) if away_code else team1_name
        home_name = self.get_team_name(home_code) if home_code else team2_name
        
        away_prob = self._get_probability(away_market)
        home_prob = self._get_probability(home_market)
        
        combined_volume = max(
            away_market.get("volume", 0),
            home_market.get("volume", 0)
        )
        if combined_volume == 0:
            combined_volume = max(
                away_market.get("volume_24h", 0),
                home_market.get("volume_24h", 0)
            )
        
        combined = {
            "event_ticker": event_ticker,
            "category": self.get_category_name(market_type),
            "matchup": f"{away_name} @ {home_name}",
            "display_name": m1.get("title", ""),
            "away_team": away_name,
            "away_team_code": away_code,
            "away_ticker": away_market.get("ticker", ""),
            "away_probability": away_prob,
            "away_probability_pct": f"{away_prob * 100:.0f}%",
            "home_team": home_name,
            "home_team_code": home_code,
            "home_ticker": home_market.get("ticker", ""),
            "home_probability": home_prob,
            "home_probability_pct": f"{home_prob * 100:.0f}%",
            "display_volume": combined_volume,
            "market_type_code": market_type,
            "away_contract": away_market,
            "home_contract": home_market
        }
        
        return combined
    
    def _get_probability(self, market: Dict) -> float:
        """Helper to get probability from market with fallback chain."""
        yes_bid = market.get("yes_bid", 0)
        last_price = market.get("last_price", 0)
        mid_price = market.get("mid_price", 0)
        
        price = yes_bid if yes_bid > 0 else (last_price if last_price > 0 else mid_price)
        return price / 100.0
    
    def get_normalized_markets(self, limit: int = 100, cursor: Optional[str] = None) -> Dict:
        """
        Fetch and normalize NFL markets, combining paired markets into single rows.
        
        Returns:
            Dictionary with combined markets and cursor
        """
        data = self.get_nfl_markets(limit=limit, cursor=cursor)
        markets = data.get("markets", [])
        
        grouped = self.group_markets_by_event(markets)
        
        combined_markets = []
        for event_ticker, event_markets in grouped.items():
            combined = self.combine_market_pair(event_markets)
            if combined:
                combined_markets.append(combined)
            else:
                for m in event_markets:
                    combined_markets.append(self.normalize_market(m))
        
        return {
            "markets": combined_markets,
            "cursor": data.get("cursor")
        }
