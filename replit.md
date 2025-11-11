# Overview

OddSense is a multi-sport prediction markets explorer built with Streamlit, integrating with the Kalshi prediction market API, The Odds API for real-time sportsbook betting odds, ESPN's public API for historical game data and player statistics, Google Gemini AI for game previews with player insights, and OpenAI for AI-powered market insights. The platform supports **NFL, NBA, NHL, and Soccer (Premier League)** markets, displaying them in a hierarchical structure with automatic categorization, centralized team name normalization, AI-generated game analysis with player highlights, multi-sportsbook odds comparison, and historical accuracy comparisons. The application provides a mobile-optimized experience, visual indicators for market assessment, and comprehensive market context to make informed trading decisions.

The business vision is to offer a user-friendly platform for exploring multi-sport prediction markets, enhancing accessibility and understanding for both casual fans and serious traders across major sports. By leveraging AI for insights, comparing predictions to actual results, supporting multiple sports leagues, and focusing on intuitive design, the project seeks to carve a niche in the sports prediction market analysis space.

# Recent Changes

**November 11, 2025 - Multi-Sport Platform Expansion**
- Expanded platform from NFL-only to multi-sport support: **NFL, NBA, NHL, and Soccer (Premier League)**
- Created centralized `sport_config.py` with complete team rosters (32 NFL, 30 NBA, 32 NHL, 20 Soccer teams) and variation maps for consistent team name normalization across all services
- Updated KalshiService, OddsAPIService, and ESPNService to accept sport parameter and use centralized team data with sport-specific endpoints
- Implemented manual per-sport service caching (`_SERVICE_CACHE`) to ensure distinct Kalshi/OddsAPI/ESPN instances per sport, avoiding Streamlit cache_resource issues
- Added multi-sport aggregation for "All" view that combines events from all sports with proper `_sport` metadata tagging
- Updated navigation to replace MLB with Soccer and enable sport filtering (All, NFL, NBA, Soccer, NHL)
- Fixed critical navigation bugs:
  - Detail links now pass event's actual sport (from `_sport` metadata) instead of current filter
  - Added robust legacy link handling with auto-detection that searches all sports when receiving invalid sport parameter
- Updated detail page for sport-specific stats using stat_categories from config (passing for NFL, points for NBA, goals for NHL/Soccer)
- Architect-reviewed and production-ready multi-sport core implementation

**November 6, 2025 - The Odds API Migration & Player Stats Integration**
- Migrated sportsbook odds from SportsGameOdds API to The Odds API for better reliability and 500 free requests/month
- Added ESPN player statistics integration showing team stat leaders (passing, rushing, receiving) on detail pages
- Implemented collapsible player stats section with side-by-side team comparison
- Enhanced ESPN service with methods: get_team_leaders(), get_player_stats(), get_team_roster(), get_team_id_by_name()
- Updated odds API service with proper American odds conversion, consensus calculation, and best odds discovery
- Fixed all method signatures and data structures to match The Odds API response format
- Removed deprecated SportsGameOdds service file
- Updated all documentation to reflect The Odds API as the primary sportsbook data source
- **Enhanced AI Game Preview formatting**: Redesigned with purple-to-indigo gradient background, larger text (1.15rem), improved line spacing (1.8), sentence breaks for better readability, rounded corners, and box shadows for premium visual appeal

