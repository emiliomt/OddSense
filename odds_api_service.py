import os
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class OddsAPIService:
    """
    Service for fetching NFL betting odds from The Odds API.
    API Documentation: https://the-odds-api.com/liveapi/guides/v4/
    """
    
    BASE_URL = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
    
    # Class-level cache to share across instances
    _odds_cache: Optional[List[Dict]] = None
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl = timedelta(minutes=5)
    
    # NFL team name normalization mapping
    NFL_TEAMS = {
        "Arizona Cardinals": ["Arizona", "Cardinals", "ARI"],
        "Atlanta Falcons": ["Atlanta", "Falcons", "ATL"],
        "Baltimore Ravens": ["Baltimore", "Ravens", "BAL"],
        "Buffalo Bills": ["Buffalo", "Bills", "BUF"],
        "Carolina Panthers": ["Carolina", "Panthers", "CAR"],
        "Chicago Bears": ["Chicago", "Bears", "CHI"],
        "Cincinnati Bengals": ["Cincinnati", "Bengals", "CIN"],
        "Cleveland Browns": ["Cleveland", "Browns", "CLE"],
        "Dallas Cowboys": ["Dallas", "Cowboys", "DAL"],
        "Denver Broncos": ["Denver", "Broncos", "DEN"],
        "Detroit Lions": ["Detroit", "Lions", "DET"],
        "Green Bay Packers": ["Green Bay", "Packers", "GB", "GNB"],
        "Houston Texans": ["Houston", "Texans", "HOU"],
        "Indianapolis Colts": ["Indianapolis", "Colts", "IND"],
        "Jacksonville Jaguars": ["Jacksonville", "Jaguars", "JAX", "JAC"],
        "Kansas City Chiefs": ["Kansas City", "Chiefs", "KC", "KAN"],
        "Las Vegas Raiders": ["Las Vegas", "Raiders", "LV", "LVR", "Oakland"],
        "Los Angeles Chargers": ["Los Angeles Chargers", "Chargers", "LAC", "LA Chargers"],
        "Los Angeles Rams": ["Los Angeles Rams", "Rams", "LAR", "LA Rams"],
        "Miami Dolphins": ["Miami", "Dolphins", "MIA"],
        "Minnesota Vikings": ["Minnesota", "Vikings", "MIN"],
        "New England Patriots": ["New England", "Patriots", "NE", "NWE"],
        "New Orleans Saints": ["New Orleans", "Saints", "NO", "NOR"],
        "New York Giants": ["New York Giants", "Giants", "NYG", "NY Giants"],
        "New York Jets": ["New York Jets", "Jets", "NYJ", "NY Jets"],
        "Philadelphia Eagles": ["Philadelphia", "Eagles", "PHI"],
        "Pittsburgh Steelers": ["Pittsburgh", "Steelers", "PIT"],
        "San Francisco 49ers": ["San Francisco", "49ers", "SF", "SFO"],
        "Seattle Seahawks": ["Seattle", "Seahawks", "SEA"],
        "Tampa Bay Buccaneers": ["Tampa Bay", "Buccaneers", "TB", "TAM"],
        "Tennessee Titans": ["Tennessee", "Titans", "TEN"],
        "Washington Commanders": ["Washington", "Commanders", "WAS", "Washington Football Team", "Redskins"],
    }
    
    def __init__(self):
        self.api_key = os.getenv("ODDS_API_KEY")
        if not self.api_key:
            logger.warning("ODDS_API_KEY not found in environment variables")
    
    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team names to match across different APIs.
        Uses fuzzy matching to handle variations.
        """
        team_name_lower = team_name.lower()
        
        best_match: Optional[str] = None
        best_ratio = 0
        
        for canonical_name, variations in self.NFL_TEAMS.items():
            for variant in variations:
                ratio = SequenceMatcher(None, team_name_lower, variant.lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = canonical_name
        
        if best_ratio > 0.6 and best_match:
            return best_match
        
        return team_name
    
    def get_nfl_odds(self) -> List[Dict]:
        """
        Fetch current NFL odds from The Odds API.
        Returns a list of games with odds from multiple bookmakers.
        Implements 5-minute caching to minimize API usage.
        """
        if not self.api_key:
            logger.error("Cannot fetch odds: ODDS_API_KEY not configured")
            return []
        
        # Check cache validity
        now = datetime.now(timezone.utc)
        if (OddsAPIService._cache_timestamp and 
            OddsAPIService._odds_cache is not None and
            (now - OddsAPIService._cache_timestamp) < OddsAPIService._cache_ttl):
            logger.info("Returning cached odds data")
            return OddsAPIService._odds_cache
        
        try:
            params = {
                "apiKey": self.api_key,
                "regions": "us",
                "markets": "h2h",  # Head-to-head (moneyline)
                "oddsFormat": "american",
                "dateFormat": "iso"
            }
            
            logger.info(f"Fetching NFL odds from The Odds API")
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            odds_data = response.json()
            logger.info(f"Successfully fetched {len(odds_data)} games from The Odds API")
            
            # Update cache
            OddsAPIService._odds_cache = odds_data
            OddsAPIService._cache_timestamp = now
            
            return odds_data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error fetching from The Odds API: {e}")
            # Return cached data if available, even if expired
            if OddsAPIService._odds_cache is not None:
                logger.info("Returning stale cache due to API error")
                return OddsAPIService._odds_cache
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            OddsAPIService._odds_cache = []
            OddsAPIService._cache_timestamp = now
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from The Odds API: {e}")
            # Return cached data if available, even if expired
            if OddsAPIService._odds_cache is not None:
                logger.info("Returning stale cache due to network error")
                return OddsAPIService._odds_cache
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            OddsAPIService._odds_cache = []
            OddsAPIService._cache_timestamp = now
            return []
    
    def find_game_by_teams(self, away_team: str, home_team: str) -> Optional[Dict]:
        """
        Find a specific NFL game by team names.
        Uses fuzzy matching to handle name variations.
        """
        odds_data = self.get_nfl_odds()
        
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
