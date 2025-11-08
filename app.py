# app.py
import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests
import streamlit as st

from espn_lookup import find_game_id
from kalshi_service import KalshiService
from espn_service import espn
from odds_api_service import OddsAPIService
from gemini_service import GeminiService

st.set_page_config(page_title="OddSense",
                   page_icon="📊",
                   layout="wide",
                   initial_sidebar_state="collapsed")

CONTEXT_URL = os.getenv("CONTEXT_URL", "http://localhost:8000")

# Figma-like Dark Mode CSS
st.markdown("""
<style>
    /* Global dark theme */
    .stApp {
        background-color: #0f172a;
    }

    /* Top Navigation Menu */
    .top-nav {
        background: #1e293b;
        border-bottom: 1px solid #334155;
        padding: 0.75rem 1rem;
        margin-bottom: 1.5rem;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .nav-brand {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .nav-links {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .nav-link {
        background: transparent;
        border: 1px solid #334155;
        color: #94a3b8;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .nav-link:hover {
        background: #334155;
        color: #f1f5f9;
        border-color: #475569;
    }

    .nav-link.active {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }

    @media (max-width: 768px) {
        .top-nav {
            flex-direction: column;
            align-items: flex-start;
        }

        .nav-links {
            width: 100%;
        }

        .nav-link {
            flex: 1;
            text-align: center;
        }
    }

    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem;
        }
        h1 {
            font-size: 1.75rem !important;
        }
        h2 {
            font-size: 1.25rem !important;
        }
    }

    /* Typography improvements */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #f1f5f9 !important;
    }

    /* Odds quality indicators - dark mode */
    .odds-excellent {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    }

    .odds-good {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }

    .odds-neutral {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }

    .odds-poor {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
    }

    /* Figma-like dark market cards */
    .market-card {
        background: #1e293b;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
    }

    .market-card:hover {
        border-color: #475569;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }

    .market-card-excellent {
        border-left: 3px solid #10b981;
    }

    .market-card-good {
        border-left: 3px solid #6366f1;
    }

    .market-card-neutral {
        border-left: 3px solid #f59e0b;
    }

    .market-card-poor {
        border-left: 3px solid #ef4444;
    }

    /* Probability badge - dark mode */
    .prob-badge {
        display: inline-block;
        font-size: 1.75rem;
        font-weight: 800;
        padding: 0.375rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        letter-spacing: -0.02em;
    }

    /* Value indicator - dark mode */
    .value-indicator {
        font-size: 0.875rem;
        font-weight: 600;
        padding: 0.375rem 0.75rem;
        border-radius: 8px;
        display: inline-block;
        margin-top: 0.375rem;
        letter-spacing: 0.01em;
    }

    .value-strong {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .value-moderate {
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    .value-weak {
        background: rgba(239, 68, 68, 0.15);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Market metrics row - dark mode */
    .market-metrics {
        font-size: 0.8rem !important;
        color: #94a3b8 !important;
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        margin-top: 0.75rem;
        font-weight: 500;
    }

    .market-metrics span {
        font-size: 0.8rem !important;
        color: #94a3b8 !important;
        background: rgba(51, 65, 85, 0.5);
        padding: 0.25rem 0.625rem;
        border-radius: 6px;
    }

    /* Buttons - dark mode */
    .stButton > button {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: #334155 !important;
        border-color: #475569 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    /* Link buttons - dark mode */
    a[data-testid="stLinkButton"] {
        text-decoration: none !important;
    }

    /* Sidebar - dark mode */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }

    /* Inputs - dark mode */
    .stTextInput input {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 1px #6366f1 !important;
    }

    /* Number input - dark mode */
    .stNumberInput input {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
    }

    /* Plotly chart containers - dark mode */
    .js-plotly-plot,
    .plotly {
        background-color: #1e293b !important;
        border-radius: 8px;
    }

    .stPlotlyChart {
        background-color: #1e293b !important;
        border-radius: 8px;
    }
</style>
""",
            unsafe_allow_html=True)


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


