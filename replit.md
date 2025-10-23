# Overview

This is an NFL prediction markets explorer built with Streamlit that integrates with the Kalshi betting API and OpenAI for AI-powered market insights. The application allows users to browse, search, and analyze NFL betting markets with automated analysis powered by GPT-5.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses **Streamlit** as the web framework, providing a Python-based UI with built-in state management and reactive components. This was chosen for rapid development and seamless integration with Python data services. The interface follows a multi-page pattern with:
- A market listing page with search and pagination
- A detail view for individual markets with AI-generated insights
- Session state management for navigation and caching

**Pros**: Fast development, Python-native, built-in caching
**Cons**: Limited customization compared to React/Vue, server-side rendering only

## Backend Architecture
The application follows a **service-oriented architecture** with separation of concerns:
- `kalshi_service.py` handles all Kalshi API interactions
- `openai_service.py` manages AI analysis generation
- `app.py` serves as the presentation layer and orchestrator

This modular approach allows for easy testing, maintenance, and potential reuse of services. No traditional backend server is required since Streamlit handles the HTTP layer.

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
3. Markets grouped by event and displayed with pagination
4. User selects market → Detail page loads with additional API calls
5. OpenAI generates analysis for selected market
6. Results displayed with Plotly visualizations

**Note**: The application currently operates in read-only mode without user authentication. Future enhancements may include authenticated trading capabilities.

# Known Limitations
- Client-side search only filters current page results (not across all pages)
- Page sizes may vary slightly (95-100 markets) due to NFL filtering after fetching
- Some markets may lack historical price data (handled gracefully with info messages)
- OpenAI API quota limitations may prevent AI brief generation (displays error message)
