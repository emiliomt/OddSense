"""
ESPN API Service
Fetches historical NFL game data from ESPN's unofficial public API.
"""

import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ESPNService:
    """Service for fetching NFL game data from ESPN API."""
    
    BASE_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; KalshiMarketsExplorer/1.0)'
        })
    
    def get_scoreboard(self, date: Optional[str] = None, week: Optional[int] = None, 
                       season: Optional[int] = None, seasontype: int = 2) -> Optional[Dict]:
        """
        Fetch NFL scoreboard for a specific date, week, or current games.
        
        Args:
            date: Date string in YYYYMMDD format (e.g., '20251103')
            week: Week number (1-18 for regular season)
            season: Year (e.g., 2025)
            seasontype: 1=preseason, 2=regular season, 3=playoffs
        
        Returns:
            Dict with scoreboard data including games, scores, and status
        """
        url = f"{self.BASE_URL}/scoreboard"
        params = {}
        
        if date:
            params['dates'] = date
        elif week and season:
            params['seasontype'] = seasontype
            params['week'] = week
            params['dates'] = season
        
        try:
            logger.info(f"Fetching ESPN scoreboard: {url} with params {params}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched scoreboard with {len(data.get('events', []))} games")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ESPN scoreboard: {e}")
            return None
    
    def get_game_summary(self, game_id: str) -> Optional[Dict]:
        """
        Fetch detailed game summary including box score, stats, and play-by-play.
        
        Args:
            game_id: ESPN game ID (e.g., '401547402')
        
        Returns:
            Dict with comprehensive game data
        """
        url = f"{self.BASE_URL}/summary"
        params = {'event': game_id}
        
        try:
            logger.info(f"Fetching ESPN game summary for game_id={game_id}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched game summary for {game_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching game summary for {game_id}: {e}")
            return None
    
    def find_game_by_teams_and_date(self, away_team: str, home_team: str, 
                                    game_date: datetime) -> Optional[Dict]:
        """
        Find a specific game by team names and approximate date.
        
        Args:
            away_team: Away team name (e.g., 'Las Vegas Raiders')
            home_team: Home team name (e.g., 'Denver Broncos')
            game_date: Expected game date (datetime object)
        
        Returns:
            Dict with game data if found, None otherwise
        """
        # Format date for ESPN API (YYYYMMDD)
        date_str = game_date.strftime('%Y%m%d')
        
        # Try the exact date and neighboring dates
        for day_offset in [0, -1, 1, -2, 2]:
            from datetime import timedelta
            check_date = game_date + timedelta(days=day_offset)
            check_date_str = check_date.strftime('%Y%m%d')
            
            scoreboard = self.get_scoreboard(date=check_date_str)
            if not scoreboard or 'events' not in scoreboard:
                continue
            
            # Search for matching game
            for event in scoreboard['events']:
                if not event.get('competitions'):
                    continue
                
                competition = event['competitions'][0]
                competitors = competition.get('competitors', [])
                
                if len(competitors) != 2:
                    continue
                
                # Extract team names
                teams = {}
                for comp in competitors:
                    home_away = comp.get('homeAway', '')
                    team_name = comp.get('team', {}).get('displayName', '')
                    teams[home_away] = team_name
                
                # Check if teams match
                if (self._team_names_match(teams.get('away', ''), away_team) and
                    self._team_names_match(teams.get('home', ''), home_team)):
                    
                    logger.info(f"Found matching game: {away_team} @ {home_team} on {check_date_str}")
                    return self._extract_game_result(event)
        
        logger.warning(f"No game found for {away_team} @ {home_team} near {date_str}")
        return None
    
    def _team_names_match(self, espn_name: str, kalshi_name: str) -> bool:
        """
        Check if ESPN and Kalshi team names match (fuzzy matching).
        
        Examples:
            'Kansas City Chiefs' matches 'Kansas City'
            'Las Vegas Raiders' matches 'Las Vegas Raiders'
        """
        espn_lower = espn_name.lower()
        kalshi_lower = kalshi_name.lower()
        
        # Direct match
        if espn_lower == kalshi_lower:
            return True
        
        # Kalshi name is substring of ESPN name (common case)
        if kalshi_lower in espn_lower:
            return True
        
        # ESPN name is substring of Kalshi name
        if espn_lower in kalshi_lower:
            return True
        
        # Match by team nickname (last word)
        espn_parts = espn_lower.split()
        kalshi_parts = kalshi_lower.split()
        
        if espn_parts and kalshi_parts:
            # Match by last word (team nickname)
            if espn_parts[-1] == kalshi_parts[-1]:
                return True
        
        return False
    
    def _extract_game_result(self, event: Dict) -> Dict:
        """
        Extract relevant game result information from ESPN event data.
        
        Returns:
            Dict with game_id, status, scores, winner, etc.
        """
        competition = event.get('competitions', [{}])[0]
        competitors = competition.get('competitors', [])
        
        # Extract team data
        home_team = None
        away_team = None
        
        for comp in competitors:
            team_data = {
                'id': comp.get('id'),
                'name': comp.get('team', {}).get('displayName', ''),
                'abbreviation': comp.get('team', {}).get('abbreviation', ''),
                'score': int(comp.get('score', 0)) if comp.get('score') else None,
                'winner': comp.get('winner', False)
            }
            
            if comp.get('homeAway') == 'home':
                home_team = team_data
            else:
                away_team = team_data
        
        # Game status
        status = event.get('status', {})
        status_type = status.get('type', {})
        
        result = {
            'game_id': event.get('id'),
            'name': event.get('name'),
            'short_name': event.get('shortName'),
            'date': event.get('date'),
            'status': {
                'completed': status_type.get('completed', False),
                'description': status_type.get('description', ''),
                'state': status_type.get('state', '')
            },
            'home_team': home_team,
            'away_team': away_team,
            'winner': None
        }
        
        # Determine winner
        if result['status']['completed']:
            if home_team and away_team:
                if home_team.get('winner'):
                    result['winner'] = 'home'
                elif away_team.get('winner'):
                    result['winner'] = 'away'
        
        return result
    
    def compare_to_kalshi_odds(self, game_result: Dict, kalshi_probability: float, 
                               bet_on_team: str) -> Dict:
        """
        Compare ESPN game result to Kalshi implied odds.
        
        Args:
            game_result: Game result from ESPN
            kalshi_probability: Kalshi implied probability (0-1)
            bet_on_team: Which team the Kalshi market was for ('home' or 'away')
        
        Returns:
            Dict with comparison analysis
        """
        if not game_result.get('status', {}).get('completed'):
            return {
                'status': 'incomplete',
                'message': 'Game has not finished yet'
            }
        
        # Check if the bet won
        winner = game_result.get('winner')
        bet_won = (winner == bet_on_team)
        
        # Get team info
        team_info = game_result.get(f'{bet_on_team}_team', {})
        team_name = team_info.get('name', 'Unknown')
        
        # Calculate analysis
        kalshi_pct = kalshi_probability * 100
        
        # Categorize market confidence
        if kalshi_pct >= 75:
            confidence = "very confident"
        elif kalshi_pct >= 60:
            confidence = "moderately confident"
        elif kalshi_pct >= 40:
            confidence = "uncertain"
        elif kalshi_pct >= 25:
            confidence = "doubtful"
        else:
            confidence = "very doubtful"
        
        # Build analysis
        analysis = {
            'bet_won': bet_won,
            'team_name': team_name,
            'kalshi_probability': kalshi_probability,
            'kalshi_percentage': f"{kalshi_pct:.1f}%",
            'confidence_level': confidence,
            'actual_winner': game_result.get(f"{winner}_team", {}).get('name') if winner else None,
            'final_score': {
                'home': game_result.get('home_team', {}).get('score'),
                'away': game_result.get('away_team', {}).get('score')
            }
        }
        
        # Generate message
        if bet_won:
            if kalshi_pct >= 60:
                analysis['message'] = f"✅ Market prediction correct! The market was {confidence} ({kalshi_pct:.0f}%) that {team_name} would win, and they did."
            else:
                analysis['message'] = f"✅ Upset alert! Despite low odds ({kalshi_pct:.0f}%), {team_name} won!"
        else:
            if kalshi_pct >= 60:
                analysis['message'] = f"❌ Market prediction wrong. The market was {confidence} ({kalshi_pct:.0f}%) that {team_name} would win, but they lost."
            else:
                analysis['message'] = f"❌ Expected result. The market was {confidence} ({kalshi_pct:.0f}%) that {team_name} would win, and they lost as predicted."
        
        return analysis


# Global instance
espn = ESPNService()
