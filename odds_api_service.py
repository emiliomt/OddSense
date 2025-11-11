import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from sport_config import get_sport_config, build_team_variations_map

logger = logging.getLogger(__name__)

class OddsAPIService:
    """
    Service for fetching sports betting odds from The Odds API.
    Supports NFL, NBA, NHL, and Soccer.
    API Documentation: https://the-odds-api.com/liveapi/guides/v4/
    """
    
    # Class-level cache to share across instances (separate per sport)
    _odds_cache: Dict[str, Optional[List[Dict]]] = {}
    _cache_timestamp: Dict[str, Optional[datetime]] = {}
    _cache_ttl = timedelta(minutes=5)
    
    def __init__(self, sport: str = "nfl"):
        self.sport = sport.lower()
        self.sport_config = get_sport_config(self.sport)
        self.api_key = os.getenv("ODDS_API_KEY")
        
        # Set sport-specific endpoint
        odds_api_key = self.sport_config.get("odds_api_key", "americanfootball_nfl")
        self.base_url = f"https://api.the-odds-api.com/v4/sports/{odds_api_key}/odds"
        
        # Get centralized team variations map for normalization
        self.team_variations = build_team_variations_map(self.sport)
        
        if not self.api_key:
            logger.warning("ODDS_API_KEY not found in environment variables")
    
    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team names to match across different APIs.
        Uses direct lookup from centralized team variations map with fuzzy matching fallback.
        """
        # Try direct lookup first (case-insensitive)
        for variation, canonical in self.team_variations.items():
            if team_name.lower() == variation.lower():
                return canonical
        
        # Fallback to fuzzy matching
        team_name_lower = team_name.lower()
        best_match: Optional[str] = None
        best_ratio = 0
        
        for variation, canonical in self.team_variations.items():
            ratio = SequenceMatcher(None, team_name_lower, variation.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = canonical
        
        if best_ratio > 0.6 and best_match:
            return best_match
        
        return team_name
    
    def get_odds(self) -> List[Dict]:
        """
        Fetch current sports odds from The Odds API.
        Returns a list of games with odds from multiple bookmakers.
        Implements 5-minute caching per sport to minimize API usage.
        """
        if not self.api_key:
            logger.error("Cannot fetch odds: ODDS_API_KEY not configured")
            return []
        
        # Check cache validity for this sport
        now = datetime.now(timezone.utc)
        cache_ts = OddsAPIService._cache_timestamp.get(self.sport)
        cache_data = OddsAPIService._odds_cache.get(self.sport)
        
        if (cache_ts and cache_data is not None and
            (now - cache_ts) < OddsAPIService._cache_ttl):
            logger.info(f"Returning cached {self.sport.upper()} odds data")
            return cache_data
        
        try:
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h",  # Head-to-head (moneyline)
                "oddsFormat": "american",
                "dateFormat": "iso"
            }
            
            logger.info(f"Fetching {self.sport.upper()} odds from The Odds API")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            odds_data = response.json()
            logger.info(f"Successfully fetched {len(odds_data)} {self.sport.upper()} games from The Odds API")
            
            # Update cache for this sport
            OddsAPIService._odds_cache[self.sport] = odds_data
            OddsAPIService._cache_timestamp[self.sport] = now
            
            return odds_data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error fetching from The Odds API: {e}")
            # Return cached data if available, even if expired
            if cache_data is not None:
                logger.info("Returning stale cache due to API error")
                return cache_data
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            OddsAPIService._odds_cache[self.sport] = []
            OddsAPIService._cache_timestamp[self.sport] = now
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from The Odds API: {e}")
            # Return cached data if available, even if expired
            if cache_data is not None:
                logger.info("Returning stale cache due to network error")
                return cache_data
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            OddsAPIService._odds_cache[self.sport] = []
            OddsAPIService._cache_timestamp[self.sport] = now
            return []
    
    def find_game_by_teams(self, away_team: str, home_team: str) -> Optional[Dict]:
        """
        Find a specific game by team names.
        Uses fuzzy matching to handle name variations.
        """
        odds_data = self.get_odds()
        
        if not odds_data:
            return None
        
        # Normalize team names
        normalized_away = self._normalize_team_name(away_team)
        normalized_home = self._normalize_team_name(home_team)
        
        for game in odds_data:
            game_away = self._normalize_team_name(game.get("away_team", ""))
            game_home = self._normalize_team_name(game.get("home_team", ""))
            
            if game_away == normalized_away and game_home == normalized_home:
                return game
        
        return None
    
    def american_to_probability(self, american_odds: int) -> float:
        """
        Convert American odds to implied probability percentage.
        
        Examples:
        -150 (favorite) -> 60.0%
        +200 (underdog) -> 33.3%
        """
        if american_odds < 0:
            # Favorite: abs(odds) / (abs(odds) + 100)
            return (abs(american_odds) / (abs(american_odds) + 100)) * 100
        else:
            # Underdog: 100 / (odds + 100)
            return (100 / (american_odds + 100)) * 100
    
    def get_market_consensus(self, game: Dict) -> Dict[str, float]:
        """
        Calculate consensus probability across all bookmakers for a game.
        Returns average implied probability for each team.
        """
        if not game or "bookmakers" not in game:
            return {}
        
        away_team = game.get("away_team", "")
        home_team = game.get("home_team", "")
        
        away_probs = []
        home_probs = []
        
        for bookmaker in game["bookmakers"]:
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        if outcome["name"] == away_team:
                            away_probs.append(self.american_to_probability(outcome["price"]))
                        elif outcome["name"] == home_team:
                            home_probs.append(self.american_to_probability(outcome["price"]))
        
        consensus = {}
        if away_probs:
            consensus[away_team] = sum(away_probs) / len(away_probs)
        if home_probs:
            consensus[home_team] = sum(home_probs) / len(home_probs)
        
        return consensus
    
    def get_best_odds(self, game: Dict, team_name: str) -> Optional[Dict]:
        """
        Find the best available odds for a specific team.
        For favorites (negative odds), best = least negative (e.g., -120 better than -150)
        For underdogs (positive odds), best = most positive (e.g., +200 better than +150)
        """
        if not game or "bookmakers" not in game:
            return None
        
        best_odds = None
        best_bookmaker = None
        
        for bookmaker in game["bookmakers"]:
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        if outcome["name"] == team_name:
                            odds = outcome["price"]
                            
                            if best_odds is None:
                                best_odds = odds
                                best_bookmaker = bookmaker["title"]
                            else:
                                # For favorites (negative), less negative is better
                                # For underdogs (positive), more positive is better
                                if (odds < 0 and odds > best_odds) or (odds > 0 and odds > best_odds):
                                    best_odds = odds
                                    best_bookmaker = bookmaker["title"]
        
        if best_odds is not None:
            return {
                "odds": best_odds,
                "bookmaker": best_bookmaker,
                "probability": self.american_to_probability(best_odds)
            }
        
        return None
    
    def get_all_bookmaker_odds(self, game: Dict, team_name: str) -> List[Dict]:
        """
        Get odds from all bookmakers for a specific team.
        Returns a list of {bookmaker, odds, probability} dicts.
        """
        if not game or "bookmakers" not in game:
            return []
        
        all_odds = []
        
        for bookmaker in game["bookmakers"]:
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        if outcome["name"] == team_name:
                            odds = outcome["price"]
                            all_odds.append({
                                "bookmaker": bookmaker["title"],
                                "odds": odds,
                                "probability": self.american_to_probability(odds)
                            })
        
        return all_odds
