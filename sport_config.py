from typing import Dict, List, Literal

SportType = Literal["nfl", "nba", "nhl", "soccer"]

# Centralized team rosters with abbreviations and variations
NFL_TEAMS = {
    "Arizona Cardinals": {"abbr": "ARI", "variations": ["Arizona", "Cardinals"]},
    "Atlanta Falcons": {"abbr": "ATL", "variations": ["Atlanta", "Falcons"]},
    "Baltimore Ravens": {"abbr": "BAL", "variations": ["Baltimore", "Ravens"]},
    "Buffalo Bills": {"abbr": "BUF", "variations": ["Buffalo", "Bills"]},
    "Carolina Panthers": {"abbr": "CAR", "variations": ["Carolina", "Panthers"]},
    "Chicago Bears": {"abbr": "CHI", "variations": ["Chicago", "Bears"]},
    "Cincinnati Bengals": {"abbr": "CIN", "variations": ["Cincinnati", "Bengals"]},
    "Cleveland Browns": {"abbr": "CLE", "variations": ["Cleveland", "Browns"]},
    "Dallas Cowboys": {"abbr": "DAL", "variations": ["Dallas", "Cowboys"]},
    "Denver Broncos": {"abbr": "DEN", "variations": ["Denver", "Broncos"]},
    "Detroit Lions": {"abbr": "DET", "variations": ["Detroit", "Lions"]},
    "Green Bay Packers": {"abbr": "GB", "variations": ["Green Bay", "Packers", "GNB"]},
    "Houston Texans": {"abbr": "HOU", "variations": ["Houston", "Texans"]},
    "Indianapolis Colts": {"abbr": "IND", "variations": ["Indianapolis", "Colts"]},
    "Jacksonville Jaguars": {"abbr": "JAX", "variations": ["Jacksonville", "Jaguars", "JAC"]},
    "Kansas City Chiefs": {"abbr": "KC", "variations": ["Kansas City", "Chiefs", "KAN"]},
    "Las Vegas Raiders": {"abbr": "LV", "variations": ["Las Vegas", "Raiders", "Oakland", "LVR"]},
    "Los Angeles Chargers": {"abbr": "LAC", "variations": ["Los Angeles Chargers", "LA Chargers", "Chargers"]},
    "Los Angeles Rams": {"abbr": "LAR", "variations": ["Los Angeles Rams", "LA Rams", "Rams"]},
    "Miami Dolphins": {"abbr": "MIA", "variations": ["Miami", "Dolphins"]},
    "Minnesota Vikings": {"abbr": "MIN", "variations": ["Minnesota", "Vikings"]},
    "New England Patriots": {"abbr": "NE", "variations": ["New England", "Patriots", "NWE"]},
    "New Orleans Saints": {"abbr": "NO", "variations": ["New Orleans", "Saints", "NOR"]},
    "New York Giants": {"abbr": "NYG", "variations": ["New York Giants", "NY Giants", "Giants"]},
    "New York Jets": {"abbr": "NYJ", "variations": ["New York Jets", "NY Jets", "Jets"]},
    "Philadelphia Eagles": {"abbr": "PHI", "variations": ["Philadelphia", "Eagles"]},
    "Pittsburgh Steelers": {"abbr": "PIT", "variations": ["Pittsburgh", "Steelers"]},
    "San Francisco 49ers": {"abbr": "SF", "variations": ["San Francisco", "49ers", "SFO"]},
    "Seattle Seahawks": {"abbr": "SEA", "variations": ["Seattle", "Seahawks"]},
    "Tampa Bay Buccaneers": {"abbr": "TB", "variations": ["Tampa Bay", "Buccaneers", "TAM"]},
    "Tennessee Titans": {"abbr": "TEN", "variations": ["Tennessee", "Titans"]},
    "Washington Commanders": {"abbr": "WAS", "variations": ["Washington", "Commanders", "Washington Football Team"]},
}

