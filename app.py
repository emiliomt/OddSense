import streamlit as st
import pandas as pd
from kalshi_service import KalshiService
from openai_service import OpenAIService
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="NFL Kalshi Markets",
    page_icon="🏈",
    layout="wide"
)

@st.cache_resource
def get_kalshi_service():
    return KalshiService()

@st.cache_resource
def get_openai_service():
    return OpenAIService()

def init_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state.page = 'list'
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'page_cursors' not in st.session_state:
        st.session_state.page_cursors = [None]
    if 'current_markets' not in st.session_state:
        st.session_state.current_markets = []
    if 'has_more' not in st.session_state:
        st.session_state.has_more = False

def show_market_list():
    """Display the main market listing page."""
    st.title("🏈 NFL Prediction Markets")
    st.markdown("Explore NFL betting markets on Kalshi with AI-powered insights")
    
    kalshi = get_kalshi_service()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input(
            "🔍 Search markets",
            value=st.session_state.search_query,
            placeholder="Search by team, game, or market type..."
        )
        if search != st.session_state.search_query:
            st.session_state.search_query = search
            st.session_state.current_page = 0
            st.session_state.page_cursors = [None]
            st.session_state.current_markets = []
    
    with col2:
        markets_per_page = st.selectbox("Markets per page", [25, 50, 100], index=0)
    
    current_cursor = st.session_state.page_cursors[st.session_state.current_page]
    
    with st.spinner("Loading NFL markets..."):
        data = kalshi.get_nfl_markets(limit=markets_per_page, cursor=current_cursor)
        markets = data.get("markets", [])
        next_cursor = data.get("cursor")
        
        if st.session_state.search_query:
            search_lower = st.session_state.search_query.lower()
            markets = [
                m for m in markets
                if search_lower in m.get("title", "").lower()
                or search_lower in m.get("subtitle", "").lower()
                or search_lower in m.get("event_ticker", "").lower()
            ]
        
        st.session_state.current_markets = markets
        st.session_state.has_more = bool(next_cursor)
        
        if next_cursor and len(st.session_state.page_cursors) == st.session_state.current_page + 1:
            st.session_state.page_cursors.append(next_cursor)
        
        if not markets:
            st.info("No NFL markets found on this page.")
            if not st.session_state.has_more and st.session_state.current_page == 0:
                st.warning("No NFL markets available. Please try again later.")
        
        grouped_markets = kalshi.group_markets_by_event(markets)
        
        if markets:
            st.markdown(f"### Showing {len(markets)} markets across {len(grouped_markets)} events (Page {st.session_state.current_page + 1})")
        
        current_event = None
        for market in markets:
            event_ticker = market.get("event_ticker", "Unknown")
            
            if current_event != event_ticker:
                current_event = event_ticker
                st.markdown(f"## 🏟️ {event_ticker}")
                st.markdown("---")
            
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            
            with col1:
                title = market.get("title", "Unknown Market")
                subtitle = market.get("subtitle", "")
                st.markdown(f"**{title}**")
                if subtitle:
                    st.caption(subtitle)
            
            with col2:
                yes_bid = market.get("yes_bid", 0)
                st.metric("Probability", f"{yes_bid}%")
            
            with col3:
                volume = market.get("volume", 0)
                st.metric("Volume", f"${volume:,.0f}")
            
            with col4:
                if st.button("📊 Details", key=f"btn_{market['ticker']}"):
                    st.session_state.selected_ticker = market['ticker']
                    st.session_state.page = 'detail'
                    st.rerun()
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.session_state.current_page > 0:
                if st.button("⬅️ Previous"):
                    st.session_state.current_page -= 1
                    st.rerun()
        
        with col2:
            page_info = f"Page {st.session_state.current_page + 1}"
            if st.session_state.has_more:
                page_info += " (more available)"
            st.markdown(f"<div style='text-align: center'>{page_info}</div>", unsafe_allow_html=True)
        
        with col3:
            if st.session_state.has_more:
                if st.button("Next ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()

def show_market_detail():
    """Display detailed market information."""
    kalshi = get_kalshi_service()
    openai_service = get_openai_service()
    
    ticker = st.session_state.selected_ticker
    
    if st.button("⬅️ Back to Markets"):
        st.session_state.page = 'list'
        st.rerun()
    
    st.title(f"📊 Market Details: {ticker}")
    
    market = None
    with st.spinner("Loading market details..."):
        market = kalshi.get_market_details(ticker)
    
    if not market:
        st.error("Unable to load market details. Please try again.")
        return
    
    st.header(market.get("title", "Unknown Market"))
    if market.get("subtitle"):
        st.subheader(market.get("subtitle"))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        yes_bid = market.get("yes_bid", 0)
        st.metric("Yes Probability", f"{yes_bid}%", help="Current yes bid price")
    
    with col2:
        no_bid = market.get("no_bid", 0)
        st.metric("No Probability", f"{no_bid}%", help="Current no bid price")
    
    with col3:
        volume = market.get("volume", 0)
        st.metric("Volume", f"${volume:,.0f}", help="Total trading volume")
    
    with col4:
        open_interest = market.get("open_interest", 0)
        st.metric("Open Interest", f"{open_interest:,}", help="Outstanding contracts")
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Price History", "📖 Order Book", "🤖 AI Market Brief", "ℹ️ Market Info"])
    
    with tab1:
        st.subheader("Price History")
        history = kalshi.get_market_history(ticker, limit=100)
        
        if history:
            df = pd.DataFrame(history)
            
            if 'ts' in df.columns and 'price' in df.columns:
                df['timestamp'] = pd.to_datetime(df['ts'], unit='s')
                df = df.sort_values('timestamp')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['price'],
                    mode='lines+markers',
                    name='Price',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=4)
                ))
                
                fig.update_layout(
                    title="Market Price Over Time",
                    xaxis_title="Time",
                    yaxis_title="Price (¢)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Historical price data structure not available")
        else:
            st.info("No historical data available for this market")
    
    with tab2:
        st.subheader("Order Book")
        orderbook = kalshi.get_orderbook(ticker, depth=10)
        
        if orderbook:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👍 Yes Orders")
                yes_orders = orderbook.get("yes", [])
                if yes_orders:
                    yes_df = pd.DataFrame(yes_orders)
                    st.dataframe(yes_df, use_container_width=True)
                else:
                    st.info("No yes orders")
            
            with col2:
                st.markdown("### 👎 No Orders")
                no_orders = orderbook.get("no", [])
                if no_orders:
                    no_df = pd.DataFrame(no_orders)
                    st.dataframe(no_df, use_container_width=True)
                else:
                    st.info("No no orders")
        else:
            st.info("Order book data not available")
    
    with tab3:
        st.subheader("🤖 AI-Generated Market Brief")
        
        with st.spinner("Generating AI insights..."):
            brief = openai_service.generate_market_brief(market)
            st.markdown(brief)
        
        st.caption("Generated by AI - Use for informational purposes only")
    
    with tab4:
        st.subheader("Market Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**Ticker:** {market.get('ticker', 'N/A')}")
            st.markdown(f"**Event:** {market.get('event_ticker', 'N/A')}")
            st.markdown(f"**Status:** {market.get('status', 'N/A')}")
            st.markdown(f"**Market Type:** {market.get('market_type', 'N/A')}")
        
        with info_col2:
            close_time = market.get('close_time', 'N/A')
            st.markdown(f"**Closes:** {close_time}")
            st.markdown(f"**Result:** {market.get('result', 'Pending')}")
            st.markdown(f"**Can Close Early:** {market.get('can_close_early', False)}")
            st.markdown(f"**Expiration Time:** {market.get('expiration_time', 'N/A')}")

def main():
    """Main application entry point."""
    init_session_state()
    
    if st.session_state.page == 'list':
        show_market_list()
    elif st.session_state.page == 'detail':
        show_market_detail()

if __name__ == "__main__":
    main()
