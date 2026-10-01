"""
IPO Market & GMP Live Tracker View
Displays active, upcoming, and closed IPO listings, Grey Market Premiums,
subscription demand, and color-coded status categories.
"""

import pandas as pd
import streamlit as st
import ipo_mcp
from ui.common import render_back_to_top


def _style_status(val: str) -> str:
    """Format status badge colors."""
    if val == "Open":
        return "background-color: #1b5e20; color: #a5d6a7; font-weight: bold; border-radius: 4px;"
    elif val == "Upcoming":
        return "background-color: #0d47a1; color: #90caf9; font-weight: bold; border-radius: 4px;"
    elif val == "Closed":
        return "background-color: #37474f; color: #cfd8dc; border-radius: 4px;"
    return ""


def _style_type(val: str) -> str:
    """Format IPO category tags."""
    if val == "Mainboard":
        return "color: #64b5f6; font-weight: 600;"
    elif val == "SME":
        return "color: #ce93d8; font-weight: 600;"
    return ""


def _style_gmp_pct(val: float) -> str:
    """Format GMP gain percentage color indicators."""
    try:
        num = float(val)
        if num >= 25.0:
            return "color: #00e676; font-weight: bold;"
        elif num >= 10.0:
            return "color: #81c784; font-weight: bold;"
        elif num < 0.0:
            return "color: #ff5252; font-weight: bold;"
        return "color: #ffd54f;"
    except (ValueError, TypeError):
        return ""


def render_ipo_view():
    """Render the active, upcoming, and closed IPO tracking board."""
    st.subheader("🔥 Live IPO Market & Grey Market Premium (GMP)")

    # 1. Controls & Filter Bar
    c_cat, c_stat, c_sort, c_search = st.columns([1, 1, 1.2, 1.8])
    with c_cat:
        category_filter = st.selectbox("Category", ["All", "Mainboard", "SME"])
    with c_stat:
        status_filter = st.selectbox("Status", ["All", "Open", "Upcoming", "Closed"])
    with c_sort:
        sort_by = st.selectbox(
            "Sort By",
            [
                "Highest Gain %",
                "Highest GMP (₹)",
                "Most Subscribed",
                "Company Name",
            ],
        )
    with c_search:
        search_query = st.text_input("Search IPO", placeholder="e.g. Acme, Tata, Solar...")

    with st.spinner("Fetching latest live IPO market data & GMPs..."):
        data = ipo_mcp.get_upcoming_ipos()

    if data.get("status") == "error":
        st.error(f"Failed to fetch IPO data: {data.get('message')}")
        return

    ipos = data.get("ipos", [])
    if not ipos:
        st.info("No active or upcoming IPOs found at the moment.")
        return

    # 2. Filter Logic & Secondary Header Defense
    header_blacklist = {"name", "company", "ipo name", "company name"}
    filtered_ipos = [
        i for i in ipos
        if i.get("company_name", "").strip().lower() not in header_blacklist
        and "price" not in str(i.get("price_band", "")).lower()
        and "gmp" not in str(i.get("company_name", "")).lower()
    ]
    if category_filter != "All":
        filtered_ipos = [i for i in filtered_ipos if i.get("type") == category_filter]
    if status_filter != "All":
        filtered_ipos = [i for i in filtered_ipos if i.get("status") == status_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_ipos = [i for i in filtered_ipos if q in i.get("company_name", "").lower()]

    # 3. Sorting Logic
    if sort_by == "Highest Gain %":
        filtered_ipos.sort(key=lambda x: x.get("gmp_percentage", 0.0), reverse=True)
    elif sort_by == "Highest GMP (₹)":
        filtered_ipos.sort(key=lambda x: x.get("gmp_in_rs", 0.0), reverse=True)
    elif sort_by == "Most Subscribed":
        filtered_ipos.sort(key=lambda x: x.get("subscription_multiple", 0.0), reverse=True)
    elif sort_by == "Company Name":
        filtered_ipos.sort(key=lambda x: x.get("company_name", "").lower())

    # 4. Summary KPI Metrics
    open_count = sum(1 for i in filtered_ipos if i.get("status") == "Open")
    upcoming_count = sum(1 for i in filtered_ipos if i.get("status") == "Upcoming")
    avg_gmp = sum(i.get("gmp_percentage", 0.0) for i in filtered_ipos) / len(filtered_ipos) if filtered_ipos else 0.0
    highest_gmp = max(filtered_ipos, key=lambda x: x.get("gmp_percentage", 0.0)) if filtered_ipos else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Displaying IPOs", f"{len(filtered_ipos)} of {len(ipos)}")
    c2.metric("Open for Bidding", f"{open_count} Live", delta=f"{upcoming_count} Upcoming", delta_color="normal")
    c3.metric("Average Expected Gain", f"{avg_gmp:.1f}%")
    if highest_gmp:
        c4.metric(
            "Top Listing Gain",
            highest_gmp.get("company_name", "")[:18],
            f"+{highest_gmp.get('gmp_percentage', 0.0)}% GMP",
        )

    st.divider()

    # 5. Formatted Color-Coded Data Table
    df = pd.DataFrame(filtered_ipos)
    if not df.empty:
        display_map = {
            "company_name": "Company",
            "type": "Type",
            "status": "Status",
            "price_band": "Price Band (₹)",
            "gmp_in_rs": "GMP (₹)",
            "gmp_percentage": "Expected Gain %",
            "subscription_multiple": "Subscription",
            "lot_size": "Lot Size",
            "issue_size": "Issue Size",
            "open_date": "Open Date",
            "close_date": "Close Date",
            "listing_date": "Listing Date",
        }
        cols_to_use = [c for c in display_map.keys() if c in df.columns]
        df_table = df[cols_to_use].rename(columns=display_map)

        styler = df_table.style

        # Apply conditional coloring safely across Pandas versions
        if hasattr(styler, "map"):
            if "Status" in df_table.columns:
                styler = styler.map(_style_status, subset=["Status"])
            if "Type" in df_table.columns:
                styler = styler.map(_style_type, subset=["Type"])
            if "Expected Gain %" in df_table.columns:
                styler = styler.map(_style_gmp_pct, subset=["Expected Gain %"])
        else:
            if "Status" in df_table.columns:
                styler = styler.applymap(_style_status, subset=["Status"])
            if "Type" in df_table.columns:
                styler = styler.applymap(_style_type, subset=["Type"])
            if "Expected Gain %" in df_table.columns:
                styler = styler.applymap(_style_gmp_pct, subset=["Expected Gain %"])

        styler = styler.format({
            "GMP (₹)": "₹{:,.1f}",
            "Expected Gain %": "{:+.1f}%",
            "Subscription": "{:.2f}x",
        })

        st.dataframe(styler, use_container_width=True, hide_index=True)
    else:
        st.warning("No IPOs match your filter criteria.")

    render_back_to_top()
