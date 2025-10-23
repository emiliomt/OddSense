# Overview

This is an NFL prediction markets explorer built with Streamlit that integrates with the Kalshi betting API and OpenAI for AI-powered market insights. The application displays markets in a hierarchical structure matching Kalshi's UI, with automatic categorization, team name normalization, and AI-generated analysis powered by GPT-5.

# Recent Changes (October 23, 2025)

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
- A market listing page with hierarchical grouping (Category → Matchup → Markets)
- Search and pagination functionality
- Detail view for individual markets with AI-generated insights
- Session state management for navigation and caching

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

**Output Fields Added to Each Market**:
- `category`: High-level category name (e.g., "Games", "Passing Yards")
- `matchup`: Team matchup (e.g., "Minnesota Vikings @ Los Angeles Chargers") or "General"
- `display_name`: Intuitive market name with expanded team names
- `display_probability`: Decimal probability (0-1)
- `display_probability_pct`: Formatted percentage string
- `display_volume`: Correct volume field value
- `market_type_code`: Raw market type for reference

## Pagination Implementation
The app implements **true server-side cursor-based pagination**:
- Fetches fresh data from Kalshi API for each page navigation
- Stores cursors in session state (`page_cursors` list)
- Filters for NFL markets client-side (~98.5% of markets are NFL)
- Returns all filtered results without truncation to avoid losing markets
- Pages may vary slightly in size (95-100 markets) due to client-side NFL filtering
- Next/Previous buttons trigger new API calls with appropriate cursors

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
- **Purpose**: Fetches NFL prediction market data including prices, volume, and open interest
- **Key Methods**: 
  - `GET /markets` with pagination cursor support
  - Filtering for NFL-specific markets client-side (event_ticker contains "NFL")
  - `GET /markets/{ticker}` for detailed market information
  - `GET /markets/{ticker}/history` for price history
  - `GET /markets/{ticker}/orderbook` for current order book
- **Data Structure**: 
  - Prices in cents (0-100): `yes_bid`, `no_bid`, `last_price`, `mid_price`
  - Volume fields: `volume`, `volume_24h`, `liquidity`
  - Multivariate markets have comma-separated leg descriptions in title
- **Note**: API does not support server-side NFL filtering via parameters, so client-side filtering is applied

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
1. User searches/browses markets → Kalshi API call with cursor-based pagination
2. Market data filtered for NFL markets client-side
3. Markets normalized through `KalshiService.normalize_market()`
4. Markets grouped into nested structure: {category: {matchup: [markets]}}
5. Displayed with Category → Matchup → Markets hierarchy
6. User selects market → Detail page loads with additional API calls
7. OpenAI generates analysis for selected market
8. Results displayed with Plotly visualizations

**Note**: The application currently operates in read-only mode without user authentication. Future enhancements may include authenticated trading capabilities.

# Known Limitations & Behavior Notes
- Client-side search only filters current page results (not across all pages)
- Page sizes may vary slightly (95-100 markets) due to NFL filtering after fetching
- Some markets may lack historical price data (handled gracefully with info messages)
- OpenAI API quota limitations may prevent AI brief generation (displays error message)
- **Multivariate/Parlay Markets**: Markets in "Same Game Parlays" category may show the same player multiple times (e.g., "Ladd McConkey,Justin Herbert: 250+,Ladd McConkey: 60+"). This is NOT a bug—it represents combination bets where a player appears in multiple bet legs (e.g., "Ladd McConkey scores TD" AND "Ladd McConkey 60+ yards"). This reflects Kalshi's actual market structure.
- Markets with no active bids show 0% probability and $0 volume (expected behavior, not a bug)
