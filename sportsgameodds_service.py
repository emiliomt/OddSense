"""
SportsGameOdds API Service
Fetches real-time betting odds from multiple sportsbooks via SportsGameOdds API
"""

import requests
import os
from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta, timezone
import time

logger = logging.getLogger(__name__)


class SportsGameOddsService:
    """Service for fetching NFL betting odds from SportsGameOdds API."""
    
    BASE_URL = "https://api.sportsgameodds.com/v2"
    
    # Class-level cache for NFL events (shared across instances)
    _events_cache = None
    _cache_timestamp = None
    _cache_duration = 300  # Cache for 5 minutes
    
    def __init__(self):
        self.api_key = os.environ.get('SPORTSGAMEODDS_API_KEY')
        
        if not self.api_key:
            logger.warning("SPORTSGAMEODDS_API_KEY not found in environment")
        
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Accept': 'application/json',
                'X-Api-Key': self.api_key
            })
    
    def get_nfl_events(self, **kwargs) -> Optional[List[Dict]]:
        """
        Fetch current NFL events with odds from multiple sportsbooks.
        Uses caching to avoid hitting rate limits.
        
        Returns:
            List of NFL events with odds data
        """
        # Check if we have valid cached data
        now = time.time()
        if (SportsGameOddsService._events_cache is not None and 
            SportsGameOddsService._cache_timestamp is not None and
            (now - SportsGameOddsService._cache_timestamp) < SportsGameOddsService._cache_duration):
            logger.info(f"Using cached NFL events ({len(SportsGameOddsService._events_cache)} events)")
            return SportsGameOddsService._events_cache
        
        url = f"{self.BASE_URL}/events/"
        
        # Calculate date range for NFL games (today and next 2 weeks)
        # API expects UTC timestamps in RFC3339 format with 'Z' suffix and no microseconds
        today = datetime.now(timezone.utc).replace(microsecond=0)
        two_weeks = today + timedelta(days=14)
        
        params = {
            'sportID': 'AMERICANFOOTBALL_NFL',
            'oddsAvailable': True,  # Only get games with active odds
            'startsAfter': today.isoformat().replace('+00:00', 'Z'),
            'startsBefore': two_weeks.isoformat().replace('+00:00', 'Z'),
            'limit': 100
        }
        
        try:
            logger.info(f"Fetching NFL events from SportsGameOdds API (cache miss)")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('success'):
                logger.warning(f"API returned success=false: {data}")
                return []
            
            events = data.get('data', [])
            logger.info(f"Successfully fetched {len(events)} NFL events")
            
            # Update cache
            SportsGameOddsService._events_cache = events
            SportsGameOddsService._cache_timestamp = now
            
            return events
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error fetching from SportsGameOdds API: {e}")
            # Return cached data if available, even if expired
            if SportsGameOddsService._events_cache is not None:
                logger.info("Returning stale cache due to API error")
                return SportsGameOddsService._events_cache
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            SportsGameOddsService._events_cache = []
            SportsGameOddsService._cache_timestamp = now
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from SportsGameOdds API: {e}")
            # Return cached data if available, even if expired
            if SportsGameOddsService._events_cache is not None:
                logger.info("Returning stale cache due to network error")
                return SportsGameOddsService._events_cache
            # On first failure with no cache, cache empty array and set timestamp to throttle retries
            logger.info("No cache available, caching empty array and throttling retries for 5 minutes")
            SportsGameOddsService._events_cache = []
            SportsGameOddsService._cache_timestamp = now
            return []
    
    def find_game_by_teams(self, away_team: str, home_team: str) -> Optional[Dict]:
        """
        Find a specific NFL game by team names.
        
        Args:
            away_team: Away team name (e.g., "Las Vegas Raiders")
            home_team: Home team name (e.g., "Denver Broncos")
        
        Returns:
            Event data with odds, or None if not found
        """
        events = self.get_nfl_events()
        if not events:
            return None
        
        # Normalize team names for matching
        away_normalized = self._normalize_team_name(away_team)
        home_normalized = self._normalize_team_name(home_team)
        
        logger.info(f"Searching for game: {away_team} @ {home_team}")
        
        for event in events:
            teams = event.get('teams', {})
            event_away = teams.get('away', {}).get('names', {})
            event_home = teams.get('home', {}).get('names', {})
            
            # Try different name variations (short, medium, long)
            away_names = [
                event_away.get('short', ''),
                event_away.get('medium', ''),
                event_away.get('long', '')
            ]
            
            home_names = [
                event_home.get('short', ''),
                event_home.get('medium', ''),
                event_home.get('long', '')
            ]
            
            # Check if our team names match any of the variations
            away_match = any(away_normalized in self._normalize_team_name(name) for name in away_names if name)
            home_match = any(home_normalized in self._normalize_team_name(name) for name in home_names if name)
            
            if away_match and home_match:
                logger.info(f"Found matching game: {event.get('eventID')}")
                return event
        
        logger.warning(f"No game found for {away_team} @ {home_team}")
        return None
    
    def get_best_odds(self, event: Dict, team: str, market: str = 'h2h') -> Optional[Dict]:
        """
        Get the best available odds for a specific team.
        
        Args:
            event: Event data from SportsGameOdds API
            team: Team name to find odds for
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with best odds: {'bookmaker': str, 'odds': int, 'implied_probability': float}
        """
        if not event:
            return None
        
        odds_data = event.get('odds', {})
        by_bookmaker = odds_data.get('byBookmaker', {})
        
        if not by_bookmaker:
            return None
        
        team_normalized = self._normalize_team_name(team)
        teams = event.get('teams', {})
        
        # Determine if team is away or home
        away_names = [
            teams.get('away', {}).get('names', {}).get('short', ''),
            teams.get('away', {}).get('names', {}).get('medium', ''),
            teams.get('away', {}).get('names', {}).get('long', '')
        ]
        
        is_away = any(team_normalized in self._normalize_team_name(name) for name in away_names if name)
        
        best_odds = None
        best_value = float('-inf')
        
        # Iterate through bookmakers
        for bookmaker_id, book_data in by_bookmaker.items():
            moneyline = book_data.get('moneyline', {})
            
            if not moneyline:
                continue
            
            # Get the appropriate odds
            if is_away:
                odds_value = moneyline.get('away')
            else:
                odds_value = moneyline.get('home')
            
            if odds_value and odds_value > best_value:
                best_value = odds_value
                best_odds = {
                    'bookmaker': bookmaker_id.replace('_', ' ').title(),
                    'odds': int(odds_value),
                    'implied_probability': self._american_to_probability(odds_value)
                }
        
        return best_odds
    
    def get_all_bookmaker_odds(self, event: Dict, market: str = 'h2h') -> Dict[str, List[Dict]]:
        """
        Get odds from all bookmakers for an event.
        
        Args:
            event: Event data from SportsGameOdds API
            market: 'h2h' (moneyline), 'spreads', or 'totals'
        
        Returns:
            Dict with away_team and home_team odds lists
        """
        if not event:
            return {'away_team': [], 'home_team': []}
        
        odds_data = event.get('odds', {})
        by_bookmaker = odds_data.get('byBookmaker', {})
        
        if not by_bookmaker:
            return {'away_team': [], 'home_team': []}
        
        away_odds = []
        home_odds = []
        
        for bookmaker_id, book_data in by_bookmaker.items():
            bookmaker_name = bookmaker_id.replace('_', ' ').title()
            
            if market == 'h2h':
                moneyline = book_data.get('moneyline', {})
                if moneyline:
                    away_ml = moneyline.get('away')
                    home_ml = moneyline.get('home')
                    
                    if away_ml:
                        away_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': int(away_ml),
                            'implied_probability': self._american_to_probability(away_ml),
                            'point': None
                        })
                    
                    if home_ml:
                        home_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': int(home_ml),
                            'implied_probability': self._american_to_probability(home_ml),
                            'point': None
                        })
            elif market == 'spreads':
                spread = book_data.get('spread', {})
                if spread:
                    away_spread = spread.get('away', {})
                    home_spread = spread.get('home', {})
                    
                    if away_spread:
                        away_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': int(away_spread.get('price', 0)),
                            'implied_probability': self._american_to_probability(away_spread.get('price', 0)),
                            'point': away_spread.get('point')
                        })
                    
                    if home_spread:
                        home_odds.append({
                            'bookmaker': bookmaker_name,
                            'odds': int(home_spread.get('price', 0)),
                            'implied_probability': self._american_to_probability(home_spread.get('price', 0)),
                            'point': home_spread.get('point')
                        })
        
        return {
            'away_team': away_odds,
            'home_team': home_odds
        }
    
    def get_market_consensus(self, event: Dict, market: str = 'h2h') -> Optional[Dict]:
        """
        Calculate consensus (average) odds across all bookmakers.
        
        Args:
            event: Event data from SportsGameOdds API
            market: 'h2h', 'spreads', or 'totals'
        
        Returns:
            Dict with consensus odds for away and home teams
        """
        all_odds = self.get_all_bookmaker_odds(event, market)
        
        if not all_odds['away_team'] or not all_odds['home_team']:
            return None
        
        # Calculate average implied probability
        away_probs = [odd['implied_probability'] for odd in all_odds['away_team'] if odd['implied_probability']]
        home_probs = [odd['implied_probability'] for odd in all_odds['home_team'] if odd['implied_probability']]
        
        if not away_probs or not home_probs:
            return None
        
        return {
            'away_team': {
                'average_probability': sum(away_probs) / len(away_probs),
                'num_bookmakers': len(away_probs)
            },
            'home_team': {
                'average_probability': sum(home_probs) / len(home_probs),
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
        normalized = team_name.lower().strip()
        
        # Remove location prefixes for matching
        words = normalized.split()
        if len(words) > 1:
            # Return last word (team name without city)
            return words[-1]
        
        return normalized
