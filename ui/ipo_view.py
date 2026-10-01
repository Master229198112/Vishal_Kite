"""
IPO Market & GMP Live Tracker View
Displays active & upcoming IPO listings, Grey Market Premiums, and bidding demand.
"""

import pandas as pd
import streamlit as st
import ipo_mcp


def render_ipo_view():
    """Render the active and upcoming IPO tracking board."""
    st.subheader("🔥 Live IPO Market & Grey Market Premium (GMP)")

    col_filter1, col_filter2, col_search = st.columns([1, 1, 2])
    with col_filter1:
        category_filter = st.selectbox("Category", ["All", "Mainboard", "SME"])
    with col_filter2:
        status_filter = st.selectbox("Status", ["All", "Open", "Upcoming"])
    with col_search:
        search_query = st.text_input("Search IPO Name", placeholder="e.g. Acme, TNA, Tata...")

    with st.spinner("Fetching latest live IPO market data & GMPs..."):
        data = ipo_mcp.get_upcoming_ipos()

    if data.get("status") == "error":
        st.error(f"Failed to fetch IPO data: {data.get('message')}")
        return

    ipos = data.get("ipos", [])
    if not ipos:
        st.info("No active or upcoming IPOs found at the moment.")
        return

    # Apply filters
    filtered_ipos = ipos
    if category_filter != "All":
        filtered_ipos = [i for i in filtered_ipos if i.get("type") == category_filter]
    if status_filter != "All":
        filtered_ipos = [i for i in filtered_ipos if i.get("status") == status_filter]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_ipos = [i for i in filtered_ipos if q in i.get("company_name", "").lower()]

    # Metric summaries
    avg_gmp = sum(i.get("gmp_percentage", 0.0) for i in filtered_ipos) / len(filtered_ipos) if filtered_ipos else 0.0
    highest_gmp = max(filtered_ipos, key=lambda x: x.get("gmp_percentage", 0.0)) if filtered_ipos else None

    c1, c2, c3 = st.columns(3)
    c1.metric("Tracked IPOs", len(filtered_ipos))
    c2.metric("Average GMP %", f"{avg_gmp:.1f}%")
    if highest_gmp:
        c3.metric(
            "Top Listing Gain Candidate",
            highest_gmp.get("company_name")[:20],
            f"+{highest_gmp.get('gmp_percentage', 0)}% GMP",
        )

    st.divider()

    # Formatted Data Table
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

        st.dataframe(
            df_table.style.format({
                "GMP (₹)": "₹{:,.1f}",
                "Expected Gain %": "{:+.1f}%",
                "Subscription": "{:.2f}x",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No IPOs match your filter criteria.")
