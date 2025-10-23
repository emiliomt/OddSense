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
  - Filtering for NFL-specific markets by ticker

### OpenAI API
- **Model**: GPT-5 (current as of August 2025)
- **Authentication**: API key via `OPENAI_API_KEY` environment variable
- **Purpose**: Generates natural language market analysis and insights
- **Integration**: Python OpenAI client library

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
1. User searches/browses markets → Kalshi API call
2. Market data cached in Streamlit session state
3. User selects market → OpenAI generates analysis
4. Results displayed with Plotly visualizations

**Note**: The application currently operates in read-only mode without user authentication. Future enhancements may include authenticated trading capabilities.