#!/usr/bin/env python3
"""
Antigravity Kite & IPO Terminal Dashboard
Interactive full-screen analytics dashboard with role-based authentication,
bcrypt security, live Zerodha portfolio & mutual funds, real-time GMP, and Gemini AI.

Usage:
    streamlit run dashboard.py
"""

import streamlit as st
import auth_manager
from config import get_config
from ui.ai_research_view import render_ai_research_view
from ui.alerts_view import render_alerts_view
from ui.allotment_view import render_allotment_view
from ui.auth_view import auto_handle_oauth_redirect, check_auth_status, render_auth_view
from ui.ipo_view import render_ipo_view
from ui.listing_view import render_listing_view
from ui.portfolio_view import render_portfolio_view
from ui.profile_view import render_profile_view

# 1. Page Configuration
st.set_page_config(
    page_title="Antigravity Kite & IPO Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-handle Zerodha OAuth redirect if returning from authorization
auto_handle_oauth_redirect(get_config("KITE_API_KEY"), get_config("KITE_API_SECRET"))

# 2. Sleek Dark Theme Custom Styling & Navigation Elements
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .main {
        scroll-behavior: smooth !important;
    }
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e222d; padding: 14px; border-radius: 8px; border: 1px solid #2e3342; }
    div[data-testid="stSidebar"] { background-color: #131722; border-right: 1px solid #2e3342; }
    .status-badge-ok { color: #00e676; font-weight: bold; }
    .status-badge-err { color: #ff5252; font-weight: bold; }
    .status-badge-guest { color: #ffd54f; font-weight: bold; }
    .role-badge { background-color: #1b5e20; color: #a5d6a7; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }

    /* Back to Top UI Components */
    .back-to-top-inline {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 9px 24px;
        background-color: #1e222d;
        color: #90caf9 !important;
        border: 1px solid #2e3342;
        border-radius: 24px;
        text-decoration: none !important;
        font-size: 0.92rem;
        font-weight: 500;
        transition: all 0.25s ease-in-out;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    }
    .back-to-top-inline:hover {
        background-color: #29b6f6;
        color: #0e1117 !important;
        border-color: #29b6f6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(41, 182, 246, 0.35);
    }
    .back-to-top-floating {
        position: fixed;
        bottom: 24px;
        right: 24px;
        background-color: #1e222d;
        color: #90caf9 !important;
        border: 1px solid #3d4457;
        border-radius: 30px;
        padding: 8px 18px;
        font-size: 0.86rem;
        font-weight: 600;
        text-decoration: none !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
        z-index: 99999;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        transition: all 0.25s ease-in-out;
    }
    .back-to-top-floating:hover {
        background-color: #00e676;
        color: #0e1117 !important;
        border-color: #00e676;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 230, 118, 0.4);
    }
    </style>
    <div id="top-of-page"></div>
    <a href="#top-of-page" target="_self" class="back-to-top-floating" title="Back to Top">
        ⬆️ Top
    </a>
    """,
    unsafe_allow_html=True,
)

# 3. Sidebar: Authentication Status & Quick Controls
with st.sidebar:
    st.title("📈 Antigravity Terminal")
    st.caption("Zerodha Kite + Mutual Funds + IPO AI Suite")
    st.divider()

    user_logged_in = auth_manager.is_authenticated()
    current_user = auth_manager.get_current_user()

    if user_logged_in and current_user:
        st.markdown(
            f"👤 **{current_user.get('full_name', 'User')}** "
            f"<span class='role-badge'>{current_user.get('role', 'Owner').upper()}</span>",
            unsafe_allow_html=True,
        )
        st.caption(f"Demat ID: {current_user.get('kite_client_id', 'DF2893')}")

        if st.button("🚪 Sign Out", key="sidebar_logout_btn", use_container_width=True):
            auth_manager.logout_session()
            st.session_state["nav_tab"] = "🔥 Live IPOs & GMP"
            st.rerun()
    else:
        st.markdown("👤 **Visitor Access:** <span class='status-badge-guest'>Guest Mode</span>", unsafe_allow_html=True)
        st.caption("Public IPO & AI tools are open. Demat is locked.")

        with st.expander("🔐 Sign In to Access Demat", expanded=False):
            with st.form("sidebar_login_form"):
                u_in = st.text_input("Username", placeholder="e.g. vishal")
                p_in = st.text_input("Password", type="password")
                login_btn = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                if login_btn:
                    ok, msg, u_obj = auth_manager.authenticate_user(u_in, p_in)
                    if ok and u_obj:
                        auth_manager.login_session(u_obj)
                        st.session_state["nav_tab"] = "📊 Portfolio & Demat"
                        st.rerun()
                    else:
                        st.error(msg)

    st.divider()

    # System Status Indicators
    st.markdown("### 🔌 System Services")
    if user_logged_in:
        is_valid, msg, profile = check_auth_status()
        if is_valid and profile:
            st.markdown("• **Kite Connect:** <span class='status-badge-ok'>● Online</span>", unsafe_allow_html=True)
        else:
            st.markdown("• **Kite Connect:** <span class='status-badge-err'>● Token Expired</span>", unsafe_allow_html=True)
    else:
        st.markdown("• **Kite Connect:** <span class='status-badge-guest'>🔒 Login Required</span>", unsafe_allow_html=True)

    st.markdown("• **Gemini AI:** <span class='status-badge-ok'>● Ready</span>", unsafe_allow_html=True)
    st.markdown("• **IPO Market Feed:** <span class='status-badge-ok'>● Active (Live & Past)</span>", unsafe_allow_html=True)

    st.divider()
    if user_logged_in:
        c_qa1, c_qa2 = st.columns(2)
        with c_qa1:
            if st.button("🔑 Kite Login", use_container_width=True):
                st.session_state["nav_tab"] = "🔑 Authenticate"
                st.rerun()
        with c_qa2:
            if st.button("📢 Briefing", use_container_width=True):
                st.session_state["nav_tab"] = "📢 Morning Briefing"
                st.rerun()

    st.caption("Secured with bcrypt & Model Context Protocol (MCP)")


# 4. Role-Based Navigation Tabs
if user_logged_in:
    tabs = [
        "📊 Portfolio & Demat",
        "🔥 Live IPOs & GMP",
        "🤖 AI Research & Videos",
        "🔍 Allotment Status",
        "🔔 Listing Spikes",
        "📢 Morning Briefing",
        "🔑 Authenticate",
        "👤 Profile & Password",
    ]
else:
    tabs = [
        "🔥 Live IPOs & GMP",
        "🤖 AI Research & Videos",
        "🔍 Allotment Status",
        "🔔 Listing Spikes",
        "🔒 Sign In / Demat",
    ]

# Manage tab state cleanly with direct widget binding (Fixes 2-click issue)
if "nav_tab" not in st.session_state or st.session_state["nav_tab"] not in tabs:
    st.session_state["nav_tab"] = tabs[0]

selected_tab = st.radio(
    "Navigation",
    tabs,
    key="nav_tab",
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# 5. Tab View Routing
if selected_tab == "📊 Portfolio & Demat":
    render_portfolio_view()
elif selected_tab == "🔥 Live IPOs & GMP":
    render_ipo_view()
elif selected_tab == "🤖 AI Research & Videos":
    render_ai_research_view()
elif selected_tab == "🔍 Allotment Status":
    render_allotment_view()
elif selected_tab == "🔔 Listing Spikes":
    render_listing_view()
elif selected_tab == "📢 Morning Briefing":
    render_alerts_view()
elif selected_tab == "🔑 Authenticate":
    render_auth_view()
elif selected_tab == "👤 Profile & Password":
    render_profile_view()
elif selected_tab == "🔒 Sign In / Demat":
    st.subheader("🔐 Restricted Access: Zerodha Demat & Portfolio")
    st.info("Personal equity holdings, Zerodha Coin mutual funds, and trading margins are protected.")

    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("main_login_form"):
            st.markdown("#### Enter Credentials")
            main_u = st.text_input("Username", placeholder="e.g. vishal")
            main_p = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)

            if submit:
                ok, msg, u_obj = auth_manager.authenticate_user(main_u, main_p)
                if ok and u_obj:
                    auth_manager.login_session(u_obj)
                    st.session_state["nav_tab"] = "📊 Portfolio & Demat"
                    st.rerun()
                else:
                    st.error(msg)
    with col2:
        st.markdown("#### 🛡️ Public & Private Isolation")
        st.write("• **Public Friends:** Can freely explore real-time IPO listings, Grey Market Premiums, and run Gemini AI research.")
        st.write("• **Account Owner:** Only verified credentials grant access to Demat balances, mutual funds, and trade tokens.")
