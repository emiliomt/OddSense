# Overview

This is an NFL prediction markets explorer built with Streamlit that integrates with the Kalshi betting API and OpenAI for AI-powered market insights. The application displays markets in a hierarchical structure matching Kalshi's UI, with automatic categorization, team name normalization, and AI-generated analysis powered by GPT-5.

# Recent Changes (October 23, 2025)

## Latest Update: Combined Market Pairs
- **Markets now combine paired contracts** - Each game shows as a single row with both teams
- Display format: Shows both teams with their probabilities (e.g., "SEA: 45% | WAS: 55%")
- **Reduced market count by half** - ~13 games instead of ~25 individual contracts
- Detail page allows selecting which team's contract to view via radio buttons
- Session state properly manages navigation between combined markets

## Game Contracts Only
- **Switched to Professional Football Game series filtering** using `series_ticker=KXNFLGAME`
- App now displays **only standalone game outcome contracts**
- Each market represents one team winning a specific game (e.g., "Seattle at Washington Winner?")
- **Removed multivariate/parlay markets** from the display
- Clean, simple market names without comma-separated conditions

## Market Display Reorganization
- Implemented **normalization layer** that transforms raw Kalshi API data into display-ready format
- Markets now grouped by **high-level categories** (Games, Passing Yards, Rushing Yards, Anytime Touchdowns, etc.)
- Within each category, markets are **grouped by game matchup** (e.g., "Minnesota Vikings @ Los Angeles Chargers")
- Display names show **intuitive titles** instead of contract IDs
- **Fixed probability calculation** to use yes_bid → last_price → mid_price fallback chain
- **Fixed volume display** to use correct API field (volume > volume_24h > liquidity)
- **Team abbreviation expansion** replaces "Los Angeles C" with "Los Angeles Chargers" etc.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses **Streamlit** as the web framework, providing a Python-based UI with built-in state management and reactive components. The interface follows a multi-page pattern with:
- A market listing page with hierarchical grouping (Category → Matchup → Combined Markets)
- Each row shows both teams with their probabilities in one combined view
- Search and pagination functionality
- Detail view with team selection radio buttons to view either team's contract
- Session state management for navigation between combined/single markets

**Pros**: Fast development, Python-native, built-in caching
**Cons**: Limited customization compared to React/Vue, server-side rendering only

## Backend Architecture
The application follows a **service-oriented architecture** with separation of concerns:
- `kalshi_service.py` handles all Kalshi API interactions with normalization layer
- `openai_service.py` manages AI analysis generation
- `app.py` serves as the presentation layer and orchestrator

### Market Normalization Layer
The `KalshiService` class includes a comprehensive normalization pipeline that transforms raw API data:

**Category Mapping**:
- Parses event ticker pattern: `KXNFL{TYPE}-{DATE}{TEAM1}{TEAM2}`
- Maps TYPE codes to categories: GAME→"Games", PASSYDS→"Passing Yards", RSHYDS→"Rushing Yards", etc.
- Handles multivariate markets as "Same Game Parlays"

**Team Name Resolution**:
- Includes complete NFL team code dictionary (MIN→"Minnesota Vikings", LAC→"Los Angeles Chargers", etc.)
- Parses team codes by scanning from end of ticker to handle 2-3 letter codes correctly
- Expands abbreviated team names in API titles ("Los Angeles C" → "Los Angeles Chargers")

**Display Name Generation**:
- Prefers API title/subtitle when available
- Applies team abbreviation expansion to multivariate market titles
- Fallback ticker parsing for player prop markets

**Probability & Volume Calculation**:
- Probability: uses yes_bid/100 (cents to decimal), fallback chain: yes_bid → last_price → mid_price
- Volume: prefers `volume` field, fallback to `volume_24h`, then `liquidity`

**Market Pairing & Combination**:
- Groups markets by `event_ticker` to identify opposing contracts
- Combines paired markets using `combine_market_pair()` method
- Stores both team contracts as `away_contract` and `home_contract`
- Calculates probabilities for both teams with fallback chain
- Uses maximum volume from both contracts

**Output Fields Added to Combined Markets**:
- `category`: High-level category name (e.g., "Games")
- `matchup`: Team matchup (e.g., "Minnesota Vikings @ Los Angeles Chargers")
- `display_name`: Game title from API
- `away_team`, `home_team`: Full team names
- `away_ticker`, `home_ticker`: Individual contract tickers
- `away_probability`, `home_probability`: Win probabilities for each team
- `away_probability_pct`, `home_probability_pct`: Formatted percentage strings
- `display_volume`: Combined volume
- `away_contract`, `home_contract`: Full contract data for both teams
- `market_type_code`: Raw market type for reference

