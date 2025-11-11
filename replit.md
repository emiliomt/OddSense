# Overview

OddSense is a multi-sport prediction markets explorer built with Streamlit, integrating with the Kalshi prediction market API, The Odds API for real-time sportsbook betting odds, ESPN's public API for historical game data and player statistics, and Google Gemini AI for game previews with player insights. The platform supports **NFL, NBA, NHL, and Soccer (Premier League)** markets, displaying them in a hierarchical structure with automatic categorization, centralized team name normalization, AI-generated game analysis with player highlights, multi-sportsbook odds comparison, and historical accuracy comparisons. The application provides a mobile-optimized experience, visual indicators for market assessment, and comprehensive market context to make informed trading decisions.

**Week 1-2 MVP Feature**: The platform now includes a **user prediction collection system** that enables anonymous users to make predictions on games, creating a proprietary data flywheel. Users can select winning teams with confidence levels (50-100%), view community consensus on predictions, and track their prediction history. All predictions are stored in a PostgreSQL database with anonymous session tracking.

The business vision is to offer a user-friendly platform for exploring multi-sport prediction markets, enhancing accessibility and understanding for both casual fans and serious traders across major sports. By leveraging AI for insights, comparing predictions to actual results, supporting multiple sports leagues, collecting user prediction data for proprietary insights, and focusing on intuitive design, the project seeks to carve a niche in the sports prediction market analysis space.

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
- `database.py`: PostgreSQL database connection configuration with SSL support for Neon/Replit managed database, including session pooling and SQLAlchemy ORM models.
- `prediction_service.py`: Manages user prediction operations including saving predictions, retrieving user predictions, calculating community consensus, and tracking session statistics.
- `app.py`: Orchestrates application logic and presentation, managing multi-sport support, manual per-sport service caching, sport-specific data fetching, and user prediction UI.

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

## Prediction Data Collection (Week 1-2 MVP)

The platform implements a **proprietary data flywheel** by collecting user predictions:

- **Database Schema**: PostgreSQL with three tables:
  - `user_sessions`: Anonymous user tracking via UUID session identifiers, with created_at, last_active, and total_predictions counts
  - `games`: Game records keyed by event_ticker, storing sport, teams, dates, and outcome fields for accuracy tracking
  - `predictions`: User predictions linking session_id + game_id with predicted_winner, confidence (50-100%), Kalshi probability, sportsbook consensus, and is_correct flag

- **Anonymous Session Tracking**: Users are identified by UUID stored in Streamlit session_state and persisted in the database. No login required for Week 1-2 MVP.

- **Prediction UI**: Integrated into game detail pages with Streamlit form containing:
  - Radio button team selection (home vs away)
  - Confidence slider (50-100% in 5% increments)
  - Form submit button that saves to database
  - Success feedback and automatic page reload to show saved prediction
  - Green indicator showing user's existing prediction
  - Community consensus display showing total predictions and percentage breakdown by team

- **PredictionService**: Provides methods for:
  - `get_or_create_session()`: Anonymous user session management
  - `save_prediction()`: Stores or updates user predictions with single-session transaction handling
  - `get_user_prediction()`: Retrieves user's existing prediction for a game
  - `get_community_consensus()`: Aggregates all predictions for a game to show community breakdown

- **SSL Database Configuration**: Neon/Replit PostgreSQL requires `?sslmode=require` appended to DATABASE_URL with connection pooling (pool_pre_ping=True, pool_recycle=300) for stable connections.

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
-   **sqlalchemy**: ORM for PostgreSQL database interactions.
-   **psycopg2-binary**: PostgreSQL database driver.

## Environment Configuration

-   `OPENAI_API_KEY`
-   `GEMINI_API_KEY`
-   `ODDS_API_KEY`
-   `DATABASE_URL`: PostgreSQL connection string (managed by Replit)