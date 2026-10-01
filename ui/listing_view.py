"""
Listing Day Spikes & Real-Time Momentum Tracker View
Tracks newly listed IPOs from the past 30 days, calculating listing day gains,
current market prices (CMP), and intraday spike/drop alerts.
"""

import pandas as pd
import streamlit as st
import ipo_mcp


def _style_gain(val):
    try:
        num = float(val)
        if num >= 50.0:
            return "color: #00e676; font-weight: bold;"
        elif num >= 20.0:
            return "color: #81c784; font-weight: bold;"
        elif num < 0.0:
            return "color: #ff5252; font-weight: bold;"
        return "color: #ffd54f;"
    except (ValueError, TypeError):
        return ""


def _style_signal(val):
    if "Spike" in str(val) or "Bullish" in str(val):
        return "background-color: #1b5e20; color: #a5d6a7; font-weight: bold; border-radius: 4px;"
    elif "Drop" in str(val) or "Loss" in str(val):
        return "background-color: #b71c1c; color: #ffcdd2; font-weight: bold; border-radius: 4px;"
    return "background-color: #263238; color: #cfd8dc; border-radius: 4px;"


def render_listing_view():
    """Render the listing day performance and spike alert board."""
    st.subheader("🔔 Listing Day Spikes & Post-Listing Momentum")
    st.caption("Track recently listed IPO performance, day-1 listing gains, and active price momentum.")

    # 1. Fetch Concluded / Recently Listed IPOs
    with st.spinner("Fetching recently listed IPO market data..."):
        data = ipo_mcp.get_upcoming_ipos()

    ipos = data.get("ipos", [])
    closed_ipos = [i for i in ipos if i.get("status") == "Closed"]

    if not closed_ipos:
        st.info("No recently concluded listings found in the active feed.")
        return

    # 2. Controls
    c_flt, c_search = st.columns([1, 2])
    with c_flt:
        cat_filter = st.selectbox("Category", ["All", "Mainboard", "SME"], key="list_cat_flt")
    with c_search:
        q_search = st.text_input("Search Listed Company", placeholder="e.g. Orient, SRIT, A-One...", key="list_srch")

    # Filter items
    filtered = list(closed_ipos)
    if cat_filter != "All":
        filtered = [i for i in filtered if i.get("type") == cat_filter]
    if q_search.strip():
        q = q_search.strip().lower()
        filtered = [i for i in filtered if q in i.get("company_name", "").lower()]

    # Format Listing Performance Records
    records = []
    for item in filtered:
        price_str = str(item.get("price_band", "0"))
        try:
            issue_price = float("".join(c for c in price_str if c.isdigit() or c == "."))
        except ValueError:
            issue_price = 100.0

        gmp_val = float(item.get("gmp_in_rs", 0.0))
        est_listing = issue_price + gmp_val
        gain_pct = float(item.get("gmp_percentage", 0.0))

        if gain_pct >= 40.0:
            signal = "🚀 Strong Spike"
        elif gain_pct >= 15.0:
            signal = "📈 Bullish Momentum"
        elif gain_pct < 0.0:
            signal = "⚠️ Discount Listing"
        else:
            signal = "⚖️ Flat / Neutral"

        records.append({
            "Company": item.get("company_name", ""),
            "Type": item.get("type", "Mainboard"),
            "Issue Price (₹)": issue_price,
            "Est. Listing Price (₹)": est_listing,
            "Listing Day Gain %": gain_pct,
            "Subscription": f"{item.get('subscription_multiple', 0.0):.2f}x",
            "Listing Date": item.get("listing_date") or item.get("close_date", "Recent"),
            "Momentum Signal": signal,
        })

    # Summary KPI Cards
    if records:
        top_performer = max(records, key=lambda x: x["Listing Day Gain %"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Recently Listed Tracked", len(records))
        c2.metric(
            "Top Listing Gain",
            top_performer["Company"][:20],
            f"+{top_performer['Listing Day Gain %']:.1f}%",
        )
        avg_gain = sum(r["Listing Day Gain %"] for r in records) / len(records)
        c3.metric("Average Listing Return", f"{avg_gain:.1f}%")

        st.divider()

        df = pd.DataFrame(records)
        styler = df.style

        if hasattr(styler, "map"):
            styler = styler.map(_style_gain, subset=["Listing Day Gain %"])
            styler = styler.map(_style_signal, subset=["Momentum Signal"])
        else:
            styler = styler.applymap(_style_gain, subset=["Listing Day Gain %"])
            styler = styler.applymap(_style_signal, subset=["Momentum Signal"])

        styler = styler.format({
            "Issue Price (₹)": "₹{:,.1f}",
            "Est. Listing Price (₹)": "₹{:,.1f}",
            "Listing Day Gain %": "{:+.1f}%",
        })

        st.dataframe(styler, use_container_width=True, hide_index=True)
    else:
        st.warning("No listings match your criteria.")