def render_top_nav(current_page: str = "list"):
    """Render top navigation menu"""
    # Create navigation bar with columns
    nav_container = st.container()
    with nav_container:
        col1, col2 = st.columns([1, 4])

        with col1:
            st.markdown('<div style="font-size: 1.5rem; font-weight: 700; color: #f1f5f9; padding: 0.75rem 0;">📊 OddSense</div>', unsafe_allow_html=True)

        with col2:
            if current_page != "list":
                if st.button("🏠 All Markets", key="nav_home_button", use_container_width=False):
                    qp_set(page="list")
                    st.rerun()
            else:
                st.markdown('<div style="background: #6366f1; color: white; border: 1px solid #6366f1; padding: 0.5rem 1rem; border-radius: 6px; display: inline-block; margin-top: 0.5rem;">🏠 All Markets</div>', unsafe_allow_html=True)

        st.markdown('<hr style="margin: 1rem 0; border-color: #334155;">', unsafe_allow_html=True)


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
        return ("Strong Favorite", "odds-excellent",
                f"Heavy favorite at {pct_val:.0f}%")
    elif pct_val >= 60:
        return ("Favorite", "odds-good", f"Favored to win at {pct_val:.0f}%")
    elif pct_val >= 40:
        return ("Toss-Up", "odds-neutral", f"Close race at {pct_val:.0f}%")
    elif pct_val >= 25:
        return ("Underdog", "odds-good",
                f"Underdog with value at {pct_val:.0f}%")
    else:
        return ("Long Shot", "odds-excellent",
                f"Upset potential at {pct_val:.0f}%")


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
    render_top_nav("list")

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

    # Initialize SportsGameOdds API service for sportsbook data
    odds_api = OddsAPIService()

    # Mobile-optimized market cards
    for ev in events[start:end]:
        w = ev.get("winner_primary", {}) or {}
        label, bid_val = pick_display_label_and_bid(w)

        # Get odds quality
        quality_label, quality_class, quality_desc = get_odds_quality(bid_val)

        # Determine card border color
        card_class = quality_class.replace("odds-", "market-card-")

        # Create custom HTML card for better mobile UX
        matchup = ev.get(
            "pretty_event") or f"{ev['away_team']} @ {ev['home_team']}"
        prob_pct = f"{bid_val*100:.0f}%" if bid_val else "—"

        # Calculate time left
        close_dt = ev.get('close_dt')
        time_left_str = ""
        if close_dt:
            now = datetime.now(timezone.utc)
            time_diff = close_dt - now
            hours_left = time_diff.total_seconds() / 3600

            if hours_left > 48:
                days_left = int(hours_left / 24)
                time_left_str = f"{days_left}d"
            elif hours_left > 0:
                time_left_str = f"{int(hours_left)}h"
            else:
                time_left_str = "Closed"

        # Format volume and open interest
        volume_24h = ev.get('volume_24h_sum', 0)
        volume_str = f"${volume_24h:,.0f}" if volume_24h >= 1000 else f"${volume_24h:.0f}"

        open_interest = ev.get('open_interest_sum', 0)
        oi_str = f"{open_interest:,.0f}" if open_interest >= 1000 else f"{open_interest:.0f}"

        # Fetch sportsbook odds for comparison
        sportsbook_str = ""
        away_team_name = ev.get("away_team", "")
        home_team_name = ev.get("home_team", "")

        if away_team_name and home_team_name:
            try:
                game_odds = odds_api.find_game_by_teams(
                    away_team_name, home_team_name)
                if game_odds:
                    consensus = odds_api.get_market_consensus(game_odds)
                    if consensus:
                        # Determine which team the primary contract is for
                        subject_team = w.get('subject_team', '')

                        # Get sportsbook average for the same team
                        if subject_team == away_team_name and away_team_name in consensus:
                            avg_prob = consensus[away_team_name]
                            sportsbook_str = f"{avg_prob:.0f}%"
                        elif subject_team == home_team_name and home_team_name in consensus:
                            avg_prob = consensus[home_team_name]
                            sportsbook_str = f"{avg_prob:.0f}%"
            except Exception:
                # Silently fail - odds might not be available yet
                pass

        # Determine value class
        if 'excellent' in quality_class or (bid_val and (bid_val >= 0.75
                                                         or bid_val <= 0.25)):
            value_class = 'strong'
        elif 'good' in quality_class:
            value_class = 'moderate'
        else:
            value_class = 'weak'

        # Build metrics HTML
        time_metric = f'<span title="Time until market closes">⏱️ {time_left_str}</span>' if time_left_str else ''
        sportsbook_metric = f'<span title="Sportsbook consensus average">🎲 {sportsbook_str}</span>' if sportsbook_str else ''

        # Build card HTML as a single line to avoid Streamlit parsing issues
        card_html = f'<div class="market-card {card_class}"><div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;"><div style="flex: 1;"><div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; color: #f1f5f9;">{matchup}</div><div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;">{label}</div><div class="market-metrics"><span title="24-hour trading volume">📊 {volume_str}</span><span title="Open interest (total contracts)">📈 {oi_str}</span>{time_metric}{sportsbook_metric}</div></div><div style="text-align: right;"><div class="prob-badge {quality_class}">{prob_pct}</div><div class="value-indicator value-{value_class}">{quality_label}</div></div></div></div>'

        st.markdown(card_html, unsafe_allow_html=True)

        # Action button
        st.link_button("📊 View Details",
                       f"?page=detail&event={ev['event_ticker']}",
                       use_container_width=True)
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
        st.markdown(
            f"<div style='text-align: center; padding: 0.5rem; color: #94a3b8;'>Page {p}/{pages}</div>",
            unsafe_allow_html=True)
    with col3:
        if p < pages:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.p = p + 1
                qp_set(page="list")
                st.rerun()


