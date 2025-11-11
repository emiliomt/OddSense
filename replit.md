# Overview

OddSense is a multi-sport prediction markets explorer built with Streamlit, integrating with the Kalshi prediction market API, The Odds API for real-time sportsbook betting odds, ESPN's public API for historical game data and player statistics, and Google Gemini AI for game previews with player insights. The platform supports **NFL, NBA, NHL, and Soccer (Premier League)** markets, displaying them in a hierarchical structure with automatic categorization, centralized team name normalization, AI-generated game analysis with player highlights, multi-sportsbook odds comparison, and historical accuracy comparisons. The application provides a mobile-optimized experience, visual indicators for market assessment, and comprehensive market context to make informed trading decisions.

The business vision is to offer a user-friendly platform for exploring multi-sport prediction markets, enhancing accessibility and understanding for both casual fans and serious traders across major sports. By leveraging AI for insights, comparing predictions to actual results, supporting multiple sports leagues, and focusing on intuitive design, the project seeks to carve a niche in the sports prediction market analysis space.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

The application utilizes **Streamlit** for its UI, offering a Python-native, reactive web framework. It implements a multi-page pattern with a market listing page and a detail view. Key features include:

- **Market Listing Page**: Displays markets hierarchically with search, pagination, and mobile-first responsive design. Features color-coded visual odds quality indicators and enhanced market cards showing volume, open interest, time remaining, and sportsbook consensus odds.
- **Detail View**: Features AI-generated game preview with player insights, real-time multi-sportsbook odds comparison (Kalshi vs. DraftKings, FanDuel, BetMGM, etc.), historical accuracy comparison with ESPN game results, and initially collapsed sections for mobile optimization.
- **AI Game Preview**: Powered by Google Gemini 2.5 Flash, providing 3-4 sentence analyses highlighting key players, recent performance, and critical matchup factors.
- **Dark Mode Aesthetics**: Redesigned with a dark mode theme using dark slate backgrounds and an indigo primary color.

## Backend Architecture

The architecture follows a **service-oriented approach** to separate concerns, primarily using Python services:

- `sport_config.py`: Centralized configuration for all supported sports (NFL, NBA, NHL, Soccer), including team rosters, name variations, API sport keys, and stat categories for consistent normalization.
- `kalshi_service.py`: Manages interactions with the Kalshi API, supporting multi-sport queries and team name normalization.
- `odds_api_service.py`: Fetches real-time betting odds from The Odds API, supporting multi-sport data, American odds conversion, consensus calculation, and best odds discovery with caching.
- `espn_service.py`: Fetches historical game results and player statistics from ESPN's public API, providing multi-sport data for team leaders, player stats, and historical accuracy comparison.
- `gemini_service.py`: Generates AI-powered game previews using Google Gemini 2.5 Flash.
- `openai_service.py`: Handles generation of AI-powered market analyses using OpenAI's GPT-5.
- `app.py`: Orchestrates application logic and presentation, managing multi-sport support, manual per-sport service caching, and sport-specific data fetching.

### Market Normalization Layer

The `KalshiService` includes a pipeline for transforming raw Kalshi API data:
- **Category Mapping**: Maps markets into high-level categories.
- **Team Name Resolution**: Uses centralized `sport_config` to normalize team names across all sports.
- **Probability & Volume Calculation**: Implements fallback chains for probability and volume data.
- **Market Pairing & Combination**: Groups and combines opposing contracts for the same game into a single UI element.

### Multi-Sport Service Management

The application uses **manual per-sport service caching** (`_SERVICE_CACHE`) to ensure distinct, sport-specific service instances, circumventing Streamlit's cache_resource limitations for multi-sport environments. Events are tagged with `_sport` metadata for proper routing, and legacy links are handled with automatic sport detection.

## Pagination Implementation

The application uses **server-side cursor-based pagination** for fetching market data from the Kalshi API, ensuring fresh and consistent data for each page, and aggregates data from all sports for the "All" view.

## Data Visualization

**Plotly** is used for interactive charts and graphs, enabling rich visualizations of market data.

## AI Integration

The application integrates with:
- **Google Gemini AI (Gemini 2.5 Flash)** for generating engaging game previews with player insights.
- **OpenAI (GPT-5)** for generating concise market analysis briefs.

# External Dependencies

## Third-Party APIs

-   **Kalshi Trading API**:
    -   **Endpoint**: `https://api.elections.kalshi.com/trade-api/v2`
    -   **Authentication**: Unauthenticated public endpoints.
    -   **Purpose**: Fetches prediction markets, detailed market information, historical data, and order books for NFL, NBA, NHL, and Soccer.
-   **The Odds API**:
    -   **Endpoint**: `https://api.the-odds-api.com/v4/sports/{sport_key}/odds`
    -   **Authentication**: `ODDS_API_KEY` environment variable.
    -   **Purpose**: Fetches real-time betting odds from 70+ sportsbooks for NFL, NBA, NHL, and Soccer (Premier League). Provides consensus calculation, best odds discovery, and American odds conversion.
-   **ESPN Public API**:
    -   **Endpoint**: `http://site.api.espn.com/apis/site/v2/sports/{sport}/{league}`
    -   **Authentication**: No authentication required.
    -   **Purpose**: Fetches historical game results and player statistics (team leaders, rosters) for NFL, NBA, NHL, and Soccer (Premier League).
-   **OpenAI API**:
    -   **Model**: GPT-5.
    -   **Authentication**: `OPENAI_API_KEY` environment variable.
    -   **Purpose**: Generates natural language market analysis and insights.

## Python Libraries

-   **streamlit**: Web application framework.
-   **pandas**: Data manipulation.
-   **plotly**: Interactive data visualization.
-   **requests**: HTTP client.
-   **openai**: Official OpenAI Python client.

## Environment Configuration

-   `OPENAI_API_KEY`
-   `GEMINI_API_KEY`
-   `ODDS_API_KEY`