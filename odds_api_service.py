"""
The Odds API Service
Fetches real-time betting odds from multiple sportsbooks via The-Odds-API.com
"""

import requests
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class OddsAPIService:
    """Service for fetching NFL betting odds from The Odds API."""
    
    BASE_URL = "https://api.the-odds-api.com/v4/sports"
    SPORT = "americanfootball_nfl"
    
    def __init__(self):
        self.api_key = os.environ.get('ODDS_API_KEY')
        if not self.api_key:
            logger.warning("ODDS_API_KEY not found in environment variables")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
        })
    
    def get_odds(self, regions: str = 'us', markets: str = 'h2h,spreads,totals', 
                 oddsFormat: str = 'american') -> Optional[List[Dict]]:
        """
        Fetch current NFL betting odds from multiple sportsbooks.
        
        Args:
            regions: Comma-separated regions (e.g., 'us', 'uk', 'eu', 'au')
            markets: Comma-separated markets (h2h=moneyline, spreads, totals=over/under)
            oddsFormat: 'decimal' or 'american'
        
        Returns:
            List of games with odds from multiple bookmakers
        """
        if not self.api_key:
            logger.error("Cannot fetch odds: API key not configured")
            return None
        
        url = f"{self.BASE_URL}/{self.SPORT}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': oddsFormat
        }
        
        try:
            logger.info(f"Fetching odds from The Odds API: {url}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched odds for {len(data)} games")
            
            # Log remaining API requests
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            if remaining:
                logger.info(f"API requests remaining: {remaining} (used: {used})")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds from The Odds API: {e}")
            return None
    
    def find_game_by_teams(self, away_team: str, home_team: str) -> Optional[Dict]:
        """
        Find a specific game by team names and return its odds.
        
        Args:
            away_team: Away team name (e.g., "Las Vegas Raiders")
            home_team: Home team name (e.g., "Denver Broncos")
        
        Returns:
            Game data with odds from all bookmakers, or None if not found
        """
        all_odds = self.get_odds()
        if not all_odds:
            return None
        
        # Normalize team names for matching
        away_normalized = self._normalize_team_name(away_team)
        home_normalized = self._normalize_team_name(home_team)
        
        logger.info(f"Searching for game: {away_team} @ {home_team}")
        
        for game in all_odds:
            game_away = self._normalize_team_name(game.get('away_team', ''))
            game_home = self._normalize_team_name(game.get('home_team', ''))
            
            # Check if both teams match
            if away_normalized in game_away and home_normalized in game_home:
                logger.info(f"Found matching game: {game.get('away_team')} @ {game.get('home_team')}")
                return game
        
        logger.warning(f"No game found for {away_team} @ {home_team}")
        return None
    
    def get_best_odds(self, game: Dict, team: str, market: str = 'h2h') -> Optional[Dict]:
        """
        Get the best available odds for a specific team in a game.
        
        Args:
            game: Game data from The Odds API
            team: Team name to find odds for
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with best odds info: {'bookmaker': str, 'odds': int, 'price': float}
        """
        if not game or 'bookmakers' not in game:
            return None
        
        team_normalized = self._normalize_team_name(team)
        best_odds = None
        best_value = float('-inf')
        
        for bookmaker in game['bookmakers']:
            for market_data in bookmaker.get('markets', []):
                if market_data['key'] != market:
                    continue
                
                for outcome in market_data.get('outcomes', []):
                    outcome_team = self._normalize_team_name(outcome.get('name', ''))
                    
                    if team_normalized in outcome_team:
                        odds_value = outcome.get('price', 0)
                        
                        # For American odds, more positive is better for underdogs
                        # More negative (closer to 0) is better for favorites
                        if odds_value > best_value:
                            best_value = odds_value
                            best_odds = {
                                'bookmaker': bookmaker.get('title', bookmaker.get('key', 'Unknown')),
                                'odds': odds_value,
                                'implied_probability': self._american_to_probability(odds_value)
                            }
        
        return best_odds
    
    def get_all_bookmaker_odds(self, game: Dict, market: str = 'h2h') -> Dict[str, List[Dict]]:
        """
        Get odds from all bookmakers for a game.
        
        Args:
            game: Game data from The Odds API
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with away_team and home_team odds lists
        """
        if not game or 'bookmakers' not in game:
            return {'away_team': [], 'home_team': []}
        
        away_team = game.get('away_team', '')
        home_team = game.get('home_team', '')
        
        away_odds = []
        home_odds = []
        
        for bookmaker in game['bookmakers']:
            bookmaker_name = bookmaker.get('title', bookmaker.get('key', 'Unknown'))
            
            for market_data in bookmaker.get('markets', []):
                if market_data['key'] != market:
                    continue
                
                for outcome in market_data.get('outcomes', []):
                    outcome_team = outcome.get('name', '')
                    odds_value = outcome.get('price', 0)
                    
                    odds_info = {
                        'bookmaker': bookmaker_name,
                        'odds': odds_value,
                        'implied_probability': self._american_to_probability(odds_value),
                        'point': outcome.get('point')  # For spreads/totals
                    }
                    
                    if self._normalize_team_name(outcome_team) == self._normalize_team_name(away_team):
                        away_odds.append(odds_info)
                    elif self._normalize_team_name(outcome_team) == self._normalize_team_name(home_team):
                        home_odds.append(odds_info)
        
        return {
            'away_team': away_odds,
            'home_team': home_odds
        }
    
    def get_market_consensus(self, game: Dict, market: str = 'h2h') -> Optional[Dict]:
        """
        Calculate consensus (average) odds across all bookmakers.
        
        Args:
            game: Game data from The Odds API
            market: 'h2h', 'spreads', or 'totals'
        
        Returns:
            Dict with consensus odds for away and home teams
        """
        all_odds = self.get_all_bookmaker_odds(game, market)
        
        if not all_odds['away_team'] or not all_odds['home_team']:
            return None
        
        # Calculate average implied probability
        away_probs = [odd['implied_probability'] for odd in all_odds['away_team']]
        home_probs = [odd['implied_probability'] for odd in all_odds['home_team']]
        
        return {
            'away_team': {
                'average_probability': sum(away_probs) / len(away_probs) if away_probs else 0,
                'num_bookmakers': len(away_probs)
            },
            'home_team': {
                'average_probability': sum(home_probs) / len(home_probs) if home_probs else 0,
                'num_bookmakers': len(home_probs)
            }
        }
    
    @staticmethod
    def _american_to_probability(american_odds: float) -> float:
        """
        Convert American odds to implied probability.
        
        Args:
            american_odds: American odds (e.g., -150 or +200)
        
        Returns:
            Implied probability as decimal (0.0 to 1.0)
        """
        if american_odds == 0:
            return 0.0
        
        if american_odds > 0:
            # Underdog: probability = 100 / (odds + 100)
            return 100 / (american_odds + 100)
        else:
            # Favorite: probability = |odds| / (|odds| + 100)
            return abs(american_odds) / (abs(american_odds) + 100)
    
    @staticmethod
    def _normalize_team_name(team_name: str) -> str:
        """Normalize team name for matching."""
        # Convert to lowercase and remove common prefixes/suffixes
        normalized = team_name.lower().strip()
        
        # Remove location prefixes for matching
        # e.g., "Las Vegas Raiders" -> "raiders"
        words = normalized.split()
        if len(words) > 1:
            # Return last word (team name without city)
            return words[-1]
        
        return normalized