NBA_TEAMS = {
    "Atlanta Hawks": {"abbr": "ATL", "variations": ["Atlanta", "Hawks"]},
    "Boston Celtics": {"abbr": "BOS", "variations": ["Boston", "Celtics"]},
    "Brooklyn Nets": {"abbr": "BKN", "variations": ["Brooklyn", "Nets"]},
    "Charlotte Hornets": {"abbr": "CHA", "variations": ["Charlotte", "Hornets"]},
    "Chicago Bulls": {"abbr": "CHI", "variations": ["Chicago", "Bulls"]},
    "Cleveland Cavaliers": {"abbr": "CLE", "variations": ["Cleveland", "Cavaliers", "Cavs"]},
    "Dallas Mavericks": {"abbr": "DAL", "variations": ["Dallas", "Mavericks", "Mavs"]},
    "Denver Nuggets": {"abbr": "DEN", "variations": ["Denver", "Nuggets"]},
    "Detroit Pistons": {"abbr": "DET", "variations": ["Detroit", "Pistons"]},
    "Golden State Warriors": {"abbr": "GSW", "variations": ["Golden State", "Warriors", "GS"]},
    "Houston Rockets": {"abbr": "HOU", "variations": ["Houston", "Rockets"]},
    "Indiana Pacers": {"abbr": "IND", "variations": ["Indiana", "Pacers"]},
    "Los Angeles Clippers": {"abbr": "LAC", "variations": ["Los Angeles Clippers", "LA Clippers", "Clippers"]},
    "Los Angeles Lakers": {"abbr": "LAL", "variations": ["Los Angeles Lakers", "LA Lakers", "Lakers"]},
    "Memphis Grizzlies": {"abbr": "MEM", "variations": ["Memphis", "Grizzlies"]},
    "Miami Heat": {"abbr": "MIA", "variations": ["Miami", "Heat"]},
    "Milwaukee Bucks": {"abbr": "MIL", "variations": ["Milwaukee", "Bucks"]},
    "Minnesota Timberwolves": {"abbr": "MIN", "variations": ["Minnesota", "Timberwolves", "Wolves"]},
    "New Orleans Pelicans": {"abbr": "NOP", "variations": ["New Orleans", "Pelicans", "NO"]},
    "New York Knicks": {"abbr": "NYK", "variations": ["New York Knicks", "NY Knicks", "Knicks"]},
    "Oklahoma City Thunder": {"abbr": "OKC", "variations": ["Oklahoma City", "Thunder"]},
    "Orlando Magic": {"abbr": "ORL", "variations": ["Orlando", "Magic"]},
    "Philadelphia 76ers": {"abbr": "PHI", "variations": ["Philadelphia", "76ers", "Sixers"]},
    "Phoenix Suns": {"abbr": "PHX", "variations": ["Phoenix", "Suns"]},
    "Portland Trail Blazers": {"abbr": "POR", "variations": ["Portland", "Trail Blazers", "Blazers"]},
    "Sacramento Kings": {"abbr": "SAC", "variations": ["Sacramento", "Kings"]},
    "San Antonio Spurs": {"abbr": "SAS", "variations": ["San Antonio", "Spurs"]},
    "Toronto Raptors": {"abbr": "TOR", "variations": ["Toronto", "Raptors"]},
    "Utah Jazz": {"abbr": "UTA", "variations": ["Utah", "Jazz"]},
    "Washington Wizards": {"abbr": "WAS", "variations": ["Washington", "Wizards"]},
}