## Pagination Implementation
The app implements **true server-side cursor-based pagination**:
- Fetches fresh data from Kalshi API for each page navigation using `series_ticker=KXNFLGAME`
- Stores cursors in session state (`page_cursors` list)
- Returns all game outcome markets (no client-side filtering needed)
- Next/Previous buttons trigger new API calls with appropriate cursors
- Consistent page sizes since all results are game markets

## Data Visualization
**Plotly** is used for interactive charts and graphs (imported in `app.py`). This was chosen over simpler charting libraries to provide rich, interactive visualizations of market data including price movements, volume, and probability distributions.

**Alternatives considered**: Matplotlib (less interactive), Altair (simpler but less flexible)

## AI Integration
The application uses **OpenAI's GPT-5** (latest model as of August 2025) to generate market analysis briefs. The `OpenAIService` class:
- Constructs detailed prompts with market data
- Formats probability implications from bid prices
- Generates concise 3-4 sentence analyses

The AI brief covers market sentiment, probability analysis, and contextual insights to help users make informed decisions.

# External Dependencies

## Third-Party APIs

### Kalshi Trading API
- **Endpoint**: `https://api.elections.kalshi.com/trade-api/v2`
- **Authentication**: Currently using unauthenticated public endpoints
- **Purpose**: Fetches Professional Football Game prediction markets
- **Key Methods**: 
  - `GET /markets?series_ticker=KXNFLGAME` to fetch game outcome contracts
  - Pagination cursor support for navigating through markets
  - `GET /markets/{ticker}` for detailed market information
  - `GET /markets/{ticker}/history` for price history
  - `GET /markets/{ticker}/orderbook` for current order book
- **Data Structure**: 
  - Prices in cents (0-100): `yes_bid`, `no_bid`, `last_price`, `mid_price`
  - Volume fields: `volume`, `volume_24h`, `liquidity`
  - Game markets are simple binary outcomes (one team wins)
- **Filtering**: Uses `series_ticker=KXNFLGAME` to fetch only Professional Football Game markets server-side

### OpenAI API
- **Model**: GPT-5 (current as of August 2025)
- **Authentication**: API key via `OPENAI_API_KEY` environment variable
- **Purpose**: Generates natural language market analysis and insights
- **Integration**: Python OpenAI client library
- **Configuration**: No temperature parameter (GPT-5 limitation), uses max_completion_tokens instead of max_tokens

## Python Libraries
- **streamlit**: Web application framework and UI components
- **pandas**: Data manipulation and tabular display
- **plotly**: Interactive data visualization
- **requests**: HTTP client for API calls
- **openai**: Official OpenAI Python client

## Environment Configuration
- `OPENAI_API_KEY`: Required environment variable for OpenAI API access
- No database configuration currently required (stateless application)
- Session state managed in-memory by Streamlit

## Data Flow
1. User searches/browses markets → Kalshi API call with `series_ticker=KXNFLGAME` and cursor-based pagination
2. Game outcome markets returned from API (paired contracts for each game)
3. Markets grouped by `event_ticker` to identify pairs
4. Paired markets combined through `KalshiService.combine_market_pair()`
5. Combined markets grouped into nested structure: {category: {matchup: [combined_markets]}}
6. Displayed with Category → Matchup → Combined Markets hierarchy (one row per game)
7. User selects game → Detail page shows both teams with radio button selector
8. User selects team → Contract data loaded for chosen team
9. OpenAI generates analysis for selected contract
10. Results displayed with Plotly visualizations

**Note**: The application currently operates in read-only mode without user authentication. Future enhancements may include authenticated trading capabilities.

# Known Limitations & Behavior Notes
- Client-side search only filters current page results (not across all pages)
- Some markets may lack historical price data (handled gracefully with info messages)
- OpenAI API quota limitations may prevent AI brief generation (displays error message)
- Markets with no active bids show 0% probability and $0 volume (expected behavior, not a bug)
- App displays **only game outcome contracts** - no player props, parlays, or other market types
- **Each game displays as one combined row** - API returns 2 contracts per game (one per team) which are merged in the UI
- Probabilities may not sum exactly to 100% due to bid-ask spreads and market inefficiencies
