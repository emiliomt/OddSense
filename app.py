# app.py
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from espn_lookup import find_game_id
from kalshi_service import KalshiService

st.set_page_config(page_title="NFL Kalshi Markets",
                   page_icon="🏈",
                   layout="wide",
                   initial_sidebar_state="collapsed")

CONTEXT_URL = os.getenv("CONTEXT_URL", "http://localhost:8000")

# Mobile-optimized CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        h2 {
            font-size: 1.2rem !important;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
    }
    
    /* Odds quality indicators */
    .odds-excellent {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
    }
    
    .odds-good {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
    }
    
    .odds-neutral {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);
    }
    
    .odds-poor {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3);
    }
    
    /* Clean market cards */
    .market-card {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .market-card-excellent {
        border-left-color: #10b981;
    }
    
    .market-card-good {
        border-left-color: #3b82f6;
    }
    
    .market-card-neutral {
        border-left-color: #f59e0b;
    }
    
    .market-card-poor {
        border-left-color: #ef4444;
    }
    
    /* Probability badge */
    .prob-badge {
        display: inline-block;
        font-size: 1.5rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Value indicator */
    .value-indicator {
        font-size: 0.875rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        display: inline-block;
        margin-top: 0.25rem;
    }
    
    .value-strong {
        background: #d1fae5;
        color: #065f46;
    }
    
    .value-moderate {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .value-weak {
        background: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_kalshi() -> KalshiService:
    return KalshiService()


def qp_get(name: str, default: str = "list") -> str:
    try:
        return st.query_params.get(name, default)
    except Exception:
        return st.experimental_get_query_params().get(name, [default])[0]


def qp_set(**kwargs):
    try:
        st.query_params.update(kwargs)
    except Exception:
        st.experimental_set_query_params(**kwargs)


def init_state():
    st.session_state.setdefault("search", "")
    st.session_state.setdefault("events_per_page", 12)
    st.session_state.setdefault("p", 1)


def pct(x: Optional[float]) -> str:
    return f"{x*100:.0f}%" if isinstance(x, (int, float)) else "—"


def get_odds_quality(prob: Optional[float]) -> tuple[str, str, str]:
    """
    Determine odds quality and return (category, css_class, description).
    
    Logic:
    - Strong favorite (>75%): Excellent - clear market confidence
    - Slight favorite (60-75%): Good - moderate confidence
    - Toss-up (40-60%): Neutral - market is uncertain
    - Slight underdog (25-40%): Good - upset potential with value
    - Long shot (<25%): Excellent - high risk but potential high reward
    """
    if prob is None:
        return ("Unknown", "odds-neutral", "No data")
    
    pct_val = prob * 100
    
    if pct_val >= 75:
        return ("Strong Favorite", "odds-excellent", f"Heavy favorite at {pct_val:.0f}%")
    elif pct_val >= 60:
        return ("Favorite", "odds-good", f"Favored to win at {pct_val:.0f}%")
    elif pct_val >= 40:
        return ("Toss-Up", "odds-neutral", f"Close race at {pct_val:.0f}%")
    elif pct_val >= 25:
        return ("Underdog", "odds-good", f"Underdog with value at {pct_val:.0f}%")
    else:
        return ("Long Shot", "odds-excellent", f"Upset potential at {pct_val:.0f}%")


def call_context(game_id: str, include_llm: bool = True) -> Optional[dict]:
    try:
        r = requests.get(
            f"{CONTEXT_URL}/context",
            params={
                "game_id": game_id,
                "include_llm": str(include_llm).lower()
            },
            timeout=45,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"Context service not reachable at {CONTEXT_URL}. "
            f"Start your FastAPI server (uvicorn context_service:app --port 8000) or set CONTEXT_URL."
        )
        return None
    except Exception as e:
        st.error(f"Context service error: {e}")
        return None


def pick_display_label_and_bid(w: dict) -> tuple[str, Optional[float]]:
    """
    Only show one bid (%) per game:
      - Prefer YES bid if available → "<TEAM> — Yes"
      - Else prefer NO bid if available → "<TEAM> — No"
      - Else show '—'
    """
    team = w.get("subject_team") or "Team"
    yes_bid = w.get("yes_bid")
    no_bid = w.get("no_bid")
    if yes_bid is not None:
        return f"{team} — Yes", yes_bid
    if no_bid is not None:
        return f"{team} — No", no_bid
    return f"{team} — Yes", None


def page_list():
    st.title("🏈 NFL Kalshi Markets")

    with st.sidebar:
        st.subheader("Filters")
        st.session_state.search = st.text_input("Search teams/market text",
                                                st.session_state.search)
        st.session_state.events_per_page = st.number_input(
            "Events per page",
            min_value=6,
            max_value=50,
            step=2,
            value=st.session_state.events_per_page)

    kalshi = get_kalshi()
    events = kalshi.fetch_and_group_open_games()

    # Search
    q = (st.session_state.search or "").lower().strip()
    if q:

        def match(ev):
            if q in (ev["pretty_event"] or "").lower():
                return True
            if q in ev["home_team"].lower() or q in ev["away_team"].lower():
                return True
            for m in ev["all_contracts"]:
                t = " ".join([m.get("title") or "",
                              m.get("subtitle") or ""]).lower()
                if q in t:
                    return True
            return False

        events = [e for e in events if match(e)]

    # Pagination
    total = len(events)
    per = int(st.session_state.events_per_page)
    pages = max(1, (total + per - 1) // per)
    p = max(1, min(int(st.session_state.p), pages))
    start, end = (p - 1) * per, min(p * per, total)

    st.caption(f"📊 {total} games • Page {p}/{pages}")

    # Mobile-optimized market cards
    for ev in events[start:end]:
        w = ev.get("winner_primary", {}) or {}
        label, bid_val = pick_display_label_and_bid(w)
        
        # Get odds quality
        quality_label, quality_class, quality_desc = get_odds_quality(bid_val)
        
        # Determine card border color
        card_class = quality_class.replace("odds-", "market-card-")
        
        # Create custom HTML card for better mobile UX
        matchup = ev.get("pretty_event") or f"{ev['away_team']} @ {ev['home_team']}"
        prob_pct = f"{bid_val*100:.0f}%" if bid_val else "—"
        
        st.markdown(f"""
        <div class="market-card {card_class}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                <div style="flex: 1;">
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">
                        {matchup}
                    </div>
                    <div style="font-size: 0.85rem; color: #6b7280;">
                        {label}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div class="prob-badge {quality_class}">
                        {prob_pct}
                    </div>
                    <div class="value-indicator value-{'strong' if 'excellent' in quality_class or (bid_val and (bid_val >= 0.75 or bid_val <= 0.25)) else 'moderate' if 'good' in quality_class else 'weak'}">
                        {quality_label}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action button
        st.link_button("📊 View Details", f"?page=detail&event={ev['event_ticker']}", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # Pager
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if p > 1:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.p = p - 1
                qp_set(page="list")
                st.rerun()
    with col2:
        st.markdown(f"<div style='text-align: center; padding: 0.5rem;'>Page {p} of {pages}</div>", unsafe_allow_html=True)
    with col3:
        if p < pages:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.p = p + 1
                qp_set(page="list")
                st.rerun()


def page_detail():
    kalshi = get_kalshi()
    event_ticker = qp_get("event", "")
    if not event_ticker:
        st.warning("No event selected.")
        return

    events = kalshi.fetch_and_group_open_games()
    ev = next((e for e in events if e["event_ticker"] == event_ticker), None)
    if not ev:
        st.error("Event not found (may have closed).")
        return

    st.title(
        ev.get("pretty_event") or f"{ev['away_team']} at {ev['home_team']}")
    
    # Enhanced event context
    close_dt = ev.get('close_dt')
    if close_dt:
        now = datetime.now(timezone.utc)
        time_diff = close_dt - now
        hours_left = time_diff.total_seconds() / 3600
        
        if hours_left > 24:
            days_left = int(hours_left / 24)
            time_desc = f"Market closes in **{days_left} days** ({close_dt.strftime('%B %d, %Y at %I:%M %p UTC')})"
        elif hours_left > 0:
            time_desc = f"Market closes in **{int(hours_left)} hours** ({close_dt.strftime('%B %d at %I:%M %p UTC')})"
        else:
            time_desc = f"Market closed {close_dt.strftime('%B %d, %Y at %I:%M %p UTC')}"
    else:
        time_desc = "Close time not available"
    
    st.caption(time_desc)

    # Market Metrics Overview with explanations
    st.subheader("📊 Market Overview")
    
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        st.metric(
            "24h Trading Volume",
            f"${ev.get('volume_24h_sum', 0):,}",
            help="Total dollar volume traded in the last 24 hours across all contracts for this game. Higher volume indicates more active trading and better liquidity."
        )
    
    with metric_cols[1]:
        st.metric(
            "Open Interest",
            f"{ev.get('open_interest_sum', 0):,} contracts",
            help="Total number of outstanding contracts (positions that haven't been closed). This represents the total amount of money at risk in this market."
        )
    
    with metric_cols[2]:
        if close_dt:
            hours_left = (close_dt - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_left > 0:
                st.metric(
                    "Time Remaining",
                    f"{int(hours_left)} hours" if hours_left < 48 else f"{int(hours_left/24)} days",
                    help="Time until this market closes and stops accepting trades. Markets typically close shortly before the event begins."
                )
            else:
                st.metric("Status", "Closed", help="This market has closed and is no longer accepting trades.")
    
    st.divider()
    
    # ONE display row
    w = ev.get("winner_primary", {}) or {}
    label, bid_val = pick_display_label_and_bid(w)

    st.subheader("🏆 Winner Market")
    st.info(
        "**How to read this market:** "
        "The bid price shows what traders are currently willing to pay for a 'Yes' contract. "
        "A bid of 60% means the market implies a 60% chance of that outcome. "
        "You can buy 'Yes' if you think the probability is higher, or 'No' if you think it's lower."
    )
    
    grid = st.columns([5, 2, 3])
    grid[0].markdown("**Market**")
    grid[1].markdown("**Implied Probability**")
    grid[2].markdown("**Ticker**")

    r = st.columns([5, 2, 3])
    r[0].write(label)
    r[1].write(pct(bid_val))
    r[2].code(w.get("ticker") or "")

    # Historical Price Chart
    st.divider()
    st.subheader("📈 Historical Price Movement")
    
    ticker = w.get("ticker")
    if ticker:
        st.info(
            "**Understanding price history:** "
            "This chart shows how the market's implied probability has changed over time. "
            "Rising prices indicate growing confidence in the outcome, while falling prices suggest decreasing confidence. "
            "Watch for trends and sudden movements that might indicate new information entering the market."
        )
        
        import plotly.graph_objects as go
        
        # Fetch candlestick data
        candlesticks = kalshi.get_market_candlesticks(
            series_ticker=kalshi.SERIES_TICKER_GAME,
            ticker=ticker,
            period_interval=60  # 1-hour candles
        )
        
        if candlesticks and len(candlesticks) > 0:
            # Filter out candlesticks with None close prices
            valid_candles = [c for c in candlesticks if c.get("close") is not None]
            
            if valid_candles:
                timestamps = [c["timestamp"] for c in valid_candles]
                closes = [c["close"] for c in valid_candles]
                volumes = [c.get("volume", 0) for c in valid_candles]
            else:
                # No valid data
                timestamps, closes, volumes = [], [], []
            
            # Calculate trend
            if len(closes) >= 2 and closes[0] is not None and closes[-1] is not None:
                price_change = closes[-1] - closes[0]
                pct_change = (price_change / closes[0] * 100) if closes[0] > 0 else 0
                
                if abs(pct_change) > 5:
                    trend_emoji = "📈" if pct_change > 0 else "📉"
                    trend_text = f"{trend_emoji} **Market trend:** {'Rising' if pct_change > 0 else 'Falling'} ({pct_change:+.1f}% over the period shown)"
                else:
                    trend_text = "➡️ **Market trend:** Stable (minimal movement)"
                
                st.caption(trend_text)
            
            # Create price chart only if we have valid data
            if len(closes) > 0:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=closes,
                    mode='lines',
                    name='Close Price',
                    line=dict(color='#1f77b4', width=2),
                    hovertemplate='<b>Time:</b> %{x}<br><b>Price:</b> $%{y:.2f}<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Price Over Time (Hourly)",
                    xaxis_title="Time",
                    yaxis_title="Price (Probability)",
                    yaxis=dict(tickformat='.0%', range=[0, 1]),
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Volume chart
                if len(volumes) > 0 and max(volumes) > 0:
                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Bar(
                        x=timestamps,
                        y=volumes,
                        name='Volume',
                        marker_color='lightblue',
                        hovertemplate='<b>Time:</b> %{x}<br><b>Volume:</b> %{y}<extra></extra>'
                    ))
                    
                    fig_vol.update_layout(
                        title="Trading Volume Over Time",
                        xaxis_title="Time",
                        yaxis_title="Volume",
                        height=300
                    )
                    
                    with st.expander("📊 View Volume History"):
                        st.caption("**Volume spikes** can indicate important news or events affecting trader sentiment.")
                        st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info("Historical price data contains no valid close prices. This can happen for newly created markets.")
        else:
            st.info("Historical price data not yet available for this market. Check back after some trading activity.")
    
    # Order Book
    st.divider()
    st.subheader("📖 Current Order Book")
    
    if ticker:
        st.info(
            "**Understanding the order book:** "
            "The order book shows all pending buy and sell orders. "
            "'Yes' orders are from traders betting the outcome will happen. "
            "'No' orders are from traders betting it won't. "
            "The spread between best bid and ask indicates market liquidity."
        )
        
        orderbook = kalshi.get_market_orderbook(ticker)
        
        if orderbook:
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                st.markdown("**YES Orders (Betting it happens)**")
                yes_orders = orderbook.get("yes", [])
                if yes_orders:
                    yes_df = pd.DataFrame(yes_orders[:10])  # Top 10
                    if not yes_df.empty and "price" in yes_df.columns and "size" in yes_df.columns:
                        yes_display = yes_df[["price", "size"]].copy()
                        yes_display.columns = ["Price", "Size"]
                        st.dataframe(
                            yes_display,
                            hide_index=True,
                            use_container_width=True
                        )
                else:
                    st.caption("No YES orders currently available")
            
            with col_no:
                st.markdown("**NO Orders (Betting it doesn't happen)**")
                no_orders = orderbook.get("no", [])
                if no_orders:
                    no_df = pd.DataFrame(no_orders[:10])  # Top 10
                    if not no_df.empty and "price" in no_df.columns and "size" in no_df.columns:
                        no_display = no_df[["price", "size"]].copy()
                        no_display.columns = ["Price", "Size"]
                        st.dataframe(
                            no_display,
                            hide_index=True,
                            use_container_width=True
                        )
                else:
                    st.caption("No NO orders currently available")
        else:
            st.info("Order book data not available for this market.")
    
    st.divider()
    st.subheader("📋 All Event Contracts (Detailed)")
    st.caption("Complete list of all betting contracts available for this game, including player props and other markets.")
    
    df = pd.DataFrame(ev["all_contracts"])
    keep = [
        c for c in [
            "ticker", "title", "subtitle", "yes_bid", "yes_ask",
            "open_interest", "volume_24h", "close_dt", "market_type"
        ] if c in df.columns
    ]
    if "close_dt" in df.columns:
        df_sorted = df.sort_values(by="close_dt",
                                   ascending=True,
                                   na_position="last",
                                   ignore_index=True)
    else:
        df_sorted = df.copy()
    st.dataframe(df_sorted[keep], use_container_width=True)

    # ---------- Context generation ----------
    st.divider()
    st.subheader("Generate Game Context (ESPN + GPT via FastAPI)")
    auto_game_id = find_game_id(ev["away_team"], ev["home_team"],
                                ev["close_dt"])
    with st.expander("Game mapping details"):
        st.write({
            "away_team": ev["away_team"],
            "home_team": ev["home_team"],
            "kalshi_close_dt": str(ev["close_dt"]),
            "auto_resolved_game_id": auto_game_id,
            "context_url": CONTEXT_URL,
        })

    game_id = st.text_input("ESPN game_id", value=auto_game_id or "")
    colL, colR = st.columns([1, 5])
    with colL:
        run = st.button("Generate Context")

    if run and game_id:
        data = call_context(game_id, include_llm=True)
        if data:
            if data.get("llm", {}).get("summary_md"):
                st.markdown("### Analyst Brief")
                st.markdown(data["llm"]["summary_md"])
            else:
                st.info("LLM summary not available; showing facts only.")
            st.markdown("### Facts (compact)")
            st.json(data.get("facts", {}))

    st.link_button("⬅️ Back to list", "?page=list")


def main():
    init_state()
    page = qp_get("page", "list")
    if page == "detail":
        page_detail()
    else:
        page_list()


if __name__ == "__main__":
    main()