NHL_TEAMS = {
    "Anaheim Ducks": {"abbr": "ANA", "variations": ["Anaheim", "Ducks"]},
    "Arizona Coyotes": {"abbr": "ARI", "variations": ["Arizona", "Coyotes"]},
    "Boston Bruins": {"abbr": "BOS", "variations": ["Boston", "Bruins"]},
    "Buffalo Sabres": {"abbr": "BUF", "variations": ["Buffalo", "Sabres"]},
    "Calgary Flames": {"abbr": "CGY", "variations": ["Calgary", "Flames"]},
    "Carolina Hurricanes": {"abbr": "CAR", "variations": ["Carolina", "Hurricanes", "Canes"]},
    "Chicago Blackhawks": {"abbr": "CHI", "variations": ["Chicago", "Blackhawks"]},
    "Colorado Avalanche": {"abbr": "COL", "variations": ["Colorado", "Avalanche", "Avs"]},
    "Columbus Blue Jackets": {"abbr": "CBJ", "variations": ["Columbus", "Blue Jackets"]},
    "Dallas Stars": {"abbr": "DAL", "variations": ["Dallas", "Stars"]},
    "Detroit Red Wings": {"abbr": "DET", "variations": ["Detroit", "Red Wings"]},
    "Edmonton Oilers": {"abbr": "EDM", "variations": ["Edmonton", "Oilers"]},
    "Florida Panthers": {"abbr": "FLA", "variations": ["Florida", "Panthers"]},
    "Los Angeles Kings": {"abbr": "LAK", "variations": ["Los Angeles Kings", "LA Kings", "Kings"]},
    "Minnesota Wild": {"abbr": "MIN", "variations": ["Minnesota", "Wild"]},
    "Montreal Canadiens": {"abbr": "MTL", "variations": ["Montreal", "Canadiens", "Habs"]},
    "Nashville Predators": {"abbr": "NSH", "variations": ["Nashville", "Predators", "Preds"]},
    "New Jersey Devils": {"abbr": "NJD", "variations": ["New Jersey", "Devils", "NJ"]},
    "New York Islanders": {"abbr": "NYI", "variations": ["New York Islanders", "NY Islanders", "Islanders"]},
    "New York Rangers": {"abbr": "NYR", "variations": ["New York Rangers", "NY Rangers", "Rangers"]},
    "Ottawa Senators": {"abbr": "OTT", "variations": ["Ottawa", "Senators", "Sens"]},
    "Philadelphia Flyers": {"abbr": "PHI", "variations": ["Philadelphia", "Flyers"]},
    "Pittsburgh Penguins": {"abbr": "PIT", "variations": ["Pittsburgh", "Penguins", "Pens"]},
    "San Jose Sharks": {"abbr": "SJS", "variations": ["San Jose", "Sharks", "SJ"]},
    "Seattle Kraken": {"abbr": "SEA", "variations": ["Seattle", "Kraken"]},
    "St. Louis Blues": {"abbr": "STL", "variations": ["St. Louis", "St Louis", "Blues"]},
    "Tampa Bay Lightning": {"abbr": "TBL", "variations": ["Tampa Bay", "Lightning", "TB"]},
    "Toronto Maple Leafs": {"abbr": "TOR", "variations": ["Toronto", "Maple Leafs", "Leafs"]},
    "Vancouver Canucks": {"abbr": "VAN", "variations": ["Vancouver", "Canucks"]},
    "Vegas Golden Knights": {"abbr": "VGK", "variations": ["Vegas", "Golden Knights", "Knights"]},
    "Washington Capitals": {"abbr": "WSH", "variations": ["Washington", "Capitals", "Caps"]},
    "Winnipeg Jets": {"abbr": "WPG", "variations": ["Winnipeg", "Jets"]},
}

SOCCER_TEAMS = {
    "Arsenal": {"abbr": "ARS", "variations": ["Arsenal"]},
    "Aston Villa": {"abbr": "AVL", "variations": ["Aston Villa", "Villa"]},
    "Bournemouth": {"abbr": "BOU", "variations": ["Bournemouth", "AFC Bournemouth"]},
    "Brentford": {"abbr": "BRE", "variations": ["Brentford"]},
    "Brighton": {"abbr": "BHA", "variations": ["Brighton", "Brighton & Hove Albion"]},
    "Chelsea": {"abbr": "CHE", "variations": ["Chelsea"]},
    "Crystal Palace": {"abbr": "CRY", "variations": ["Crystal Palace", "Palace"]},
    "Everton": {"abbr": "EVE", "variations": ["Everton"]},
    "Fulham": {"abbr": "FUL", "variations": ["Fulham"]},
    "Ipswich Town": {"abbr": "IPS", "variations": ["Ipswich", "Ipswich Town"]},
    "Leicester City": {"abbr": "LEI", "variations": ["Leicester", "Leicester City"]},
    "Liverpool": {"abbr": "LIV", "variations": ["Liverpool"]},
    "Manchester City": {"abbr": "MCI", "variations": ["Manchester City", "Man City"]},
    "Manchester United": {"abbr": "MUN", "variations": ["Manchester United", "Man United", "Man Utd"]},
    "Newcastle": {"abbr": "NEW", "variations": ["Newcastle", "Newcastle United"]},
    "Nottingham Forest": {"abbr": "NFO", "variations": ["Nottingham Forest", "Forest"]},
    "Southampton": {"abbr": "SOU", "variations": ["Southampton"]},
    "Tottenham": {"abbr": "TOT", "variations": ["Tottenham", "Tottenham Hotspur", "Spurs"]},
    "West Ham": {"abbr": "WHU", "variations": ["West Ham", "West Ham United"]},
    "Wolverhampton": {"abbr": "WOL", "variations": ["Wolverhampton", "Wolves", "Wolverhampton Wanderers"]},
}

