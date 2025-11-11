"""
ESPN API Service
Fetches historical game data from ESPN's unofficial public API.
Supports NFL, NBA, NHL, and Soccer.
"""

import requests
from datetime import datetime, timezone
from typing import Optional, Dict, List
import logging
from sport_config import get_sport_config, get_teams_for_sport

logger = logging.getLogger(__name__)


class ESPNService:
    """Service for fetching multi-sport game data from ESPN API."""
    
    def __init__(self, sport: str = "nfl"):
        self.sport = sport.lower()
        self.sport_config = get_sport_config(self.sport)
        
        # Build sport-specific URLs from config
        espn_sport = self.sport_config.get("espn_sport", "football")
        espn_league = self.sport_config.get("espn_league", "nfl")
        
        self.BASE_URL = f"http://site.api.espn.com/apis/site/v2/sports/{espn_sport}/{espn_league}"
        self.CORE_API_URL = f"https://sports.core.api.espn.com/v2/sports/{espn_sport}/leagues/{espn_league}"
        
        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (compatible; OddSense/1.0)'
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
    
    def get_game_odds(self, game_id: str) -> Optional[Dict]:
        """
        Fetch betting odds for a specific game.
        
        Args:
            game_id: ESPN game ID (e.g., '401547402')
        
        Returns:
            Dict with odds data including moneyline, spread, over/under
        """
        # ESPN odds are in the game summary under competitions[0].odds
        summary = self.get_game_summary(game_id)
        
        if not summary or 'header' not in summary:
            return None
        
        try:
            # Extract odds from the summary
            competitions = summary.get('header', {}).get('competitions', [])
            if not competitions:
                logger.warning(f"No competitions found for game {game_id}")
                return None
            
            competition = competitions[0]
            odds_list = competition.get('odds', [])
            
            if not odds_list:
                logger.warning(f"No odds data found for game {game_id}")
                return None
            
            # Get the first odds provider (usually consensus or a major book)
            odds_data = odds_list[0] if odds_list else {}
            
            # Extract odds information
            result = {
                'provider': odds_data.get('provider', {}).get('name', 'Unknown'),
                'details': odds_data.get('details', ''),
                'over_under': odds_data.get('overUnder'),
                'spread': odds_data.get('spread'),
                'home_team_odds': {},
                'away_team_odds': {}
            }
            
            # Get home/away moneyline odds
            competitors = competition.get('competitors', [])
            for comp in competitors:
                team_id = comp.get('id')
                home_away = comp.get('homeAway', '')
                
                # Find odds for this team
                for odd in odds_list:
                    team_odds = None
                    if 'homeTeamOdds' in odd and home_away == 'home':
                        team_odds = odd.get('homeTeamOdds', {})
                    elif 'awayTeamOdds' in odd and home_away == 'away':
                        team_odds = odd.get('awayTeamOdds', {})
                    
                    if team_odds:
                        odds_info = {
                            'moneyline': team_odds.get('moneyLine'),
                            'spread_odds': team_odds.get('spreadOdds'),
                            'team_name': comp.get('team', {}).get('displayName', ''),
                            'team_abbreviation': comp.get('team', {}).get('abbreviation', '')
                        }
                        
                        # Convert moneyline to implied probability
                        if odds_info['moneyline']:
                            odds_info['implied_probability'] = self._moneyline_to_probability(odds_info['moneyline'])
                        
                        if home_away == 'home':
                            result['home_team_odds'] = odds_info
                        else:
                            result['away_team_odds'] = odds_info
                        break
            
            logger.info(f"Successfully fetched odds for game {game_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing odds data for game {game_id}: {e}")
            return None
    
    def _moneyline_to_probability(self, moneyline: int) -> float:
        """
        Convert American moneyline odds to implied probability.
        
        Args:
            moneyline: American odds (e.g., -150, +200)
        
        Returns:
            Implied probability as decimal (0-1)
        
        Examples:
            -150 (favorite) -> 60% (0.60)
            +200 (underdog) -> 33.3% (0.333)
        """
        if moneyline < 0:
            # Favorite: probability = |moneyline| / (|moneyline| + 100)
            return abs(moneyline) / (abs(moneyline) + 100)
        else:
            # Underdog: probability = 100 / (moneyline + 100)
            return 100 / (moneyline + 100)
    
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
    
    def get_team_roster(self, team_id: str) -> Optional[Dict]:
        """
        Fetch team roster with player information.
        
        Args:
            team_id: ESPN team ID (e.g., '1' for Falcons)
        
        Returns:
            Dict with roster data
        """
        url = f"{self.BASE_URL}/teams/{team_id}/roster"
        
        try:
            logger.info(f"Fetching roster for team {team_id}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched roster for team {team_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching roster for team {team_id}: {e}")
            return None
    
    def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """
        Fetch player statistics.
        
        Args:
            player_id: ESPN player ID
        
        Returns:
            Dict with player stats
        """
        url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}/stats"
        
        try:
            logger.info(f"Fetching stats for player {player_id}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully fetched stats for player {player_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching stats for player {player_id}: {e}")
            return None
    
    def get_team_id_by_name(self, team_name: str) -> Optional[str]:
        """
        Map team name to ESPN team ID (sport-specific).
        
        Returns:
            ESPN team ID as string, or None if not found
        """
        # ESPN team ID mappings by sport
        # NOTE: These IDs are ESPN-specific and different from other APIs
        nfl_ids = {
            'Arizona Cardinals': '22', 'Atlanta Falcons': '1', 'Baltimore Ravens': '33',
            'Buffalo Bills': '2', 'Carolina Panthers': '29', 'Chicago Bears': '3',
            'Cincinnati Bengals': '4', 'Cleveland Browns': '5', 'Dallas Cowboys': '6',
            'Denver Broncos': '7', 'Detroit Lions': '8', 'Green Bay Packers': '9',
            'Houston Texans': '34', 'Indianapolis Colts': '11', 'Jacksonville Jaguars': '30',
            'Kansas City Chiefs': '12', 'Las Vegas Raiders': '13', 'Los Angeles Chargers': '24',
            'Los Angeles Rams': '14', 'Miami Dolphins': '15', 'Minnesota Vikings': '16',
            'New England Patriots': '17', 'New Orleans Saints': '18', 'New York Giants': '19',
            'New York Jets': '20', 'Philadelphia Eagles': '21', 'Pittsburgh Steelers': '23',
            'San Francisco 49ers': '25', 'Seattle Seahawks': '26', 'Tampa Bay Buccaneers': '27',
            'Tennessee Titans': '10', 'Washington Commanders': '28',
        }
        
        # Select appropriate team map based on sport
        if self.sport == "nfl":
            team_map = nfl_ids
        else:
            # TODO: Add ESPN team IDs for NBA, NHL, Soccer
            # For now, return None for unsupported sports
            logger.warning(f"ESPN team IDs not yet implemented for {self.sport}")
            return None
        
        # Normalize team name using centralized data
        teams_data = get_teams_for_sport(self.sport)
        
        # Try to find canonical name from variations
        canonical_name = None
        team_name_lower = team_name.lower()
        
        for name, data in teams_data.items():
            # Check canonical name
            if name.lower() == team_name_lower:
                canonical_name = name
                break
            # Check abbreviation
            if data["abbr"].lower() == team_name_lower:
                canonical_name = name
                break
            # Check variations
            for variation in data["variations"]:
                if variation.lower() == team_name_lower:
                    canonical_name = name
                    break
            if canonical_name:
                break
        
        # Look up ESPN ID using canonical name
        if canonical_name and canonical_name in team_map:
            return team_map[canonical_name]
        
        # Fallback: partial match
        for key, value in team_map.items():
            if team_name_lower in key.lower() or key.lower() in team_name_lower:
                return value
        
        logger.warning(f"Could not find ESPN team ID for: {team_name} ({self.sport})")
        return None
    
    def get_team_leaders(self, team_name: str, category: str = 'passing') -> List[Dict]:
        """
        Get team stat leaders for a specific category.
        
        Args:
            team_name: Team name
            category: Stat category ('passing', 'rushing', 'receiving', 'defense')
        
        Returns:
            List of player dicts with stats
        """
        team_id = self.get_team_id_by_name(team_name)
        if not team_id:
            return []
        
        # Fetch team statistics page which includes leaders
        url = f"{self.BASE_URL}/teams/{team_id}/statistics"
        
        try:
            logger.info(f"Fetching team leaders for {team_name} (ID: {team_id})")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract leaders from the response
            leaders = []
            if 'leaders' in data:
                for leader_group in data['leaders']:
                    if leader_group.get('name', '').lower() == category.lower():
                        for leader in leader_group.get('leaders', []):
                            athlete = leader.get('athlete', {})
                            leaders.append({
                                'id': athlete.get('id'),
                                'name': athlete.get('displayName'),
                                'position': athlete.get('position', {}).get('abbreviation'),
                                'value': leader.get('displayValue'),
                                'stat': leader_group.get('displayName')
                            })
            
            logger.info(f"Found {len(leaders)} leaders for {team_name} in {category}")
            return leaders
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching team leaders for {team_name}: {e}")
            return []


# Note: Global instance removed - create sport-specific instances as needed
# Example: espn_nfl = ESPNService("nfl"), espn_nba = ESPNService("nba")
