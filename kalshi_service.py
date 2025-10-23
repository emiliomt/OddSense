import requests
from typing import Dict, List, Optional
from datetime import datetime

class KalshiService:
    """Service for interacting with the unauthenticated Kalshi API."""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_nfl_markets(self, limit: int = 100, cursor: Optional[str] = None) -> Dict:
        """
        Fetch NFL markets from Kalshi API.
        
        Args:
            limit: Number of markets to fetch
            cursor: Pagination cursor for next page
            
        Returns:
            Dictionary containing markets and cursor
        """
        params = {
            "limit": limit,
            "series_ticker": "NFL",
            "status": "open"
        }
        
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
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
        params = {
            "limit": limit,
            "series_ticker": "NFL",
            "status": "open",
            "event_ticker": query
        }
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/markets",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("markets", [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching markets: {e}")
            return []
    
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