SPORTS_CONFIG: Dict[str, Dict] = {
    "nfl": {
        "display_name": "NFL",
        "icon": "🏈",
        "kalshi_series": "KXNFLGAME",
        "odds_api_key": "americanfootball_nfl",
        "espn_sport": "football",
        "espn_league": "nfl",
        "stat_categories": ["passing", "rushing", "receiving"],
        "stat_labels": ["Passing", "Rushing", "Receiving"],
        "position_labels": ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "K", "P"],
        "team_count": 32,
        "teams": NFL_TEAMS
    },
    "nba": {
        "display_name": "NBA",
        "icon": "🏀",
        "kalshi_series": "KXNBAGAME",
        "odds_api_key": "basketball_nba",
        "espn_sport": "basketball",
        "espn_league": "nba",
        "stat_categories": ["points", "rebounds", "assists"],
        "stat_labels": ["Points", "Rebounds", "Assists"],
        "position_labels": ["PG", "SG", "SF", "PF", "C"],
        "team_count": 30,
        "teams": NBA_TEAMS
    },
    "nhl": {
        "display_name": "NHL",
        "icon": "🏒",
        "kalshi_series": "KXNHLGAME",
        "odds_api_key": "icehockey_nhl",
        "espn_sport": "hockey",
        "espn_league": "nhl",
        "stat_categories": ["goals", "assists", "points"],
        "stat_labels": ["Goals", "Assists", "Points"],
        "position_labels": ["C", "LW", "RW", "D", "G"],
        "team_count": 32,
        "teams": NHL_TEAMS
    },
    "soccer": {
        "display_name": "Soccer",
        "icon": "⚽",
        "kalshi_series": "KXSOCCERGAME",
        "odds_api_key": "soccer_epl",
        "espn_sport": "soccer",
        "espn_league": "eng.1",
        "stat_categories": ["goals", "assists", "saves"],
        "stat_labels": ["Goals", "Assists", "Saves"],
        "position_labels": ["GK", "DF", "MF", "FW"],
        "team_count": 20,
        "teams": SOCCER_TEAMS,
        "alt_leagues": {
            "Premier League": "eng.1",
            "Champions League": "uefa.champions",
            "La Liga": "esp.1",
            "Bundesliga": "ger.1",
            "Serie A": "ita.1",
            "Ligue 1": "fra.1",
            "MLS": "usa.1"
        }
    }
}

def get_sport_config(sport: str) -> Dict:
    """Get configuration for a specific sport."""
    return SPORTS_CONFIG.get(sport.lower(), SPORTS_CONFIG["nfl"])

def get_all_sports() -> List[str]:
    """Get list of all supported sports."""
    return list(SPORTS_CONFIG.keys())

def is_valid_sport(sport: str) -> bool:
    """Check if a sport is supported."""
    return sport.lower() in SPORTS_CONFIG

def get_teams_for_sport(sport: str) -> Dict:
    """Get team roster for a specific sport."""
    config = get_sport_config(sport)
    return config.get("teams", {})

def build_team_variations_map(sport: str) -> Dict[str, str]:
    """Build a map of team variations to canonical names for normalization."""
    teams = get_teams_for_sport(sport)
    variations_map = {}
    
    for canonical_name, team_data in teams.items():
        # Add abbreviation
        variations_map[team_data["abbr"]] = canonical_name
        # Add all variations
        for variation in team_data["variations"]:
            variations_map[variation] = canonical_name
        # Add canonical name itself
        variations_map[canonical_name] = canonical_name
    
    return variations_map