**Earlier - Dark Mode Redesign & Rebranding**
- Completely redesigned app with Figma-like dark mode aesthetics
- Rebranded from "NFL Kalshi Markets" to "OddSense" throughout the application
- Updated Streamlit theme configuration with dark slate backgrounds (#0f172a, #1e293b) and indigo primary color (#6366f1)
- Redesigned market cards with dark backgrounds, improved hover effects, and better visual hierarchy
- Fixed critical HTML rendering bug where market card probability badges and quality labels were displaying as raw HTML code blocks instead of rendering properly
- Enhanced typography with better font weights, letter spacing, and modern spacing throughout

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

The application utilizes **Streamlit** for its UI, offering a Python-native, reactive web framework. It implements a multi-page pattern with a market listing page and a detail view.

- **Market Listing Page**: Displays markets hierarchically (Category → Matchup → Combined Markets) with a single row showing both teams and their probabilities. Features search, pagination, and mobile-first responsive design with custom CSS.
- **Visual Odds Quality Indicators**: Color-coded system (Green, Blue, Orange) provides quick assessment of market signals on market cards.
- **Redesigned Market Cards**: Clean white cards with a colored left border, large probability badge, and value indicator label (e.g., "Strong Favorite").
- **Enhanced Market Cards**: Display 24h volume, open interest, time remaining, and sportsbook consensus odds directly on listing page for quick comparison.
- **Detail View**: Features AI-generated game preview with player insights, visual indicators, shortened metric labels (e.g., "24h Volume"), real-time sportsbook odds comparison showing Kalshi prediction market vs multiple sportsbooks (DraftKings, FanDuel, BetMGM, etc.) side-by-side with consensus averages and best available odds, historical accuracy comparison with ESPN game results, and initially collapsed sections for Order Book and All Event Contracts to optimize mobile viewing.
- **AI Game Preview**: Powered by Google Gemini 2.5 Flash, each detail page displays a 3-4 sentence analysis highlighting key players to watch, recent performance stats, and critical matchup factors.
- **Session State Management**: Used for navigation between combined and single markets.

## Backend Architecture

The architecture follows a **service-oriented approach** to separate concerns:

- `sport_config.py`: Centralized configuration for all sports (NFL, NBA, NHL, Soccer) containing team rosters, name variations, API sport keys, stat categories, and helper functions for team normalization across all services.
- `kalshi_service.py`: Manages all interactions with the Kalshi API with multi-sport support. Accepts sport parameter, uses centralized team data for normalization, and builds sport-specific series tickers.
- `odds_api_service.py`: Fetches real-time betting odds from multiple sportsbooks via The Odds API with multi-sport support. Accepts sport parameter, uses centralized team variations, includes American odds-to-probability conversion, consensus calculation across bookmakers, best odds discovery, and 5-minute caching to minimize API calls.
- `espn_service.py`: Fetches historical game results and player statistics from ESPN's public API with multi-sport support. Sport-aware BASE_URLs built from config, includes methods for team stat leaders, player stats, team rosters, and historical game accuracy comparison.
- `gemini_service.py`: Generates AI-powered game previews with player insights using Google Gemini 2.5 Flash. Creates engaging 3-4 sentence summaries highlighting key players, recent stats, and tactical matchups.
- `openai_service.py`: Handles the generation of AI-powered market analyses.
- `app.py`: Orchestrates the application logic and serves the presentation layer with multi-sport support, manual per-sport service caching, and sport-specific data fetching.

### Market Normalization Layer

The `KalshiService` includes a pipeline for transforming raw Kalshi API data into a display-ready format:

- **Category Mapping**: Parses event tickers to map markets into high-level categories (e.g., "Games", "Passing Yards").
- **Team Name Resolution**: Uses centralized sport_config team dictionaries with comprehensive variation maps to expand abbreviations and normalize team names across all sports (NFL, NBA, NHL, Soccer).
- **Display Name Generation**: Prioritizes API titles/subtitles, with fallbacks and team abbreviation expansion for clarity.
- **Probability & Volume Calculation**: Implements a fallback chain for probability (yes_bid → last_price → mid_price) and volume (volume → volume_24h → liquidity).
- **Market Pairing & Combination**: Groups and combines opposing contracts for the same game into a single UI element, calculating probabilities and combining relevant data for both teams.

### Multi-Sport Service Management

The application implements **manual per-sport service caching** to ensure correct sport-specific instances:

- **Service Accessor Pattern**: `get_kalshi(sport)`, `get_odds_api(sport)`, `get_espn(sport)` functions provide sport-specific service instances
- **Manual Caching Dictionary**: `_SERVICE_CACHE` stores distinct instances per sport to avoid Streamlit's @st.cache_resource issues with sport-specific initialization
- **Sport Metadata Tagging**: Events in "All" view include `_sport` metadata for proper routing to detail pages
- **Legacy Link Handling**: Detail page validates sport parameter and auto-detects event's actual sport by searching all sports when invalid sport received
- **Sport-Specific Stats**: Detail page uses sport_config stat_categories (e.g., "passing" for NFL, "points" for NBA, "goals" for NHL/Soccer)

## Pagination Implementation

The application uses **server-side cursor-based pagination** for fetching market data from the Kalshi API. This ensures fresh data for each page and consistent page sizes by requesting sport-specific series tickers (e.g., `series_ticker=KXNFLGAME` for NFL, `series_ticker=KXNBAGAME` for NBA, etc.). The "All" view aggregates events from all sports by fetching each sport's markets separately and combining them with `_sport` metadata tagging.

## Data Visualization

**Plotly** is used for interactive charts and graphs, enabling rich visualizations of market data such as price movements and volume over time.

## AI Integration

The application integrates with two AI services:

### Google Gemini AI (Game Previews)
- **Model**: Gemini 2.5 Flash
- **Service**: `gemini_service.py`
- **Purpose**: Generates engaging game previews with player-specific insights for each matchup
- **Features**:
  - Names 2-3 key players per team with positions (e.g., "QB Russell Wilson", "DE Maxx Crosby")
  - Recent performance stats and trends
  - Tactical matchup analysis
  - Context from Kalshi probabilities and sportsbook odds
- **Display**: Appears on detail pages in "🤖 AI Game Preview" section
- **Authentication**: Requires `GEMINI_API_KEY` environment variable (from Google AI Studio)

### OpenAI (Market Analysis)
- **Model**: GPT-5 (August 2025 release)
- **Service**: `openai_service.py`
- **Purpose**: Generates concise 3-4 sentence market analysis briefs
- **Configuration**: Uses `max_completion_tokens=5000` and `reasoning_effort="low"` for simple analysis tasks
- **Authentication**: Requires `OPENAI_API_KEY` environment variable

# External Dependencies

## Third-Party APIs

### Kalshi Trading API

- **Endpoint**: `https://api.elections.kalshi.com/trade-api/v2`
- **Authentication**: Uses unauthenticated public endpoints.
- **Purpose**: Fetches prediction markets for multiple sports, detailed market information, historical price data, and order books.
- **Multi-Sport Support**: 
  - NFL: `series_ticker=KXNFLGAME`
  - NBA: `series_ticker=KXNBAGAME`
  - NHL: `series_ticker=KXNHLGAME`
  - Soccer: `series_ticker=KXSOCCERGAME`
- **Filtering**: Uses sport-specific series tickers to retrieve game outcome contracts for each league.

### The Odds API

- **Endpoint**: `https://api.the-odds-api.com/v4/sports/{sport_key}/odds`
- **Authentication**: Requires `ODDS_API_KEY` environment variable (query parameter).
- **Free Tier**: 500 requests per month with no credit card required
- **Multi-Sport Support**:
  - NFL: `americanfootball_nfl`
  - NBA: `basketball_nba`
  - NHL: `icehockey_nhl`
  - Soccer: `soccer_epl` (Premier League)
- **Purpose**: Fetches real-time betting odds from multiple sportsbooks for multi-sport games.
- **Features**:
  - **Multi-Sportsbook Coverage**: Aggregates odds from 70+ bookmakers including DraftKings, FanDuel, BetMGM, Caesars, and more
  - **Live Odds**: Real-time moneyline (h2h), spreads, and totals
  - **Consensus Calculation**: Computes average implied probability across all bookmakers
  - **Best Odds Discovery**: Identifies the best available odds for each team
  - **American Odds Format**: Displays traditional sportsbook format (e.g., -150, +200)
  - **Odds Conversion**: Converts American moneyline to implied win probability
    - Favorites (negative): `-150` → `60.0%` via `abs(odds) / (abs(odds) + 100)`
    - Underdogs (positive): `+200` → `33.3%` via `100 / (odds + 100)`
  - **Team Name Normalization**: Fuzzy matching to handle variations between APIs
- **Odds Display**: Shows comprehensive comparison table with:
  - OddSense prediction market probability
  - Sportsbook consensus average (across all bookmakers)
  - Best available odds with bookmaker name
  - Expandable detailed view of all individual sportsbook odds
- **Use Case**: Enables arbitrage opportunity detection, market consensus validation, and informed betting decisions
- **Rate Limits**: 500 requests/month on free tier; implementation uses 5-minute caching to minimize API calls
- **Caching Strategy**: Class-level cache shared across instances with throttling to prevent retry storms on failures

### ESPN Public API

- **Endpoint**: `http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}`
- **Authentication**: No authentication required (unofficial public API).
- **Multi-Sport Support**:
  - NFL: `football/nfl`
  - NBA: `basketball/nba`
  - NHL: `hockey/nhl`
  - Soccer: `soccer/eng.1` (Premier League)
- **Purpose**: Fetches historical game results and player statistics for comprehensive multi-sport game analysis.
- **Features**:
  - **Game Results**: Scoreboard data, final scores, winners, and game status for accuracy comparison
  - **Player Statistics**: Team stat leaders by category (passing, rushing, receiving, defense)
  - **Team Rosters**: Full roster information with player positions and details
  - **Historical Data**: Access to games dating back to 1999+
  - **Fuzzy Matching**: Team name matching handles variations between different APIs
  - **Flexible Search**: ±2 day search window for game date flexibility
  - **Team Mapping**: Comprehensive multi-sport team ID mapping (32 NFL, 30 NBA, 32 NHL, 20 Soccer teams)
- **New Methods**:
  - `get_team_leaders(team_name, category)`: Returns top 3 stat leaders for a team
  - `get_player_stats(player_id)`: Fetches detailed statistics for individual players
  - `get_team_roster(team_id)`: Retrieves complete team roster
  - `get_team_id_by_name(team_name)`: Maps team names to ESPN team IDs
- **Note**: Unofficial API - structure may change without notice.

### OpenAI API

- **Model**: GPT-5 (August 2025 release).
- **Authentication**: Requires `OPENAI_API_KEY` environment variable.
- **Purpose**: Generates natural language market analysis and insights based on provided market data.
- **Configuration**: Uses `max_completion_tokens=5000` and `reasoning_effort="low"`.

## Python Libraries

- **streamlit**: Web application framework.
- **pandas**: Data manipulation.
- **plotly**: Interactive data visualization.
- **requests**: HTTP client.
- **openai**: Official OpenAI Python client.

## Environment Configuration

- `OPENAI_API_KEY`: Environment variable for OpenAI API access.
- `GEMINI_API_KEY`: Environment variable for Google Gemini AI access (game previews with player insights).
- `ODDS_API_KEY`: Environment variable for The Odds API access (real-time sportsbook odds - 500 free requests/month).