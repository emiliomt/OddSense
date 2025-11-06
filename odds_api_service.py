
"""
The Rundown API Service
Fetches real-time betting odds from multiple sportsbooks via The Rundown API (RapidAPI)
"""

import requests
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class OddsAPIService:
    """Service for fetching NFL betting odds from The Rundown API."""
    
    BASE_URL = "https://therundown-therundown-v1.p.rapidapi.com"
    SPORT_ID = 2  # NFL
    
    def __init__(self):
        self.api_key = os.environ.get('RAPIDAPI_KEY', '18e5027c32mshf0f052aa9879a25p1d3771jsn831d4331a324')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'x-rapidapi-host': 'therundown-therundown-v1.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        })
    
    def get_odds(self, **kwargs) -> Optional[List[Dict]]:
        """
        Fetch current NFL betting odds from multiple sportsbooks.
        
        Returns:
            List of games with odds from multiple bookmakers
        """
        # The Rundown API uses /sports/{sport_id}/events/{date} format
        # Try today's date first
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Try the events endpoint with date parameter
        url = f"{self.BASE_URL}/sports/{self.SPORT_ID}/events/{today}"
        
        try:
            logger.info(f"Fetching odds from The Rundown API: {url}")
            response = self.session.get(url, timeout=10)
            
            # If 404, try without date
            if response.status_code == 404:
                logger.warning(f"404 on dated endpoint, trying base events")
                url = f"{self.BASE_URL}/sports/{self.SPORT_ID}/events"
                response = self.session.get(url, timeout=10)
            
            # If still 404, the API may not have data or structure changed
            if response.status_code == 404:
                logger.warning(f"No events found. API may have no current games or endpoint changed.")
                # Return empty list instead of None to avoid breaking the app
                return []
            
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response structures
            if isinstance(data, dict):
                events = data.get('events', [])
                if not events:
                    # Try other possible keys
                    events = data.get('data', [])
                if not events:
                    events = data.get('schedule', [])
            elif isinstance(data, list):
                events = data
            else:
                events = []
            
            logger.info(f"Successfully fetched odds for {len(events)} games")
            
            return events
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error fetching odds from The Rundown API: {e}")
            # Return empty list to gracefully handle API errors
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching odds from The Rundown API: {e}")
            # Return empty list to gracefully handle network errors
            return []
    
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
        
        for event in all_odds:
            # Try different possible team field structures
            teams_normalized = event.get('teams_normalized', [])
            teams = event.get('teams', [])
            
            # Handle teams_normalized structure
            if teams_normalized and len(teams_normalized) >= 2:
                event_away = self._normalize_team_name(teams_normalized[0].get('name', ''))
                event_home = self._normalize_team_name(teams_normalized[1].get('name', ''))
                
                if away_normalized in event_away and home_normalized in event_home:
                    logger.info(f"Found matching game via teams_normalized")
                    return event
            
            # Handle simple teams array structure
            if teams and len(teams) >= 2:
                event_away = self._normalize_team_name(teams[0] if isinstance(teams[0], str) else teams[0].get('name', ''))
                event_home = self._normalize_team_name(teams[1] if isinstance(teams[1], str) else teams[1].get('name', ''))
                
                if away_normalized in event_away and home_normalized in event_home:
                    logger.info(f"Found matching game via teams array")
                    return event
        
        logger.warning(f"No game found for {away_team} @ {home_team}")
        return None
    
    def get_best_odds(self, game: Dict, team: str, market: str = 'h2h') -> Optional[Dict]:
        """
        Get the best available odds for a specific team in a game.
        
        Args:
            game: Game data from The Rundown API
            team: Team name to find odds for
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with best odds info: {'bookmaker': str, 'odds': int, 'price': float}
        """
        if not game:
            return None
        
        # Check for lines in different possible locations
        lines = game.get('lines', {})
        if not lines:
            lines = game.get('odds', {})
        if not lines:
            return None
        
        team_normalized = self._normalize_team_name(team)
        best_odds = None
        best_value = float('-inf')
        
        # Determine if team is away or home
        teams_normalized = game.get('teams_normalized', [])
        teams = game.get('teams', [])
        
        away_name = ''
        home_name = ''
        
        if teams_normalized and len(teams_normalized) >= 2:
            away_name = teams_normalized[0].get('name', '')
            home_name = teams_normalized[1].get('name', '')
        elif teams and len(teams) >= 2:
            away_name = teams[0] if isinstance(teams[0], str) else teams[0].get('name', '')
            home_name = teams[1] if isinstance(teams[1], str) else teams[1].get('name', '')
        
        if not away_name or not home_name:
            return None
        
        is_away = team_normalized in self._normalize_team_name(away_name)
        
        # Iterate through bookmakers
        for book_key, book_data in lines.items():
            if not isinstance(book_data, dict):
                continue
            
            moneyline = book_data.get('moneyline', {})
            if not moneyline:
                continue
            
            # Get the appropriate moneyline value
            if market == 'h2h':
                if is_away:
                    odds_value = moneyline.get('moneyline_away')
                else:
                    odds_value = moneyline.get('moneyline_home')
                
                if odds_value and odds_value > best_value:
                    best_value = odds_value
                    best_odds = {
                        'bookmaker': book_data.get('affiliate', {}).get('affiliate_name', book_key),
                        'odds': odds_value,
                        'implied_probability': self._american_to_probability(odds_value)
                    }
        
        return best_odds
    
    def get_all_bookmaker_odds(self, game: Dict, market: str = 'h2h') -> Dict[str, List[Dict]]:
        """
        Get odds from all bookmakers for a game.
        
        Args:
            game: Game data from The Rundown API
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with away_team and home_team odds lists
        """
        if not game:
            return {'away_team': [], 'home_team': []}
        
        # Check for lines in different possible locations
        lines = game.get('lines', {})
        if not lines:
            lines = game.get('odds', {})
        if not lines:
            return {'away_team': [], 'home_team': []}
        
        away_odds = []
        home_odds = []
        
        for book_key, book_data in lines.items():
            if not isinstance(book_data, dict):
                continue
            
            bookmaker_name = book_data.get('affiliate', {}).get('affiliate_name', book_key)
            
            if market == 'h2h':
                moneyline = book_data.get('moneyline', {})
                if moneyline:
                    away_ml = moneyline.get('moneyline_away')
                    home_ml = moneyline.get('moneyline_home')
                    
                    if away_ml:
                        away_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': away_ml,
                            'implied_probability': self._american_to_probability(away_ml),
                            'point': None
                        })
                    
                    if home_ml:
                        home_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': home_ml,
                            'implied_probability': self._american_to_probability(home_ml),
                            'point': None
                        })
            elif market == 'spreads':
                spread = book_data.get('spread', {})
                if spread:
                    away_odds.append({
                        'bookmaker': bookmaker_name,
                        'odds': spread.get('point_spread_away_money'),
                        'implied_probability': self._american_to_probability(spread.get('point_spread_away_money', 0)),
                        'point': spread.get('point_spread_away')
                    })
                    
                    home_odds.append({
                        'bookmaker': bookmaker_name,
                        'odds': spread.get('point_spread_home_money'),
                        'implied_probability': self._american_to_probability(spread.get('point_spread_home_money', 0)),
                        'point': spread.get('point_spread_home')
                    })
        
        return {
            'away_team': away_odds,
            'home_team': home_odds
        }
    
    def get_market_consensus(self, game: Dict, market: str = 'h2h') -> Optional[Dict]:
        """
        Calculate consensus (average) odds across all bookmakers.
        
        Args:
            game: Game data from The Rundown API
            market: 'h2h', 'spreads', or 'totals'
        
        Returns:
            Dict with consensus odds for away and home teams
        """
        all_odds = self.get_all_bookmaker_odds(game, market)
        
        if not all_odds['away_team'] or not all_odds['home_team']:
            return None
        
        # Calculate average implied probability
        away_probs = [odd['implied_probability'] for odd in all_odds['away_team'] if odd['implied_probability']]
        home_probs = [odd['implied_probability'] for odd in all_odds['home_team'] if odd['implied_probability']]
        
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
        if american_odds == 0 or american_odds is None:
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
