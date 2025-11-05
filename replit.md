# Overview

This project is an NFL prediction markets explorer built with Streamlit, integrating with the Kalshi betting API and OpenAI for AI-powered market insights. It displays markets in a hierarchical structure, featuring automatic categorization, team name normalization, and AI-generated analysis. The application aims to provide users with a mobile-optimized experience, visual indicators for market assessment, and comprehensive market context to make informed trading decisions.

The business vision is to offer a user-friendly platform for exploring NFL prediction markets, enhancing accessibility and understanding for both casual fans and serious traders. By leveraging AI for insights and focusing on intuitive design, the project seeks to carve a niche in the sports prediction market analysis space.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

The application utilizes **Streamlit** for its UI, offering a Python-native, reactive web framework. It implements a multi-page pattern with a market listing page and a detail view.

- **Market Listing Page**: Displays markets hierarchically (Category → Matchup → Combined Markets) with a single row showing both teams and their probabilities. Features search, pagination, and mobile-first responsive design with custom CSS.
- **Visual Odds Quality Indicators**: Color-coded system (Green, Blue, Orange) provides quick assessment of market signals on market cards.
- **Redesigned Market Cards**: Clean white cards with a colored left border, large probability badge, and value indicator label (e.g., "Strong Favorite").
- **Detail View**: Allows selection of a specific team's contract via radio buttons. Includes visual indicators, shortened metric labels (e.g., "24h Volume"), and initially collapsed sections for Order Book and All Event Contracts to optimize mobile viewing.
- **Session State Management**: Used for navigation between combined and single markets.

## Backend Architecture

The architecture follows a **service-oriented approach** to separate concerns:

- `kalshi_service.py`: Manages all interactions with the Kalshi API, including data normalization.
- `openai_service.py`: Handles the generation of AI-powered market analyses.
- `app.py`: Orchestrates the application logic and serves the presentation layer.

### Market Normalization Layer

The `KalshiService` includes a pipeline for transforming raw Kalshi API data into a display-ready format:

- **Category Mapping**: Parses event tickers to map markets into high-level categories (e.g., "Games", "Passing Yards").
- **Team Name Resolution**: Uses a comprehensive NFL team code dictionary to expand abbreviations and normalize team names.
- **Display Name Generation**: Prioritizes API titles/subtitles, with fallbacks and team abbreviation expansion for clarity.
- **Probability & Volume Calculation**: Implements a fallback chain for probability (yes_bid → last_price → mid_price) and volume (volume → volume_24h → liquidity).
- **Market Pairing & Combination**: Groups and combines opposing contracts for the same game into a single UI element, calculating probabilities and combining relevant data for both teams.

## Pagination Implementation

The application uses **server-side cursor-based pagination** for fetching market data from the Kalshi API. This ensures fresh data for each page and consistent page sizes by specifically requesting `series_ticker=KXNFLGAME`.

## Data Visualization

**Plotly** is used for interactive charts and graphs, enabling rich visualizations of market data such as price movements and volume over time.

## AI Integration

The application integrates with **OpenAI's GPT-5** for generating concise 3-4 sentence market analysis briefs. The `OpenAIService` constructs detailed prompts, formats probability implications, and manages API interactions. GPT-5 is configured with `max_completion_tokens=5000` to accommodate its reasoning process and `reasoning_effort="low"` for simple analysis tasks.

# External Dependencies

## Third-Party APIs

### Kalshi Trading API

- **Endpoint**: `https://api.elections.kalshi.com/trade-api/v2`
- **Authentication**: Uses unauthenticated public endpoints.
- **Purpose**: Fetches Professional Football Game prediction markets (`series_ticker=KXNFLGAME`), detailed market information, historical price data, and order books.
- **Filtering**: Specifically uses `series_ticker=KXNFLGAME` to retrieve only game outcome contracts.

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