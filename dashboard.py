#!/usr/bin/env python3
"""
Antigravity Kite & IPO Terminal Dashboard
Interactive full-screen analytics dashboard with one-click Zerodha authentication,
live Demat portfolio tracking, real-time GMP, and Gemini AI synthesis.

Usage:
    streamlit run dashboard.py
"""

import streamlit as st
from config import get_config
from ui.ai_research_view import render_ai_research_view
from ui.auth_view import auto_handle_oauth_redirect, check_auth_status, render_auth_view
from ui.ipo_view import render_ipo_view
from ui.portfolio_view import render_portfolio_view

# 1. Page Configuration
st.set_page_config(
    page_title="Antigravity Kite & IPO Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-handle Zerodha OAuth redirect if returning from authorization
auto_handle_oauth_redirect(get_config("KITE_API_KEY"), get_config("KITE_API_SECRET"))

# 2. Sleek Custom Styling
st.markdown(
    """
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 14px; border-radius: 8px; border: 1px solid #2e3342; }
    div[data-testid="stSidebar"] { background-color: #131722; border-right: 1px solid #2e3342; }
    .status-badge-ok { color: #00e676; font-weight: bold; }
    .status-badge-err { color: #ff5252; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Sidebar Overview
with st.sidebar:
    st.title("📈 Antigravity Terminal")
    st.caption("Zerodha Kite + IPO AI Suite")
    st.divider()

    # Connection Status Pill
    is_valid, msg, profile = check_auth_status()
    st.markdown("### 🔌 System Status")
    if is_valid and profile:
        st.markdown(f"• **Kite Connect:** <span class='status-badge-ok'>● Online</span>", unsafe_allow_html=True)
        st.caption(f"Connected as {profile.get('user_name', '')} ({profile.get('user_id', '')})")
    else:
        st.markdown(f"• **Kite Connect:** <span class='status-badge-err'>● Login Needed</span>", unsafe_allow_html=True)
        st.caption(msg)

    st.markdown(f"• **Gemini AI:** <span class='status-badge-ok'>● Ready</span>", unsafe_allow_html=True)
    st.markdown(f"• **IPO Scrapers:** <span class='status-badge-ok'>● Active (53 Tracked)</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔑 Daily Kite Login (1-Click)", use_container_width=True):
        st.session_state["active_tab"] = "🔑 Authenticate"
        st.rerun()

    st.caption("Powered by Google Antigravity & Model Context Protocol (MCP)")


# 4. Main Tab Navigation
tabs = [
    "📊 Portfolio & Demat",
    "🔥 Live IPOs & GMP",
    "🤖 AI Research & Videos",
    "🔑 Authenticate",
]

default_idx = 0
if "active_tab" in st.session_state and st.session_state["active_tab"] in tabs:
    default_idx = tabs.index(st.session_state["active_tab"])

selected_tab = st.radio(
    "Navigation",
    tabs,
    index=default_idx,
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

if selected_tab == "📊 Portfolio & Demat":
    render_portfolio_view()
elif selected_tab == "🔥 Live IPOs & GMP":
    render_ipo_view()
elif selected_tab == "🤖 AI Research & Videos":
    render_ai_research_view()
elif selected_tab == "🔑 Authenticate":
    render_auth_view()