def page_detail():
    render_top_nav("detail")

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

    # Use single column on mobile for better stacking
    metric_cols = st.columns(3)

    with metric_cols[0]:
        st.metric("24h Volume",
                  f"${ev.get('volume_24h_sum', 0):,}",
                  help="Total dollar volume traded in the last 24 hours")

    with metric_cols[1]:
        st.metric("Open Interest",
                  f"{ev.get('open_interest_sum', 0):,}",
                  help="Outstanding contracts (positions not yet closed)")

    with metric_cols[2]:
        if close_dt:
            hours_left = (close_dt -
                          datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_left > 0:
                st.metric("Time Left",
                          f"{int(hours_left)}h"
                          if hours_left < 48 else f"{int(hours_left/24)}d",
                          help="Time until market closes")
            else:
                st.metric("Status", "Closed", help="Market has closed")

    st.divider()

    # AI-Generated Game Preview
    st.subheader("🤖 AI Game Preview")
    with st.spinner("Generating AI-powered game analysis..."):
        gemini = GeminiService()
        away_team_name = ev.get("away_team", "")
        home_team_name = ev.get("home_team", "")

        # Get primary contract probability
        w_temp = ev.get("winner_primary", {}) or {}
        _, primary_prob = pick_display_label_and_bid(w_temp)

        # Try to get sportsbook odds for context
        sportsbook_prob = None
        try:
            odds_api = OddsAPIService()
            game_odds = odds_api.find_game_by_teams(away_team_name,
                                                    home_team_name)
            if game_odds:
                consensus = odds_api.get_market_consensus(game_odds)
                if consensus:
                    subject_team = w_temp.get('subject_team', '')
                    if subject_team == away_team_name and away_team_name in consensus:
                        sportsbook_prob = consensus[
                            away_team_name] / 100  # Convert percentage to decimal
                    elif subject_team == home_team_name and home_team_name in consensus:
                        sportsbook_prob = consensus[
                            home_team_name] / 100  # Convert percentage to decimal
        except Exception:
            pass

        # Generate game date string
        game_date = None
        if close_dt:
            game_date = close_dt.strftime('%B %d, %Y')

        summary = gemini.generate_game_summary(away_team=away_team_name,
                                               home_team=home_team_name,
                                               kalshi_prob=primary_prob,
                                               sportsbook_prob=sportsbook_prob,
                                               game_date=game_date)

        if summary:
            # Format the AI preview with better typography and spacing
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                    margin: 1rem 0;
                ">
                    <div style="
                        color: white;
                        font-size: 1.4rem;
                        line-height: 1.1;
                        font-weight: 400;
                        letter-spacing: 0.3px;
                    ">
                        {summary.replace('. ', '.<br><br>')}
                    </div>
                </div>
            """,
                        unsafe_allow_html=True)
        else:
            st.warning("AI game preview unavailable. Check back soon!")

    # Team Stat Leaders Section
    st.divider()
    st.subheader("⭐ Team Stat Leaders")

    with st.expander("View Key Player Stats", expanded=False):
        cols = st.columns(2)

        # Away team leaders
        with cols[0]:
            st.markdown(f"**{away_team_name}**")
            away_leaders = espn.get_team_leaders(away_team_name,
                                                 category='passing')
            if away_leaders:
                for leader in away_leaders[:3]:  # Top 3
                    st.write(
                        f"• **{leader.get('name')}** ({leader.get('position')}): {leader.get('value')}"
                    )
            else:
                st.caption("Stats unavailable")

        # Home team leaders
        with cols[1]:
            st.markdown(f"**{home_team_name}**")
            home_leaders = espn.get_team_leaders(home_team_name,
                                                 category='passing')
            if home_leaders:
                for leader in home_leaders[:3]:  # Top 3
                    st.write(
                        f"• **{leader.get('name')}** ({leader.get('position')}): {leader.get('value')}"
                    )
            else:
                st.caption("Stats unavailable")

    st.divider()

    # Winner Market with Visual Indicators
    w = ev.get("winner_primary", {}) or {}
    label, bid_val = pick_display_label_and_bid(w)

    # Get odds quality for visual indicator
    quality_label, quality_class, quality_desc = get_odds_quality(bid_val)

    # Display probability badge and quality indicator
    if bid_val is not None:
        st.markdown(
            f'<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;"><div class="prob-badge {quality_class}">{pct(bid_val)}</div><div class="value-indicator value-{"strong" if "excellent" in quality_class else "moderate" if "good" in quality_class else "weak"}">{quality_label}</div></div>',
            unsafe_allow_html=True)
        st.caption(f"**{label}** - {quality_desc}")

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

    # Sportsbook Odds vs Prediction Market Comparison
    st.divider()
    st.subheader("📊 Sportsbook Odds vs OddSense Market")

    # Initialize SportsGameOdds API service
    odds_api = OddsAPIService()

    away_team_name = ev.get("away_team", "")
    home_team_name = ev.get("home_team", "")

    # Try to fetch real-time betting odds from The Odds API
    with st.spinner("Fetching live betting odds from sportsbooks..."):
        game_odds = odds_api.find_game_by_teams(away_team_name, home_team_name)

        if game_odds:
            st.info(
                "**Comparing prediction markets to sportsbooks:** "
                "See how the prediction market compares to traditional sportsbook odds. "
                "Differences can reveal arbitrage opportunities or varying market confidence."
            )

            # Get consensus across all sportsbooks
            consensus = odds_api.get_market_consensus(game_odds)

            # Get prediction market probabilities for both teams
            away_kalshi_prob = None
            home_kalshi_prob = None

            # Find winner contracts - collect all first, then assign
            winner_contracts = []
            for contract in ev.get('all_contracts', []):
                title = contract.get('title', '') or ''
                # Only look at winner markets
                if 'winner' not in title.lower():
                    continue
                winner_contracts.append(contract)

            # Strategy 1: Try matching by team codes in event ticker
            event_ticker = ev.get('event_ticker', '')
            if event_ticker:
                # Extract team codes from ticker (e.g., KXNFLGAME-25NOV09ATLIND -> ATL, IND)
                import re
                codes = re.findall(r'[A-Z]{2,3}', event_ticker.upper())
                # Last 2 codes are usually away, home
                if len(codes) >= 2:
                    away_code, home_code = codes[-2], codes[-1]

                    # Match each winner contract to away or home
                    # Typical pattern: KXNFLGAME-25NOV09-ATL-IND-B-{TEAM}-WIN
                    # The team code appears near the end, after the event codes
                    for contract in winner_contracts:
                        ticker = (contract.get('ticker', '') or '').upper()
                        # Fallback chain: yes_bid -> last_price (for thin markets)
                        prob = contract.get('yes_bid') or contract.get(
                            'last_price')

                        # Look for pattern like -ATL-WIN or -ATL- near the end
                        # Split ticker into parts and check last few segments
                        ticker_parts = ticker.split('-')

                        # Check last 3 parts for team codes (before WIN suffix)
                        relevant_parts = ticker_parts[-3:] if len(
                            ticker_parts) >= 3 else ticker_parts

                        # Count occurrences in relevant parts only
                        away_in_end = away_code in relevant_parts
                        home_in_end = home_code in relevant_parts

                        if away_in_end and not home_in_end and away_kalshi_prob is None:
                            away_kalshi_prob = prob
                        elif home_in_end and not away_in_end and home_kalshi_prob is None:
                            home_kalshi_prob = prob

            # Strategy 2: If still missing, try text matching
            if away_kalshi_prob is None or home_kalshi_prob is None:
                for contract in winner_contracts:
                    if away_kalshi_prob is not None and home_kalshi_prob is not None:
                        break

                    title = contract.get('title', '') or ''
                    subtitle = contract.get('subtitle', '') or ''
                    full_text = f"{title} {subtitle}".lower()

                    # Fallback chain: yes_bid -> last_price (for thin markets)
                    prob = contract.get('yes_bid') or contract.get(
                        'last_price')

                    # Match team name parts
                    away_parts = [
                        p for p in away_team_name.lower().split() if len(p) > 2
                    ]
                    home_parts = [
                        p for p in home_team_name.lower().split() if len(p) > 2
                    ]

                    away_matches = sum(1 for part in away_parts
                                       if part in full_text)
                    home_matches = sum(1 for part in home_parts
                                       if part in full_text)

                    # Assign based on matches
                    if away_matches > home_matches and away_kalshi_prob is None:
                        away_kalshi_prob = prob
                    elif home_matches > away_matches and home_kalshi_prob is None:
                        home_kalshi_prob = prob
                    elif away_matches == home_matches and away_matches > 0:
                        # Tie - check for "Yes" in title to identify the team
                        if '— yes' in full_text.lower(
                        ) or 'yes' in subtitle.lower():
                            # This is likely the primary team - assign to first missing
                            if away_kalshi_prob is None:
                                away_kalshi_prob = prob
                            elif home_kalshi_prob is None:
                                home_kalshi_prob = prob

            # Strategy 3: Use winner_primary as fallback
            if away_kalshi_prob is None or home_kalshi_prob is None:
                winner_primary = ev.get('winner_primary', {})
                primary_team = winner_primary.get('subject_team', '')
                primary_bid = winner_primary.get('yes_bid')

                if primary_bid is not None:
                    # Determine if primary is away or home
                    if primary_team == away_team_name and away_kalshi_prob is None:
                        away_kalshi_prob = primary_bid
                    elif primary_team == home_team_name and home_kalshi_prob is None:
                        home_kalshi_prob = primary_bid

            # Derive complement if only one found
            if away_kalshi_prob is None and home_kalshi_prob is not None:
                away_kalshi_prob = 1 - home_kalshi_prob
            elif home_kalshi_prob is None and away_kalshi_prob is not None:
                home_kalshi_prob = 1 - away_kalshi_prob

            # Display comparison table
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.markdown("**Team**")
            with col2:
                st.markdown("**OddSense**")
            with col3:
                st.markdown("**Sportsbook Avg**")
            with col4:
                st.markdown("**Best Odds**")

            # Away team row
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.write(f"**{away_team_name}** (Away)")

            with col2:
                if away_kalshi_prob is not None:
                    st.metric("", f"{away_kalshi_prob*100:.1f}%")
                else:
                    st.write("—")

            with col3:
                if consensus and away_team_name in consensus:
                    avg_prob = consensus[away_team_name]
                    st.metric("", f"{avg_prob:.1f}%")
                else:
                    st.write("—")

            with col4:
                best = odds_api.get_best_odds(game_odds, away_team_name)
                if best:
                    st.metric(
                        "",
                        f"{best['odds']:+d}",
                        help=f"{best['bookmaker']}: {best['probability']:.1f}%"
                    )
                else:
                    st.write("—")

            # Home team row
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.write(f"**{home_team_name}** (Home)")

            with col2:
                if home_kalshi_prob is not None:
                    st.metric("", f"{home_kalshi_prob*100:.1f}%")
                else:
                    st.write("—")

            with col3:
                if consensus and home_team_name in consensus:
                    avg_prob = consensus[home_team_name]
                    st.metric("", f"{avg_prob:.1f}%")
                else:
                    st.write("—")

            with col4:
                best = odds_api.get_best_odds(game_odds, home_team_name)
                if best:
                    st.metric(
                        "",
                        f"{best['odds']:+d}",
                        help=f"{best['bookmaker']}: {best['probability']:.1f}%"
                    )
                else:
                    st.write("—")

            # Show available sportsbooks in an expander
            away_all_odds = odds_api.get_all_bookmaker_odds(
                game_odds, away_team_name)
            home_all_odds = odds_api.get_all_bookmaker_odds(
                game_odds, home_team_name)
            if away_all_odds or home_all_odds:
                with st.expander("📋 View All Sportsbook Odds"):
                    st.caption(
                        "**All available odds for this game:**")

                    # Create a dataframe for better display
                    odds_data = []

                    # Process away team odds
                    for odd in away_all_odds:
                        odds_data.append({
                            'Team':
                            f"{away_team_name} (Away)",
                            'Sportsbook':
                            odd['bookmaker'],
                            'Odds':
                            f"{odd['odds']:+d}",
                            'Win Prob':
                            f"{odd['probability']:.1f}%"
                        })

                    # Process home team odds
                    for odd in home_all_odds:
                        odds_data.append({
                            'Team':
                            f"{home_team_name} (Home)",
                            'Sportsbook':
                            odd['bookmaker'],
                            'Odds':
                            f"{odd['odds']:+d}",
                            'Win Prob':
                            f"{odd['probability']:.1f}%"
                        })

                    if odds_data:
                        df = pd.DataFrame(odds_data)
                        st.dataframe(df,
                                     use_container_width=True,
                                     hide_index=True)

        else:
            st.info(
                "Live sportsbook odds not currently available for this game. Check back closer to game time!"
            )

    # Historical Accuracy Comparison with ESPN Data
    st.divider()
    st.subheader("🎯 Market Prediction vs Actual Result")

    # Check if game has finished by looking at close_dt
    game_finished = False
    if close_dt:
        now = datetime.now(timezone.utc)
        game_finished = now > close_dt

    if game_finished and bid_val is not None:
        st.info(
            "**Compare predictions to reality:** "
            "See how accurate the prediction market was by comparing the implied probability to the actual game result from ESPN."
        )

        # Try to fetch ESPN game result
        with st.spinner("Fetching game result from ESPN..."):
            away_team_name = ev.get("away_team", "")
            home_team_name = ev.get("home_team", "")

            # Determine which team this market is for
            # The label contains team name and either "— Yes" or "— No"
            labeled_team = None
            is_yes_contract = "— Yes" in label
            is_no_contract = "— No" in label

            if away_team_name.lower() in label.lower():
                labeled_team = "away"
            elif home_team_name.lower() in label.lower():
                labeled_team = "home"

            if labeled_team and close_dt:
                game_result = espn.find_game_by_teams_and_date(
                    away_team=away_team_name,
                    home_team=home_team_name,
                    game_date=close_dt)

                if game_result:
                    # For No contracts, the bet is on the OPPONENT of the labeled team
                    # For Yes contracts, the bet is on the labeled team
                    if is_no_contract:
                        # No contract: betting the labeled team will LOSE
                        # So we're effectively betting on the opponent
                        bet_on_team = "home" if labeled_team == "away" else "away"
                        # The probability remains as-is (it's the chance the labeled team loses)
                        comparison = espn.compare_to_kalshi_odds(
                            game_result=game_result,
                            kalshi_probability=bid_val,
                            bet_on_team=bet_on_team)
                        comparison['contract_type'] = 'No'
                        comparison['labeled_team'] = labeled_team
                        # Calculate implied win probability for labeled team
                        comparison['implied_win_probability'] = 1 - bid_val
                    else:
                        # Yes contract: betting the labeled team will WIN
                        bet_on_team = labeled_team
                        comparison = espn.compare_to_kalshi_odds(
                            game_result=game_result,
                            kalshi_probability=bid_val,
                            bet_on_team=bet_on_team)
                        comparison['contract_type'] = 'Yes'

                    if comparison.get('status') == 'incomplete':
                        st.warning(comparison.get('message'))
                    else:
                        # Display comparison results
                        col1, col2 = st.columns(2)

                        with col1:
                            # Show appropriate metric based on contract type
                            if comparison.get('contract_type') == 'No':
                                # For No contracts, we're showing the opponent's win chance
                                # Label shows team X with No contract at Y%
                                # This means market gives opponent (100-Y)% chance to win
                                labeled_team_name = away_team_name if comparison.get(
                                    'labeled_team'
                                ) == 'away' else home_team_name
                                opponent_name = comparison.get('team_name')
                                implied_labeled_team_win = comparison.get(
                                    'implied_win_probability', 0)

                                st.metric(
                                    "Market Prediction",
                                    comparison.get('kalshi_percentage'),
                                    help=
                                    f"No contract on {labeled_team_name} at {pct(bid_val)} implies {opponent_name} has {comparison.get('kalshi_percentage')} chance to win"
                                )
                            else:
                                st.metric(
                                    "Market Prediction",
                                    comparison.get('kalshi_percentage'),
                                    help=
                                    f"Market was {comparison.get('confidence_level')} that {comparison.get('team_name')} would win"
                                )

                        with col2:
                            result_emoji = "✅" if comparison.get(
                                'bet_won') else "❌"
                            st.metric(
                                "Actual Result",
                                f"{result_emoji} {'Won' if comparison.get('bet_won') else 'Lost'}",
                                help=
                                f"Final score: {comparison.get('final_score', {}).get('away')} - {comparison.get('final_score', {}).get('home')}"
                            )

                        # Show analysis message
                        message = comparison.get('message', '')
                        if comparison.get('bet_won'):
                            st.success(message)
                        else:
                            if comparison.get('kalshi_probability', 0) >= 0.6:
                                st.error(message)
                            else:
                                st.info(message)
                else:
                    st.warning(
                        f"Could not find ESPN game data for {away_team_name} @ {home_team_name}"
                    )
            else:
                st.info("Unable to determine which team this market is for.")
    else:
        st.info(
            "Historical comparison will be available after the game finishes.")

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
            valid_candles = [
                c for c in candlesticks if c.get("close") is not None
            ]

            if valid_candles:
                timestamps = [c["timestamp"] for c in valid_candles]
                closes = [c["close"] for c in valid_candles]
                volumes = [c.get("volume", 0) for c in valid_candles]
            else:
                # No valid data
                timestamps, closes, volumes = [], [], []

            # Calculate trend
            if len(closes
                   ) >= 2 and closes[0] is not None and closes[-1] is not None:
                price_change = closes[-1] - closes[0]
                pct_change = (price_change / closes[0] *
                              100) if closes[0] > 0 else 0

                if abs(pct_change) > 5:
                    trend_emoji = "📈" if pct_change > 0 else "📉"
                    trend_text = f"{trend_emoji} **Market trend:** {'Rising' if pct_change > 0 else 'Falling'} ({pct_change:+.1f}% over the period shown)"
                else:
                    trend_text = "➡️ **Market trend:** Stable (minimal movement)"

                st.caption(trend_text)

            # Create price chart only if we have valid data
            if len(closes) > 0:
                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=timestamps,
                        y=closes,
                        mode='lines',
                        name='Close Price',
                        line=dict(color='#6366f1', width=3),
                        hovertemplate=
                        '<b>Time:</b> %{x}<br><b>Price:</b> $%{y:.2f}<extra></extra>'
                    ))

                fig.update_layout(title="Price Over Time (Hourly)",
                                  xaxis_title="Time",
                                  yaxis_title="Price (Probability)",
                                  yaxis=dict(tickformat='.0%', range=[0, 1]),
                                  hovermode='x unified',
                                  height=400,
                                  template='plotly_dark',
                                  paper_bgcolor='#1e293b',
                                  plot_bgcolor='#1e293b',
                                  font=dict(color='#f1f5f9'))

                st.plotly_chart(fig, use_container_width=True)

                # Volume chart
                if len(volumes) > 0 and max(volumes) > 0:
                    fig_vol = go.Figure()
                    fig_vol.add_trace(
                        go.Bar(
                            x=timestamps,
                            y=volumes,
                            name='Volume',
                            marker_color='#10b981',
                            hovertemplate=
                            '<b>Time:</b> %{x}<br><b>Volume:</b> %{y}<extra></extra>'
                        ))

                    fig_vol.update_layout(title="Trading Volume Over Time",
                                          xaxis_title="Time",
                                          yaxis_title="Volume",
                                          height=300,
                                          template='plotly_dark',
                                          paper_bgcolor='#1e293b',
                                          plot_bgcolor='#1e293b',
                                          font=dict(color='#f1f5f9'))

                    with st.expander("📊 View Volume History"):
                        st.caption(
                            "**Volume spikes** can indicate important news or events affecting trader sentiment."
                        )
                        st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info(
                    "Historical price data contains no valid close prices. This can happen for newly created markets."
                )
        else:
            st.info(
                "Historical price data not yet available for this market. Check back after some trading activity."
            )

    # Order Book (Collapsed for mobile)
    st.divider()

    with st.expander("📖 Current Order Book", expanded=False):
        if ticker:
            st.info(
                "The order book shows pending buy/sell orders. "
                "'Yes' orders bet the outcome happens; 'No' orders bet it doesn't."
            )

            orderbook = kalshi.get_market_orderbook(ticker)

            if orderbook:
                col_yes, col_no = st.columns(2)

                with col_yes:
                    st.markdown("**YES Orders**")
                    yes_orders = orderbook.get("yes", [])
                    if yes_orders:
                        yes_df = pd.DataFrame(yes_orders[:10])  # Top 10
                        if not yes_df.empty and "price" in yes_df.columns and "size" in yes_df.columns:
                            yes_display = yes_df[["price", "size"]].copy()
                            yes_display.columns = ["Price", "Size"]
                            st.dataframe(yes_display,
                                         hide_index=True,
                                         use_container_width=True)
                    else:
                        st.caption("No YES orders")

                with col_no:
                    st.markdown("**NO Orders**")
                    no_orders = orderbook.get("no", [])
                    if no_orders:
                        no_df = pd.DataFrame(no_orders[:10])  # Top 10
                        if not no_df.empty and "price" in no_df.columns and "size" in no_df.columns:
                            no_display = no_df[["price", "size"]].copy()
                            no_display.columns = ["Price", "Size"]
                            st.dataframe(no_display,
                                         hide_index=True,
                                         use_container_width=True)
                    else:
                        st.caption("No NO orders")
            else:
                st.info("Order book data not available.")
        else:
            st.info("No ticker available for order book.")

    st.divider()

    with st.expander("📋 All Event Contracts", expanded=False):
        st.caption(
            "Complete list of all betting contracts for this game, including player props and other markets."
        )

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