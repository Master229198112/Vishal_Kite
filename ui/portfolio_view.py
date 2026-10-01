"""
Zerodha Kite Portfolio & Demat View
Displays live equity & ETF holdings, cash margins, and open positions.
"""

import pandas as pd
import streamlit as st
import kite_mcp


def render_portfolio_view():
    """Render the portfolio, holdings, positions, and margins dashboard."""
    col_hdr, col_btn = st.columns([4, 1])
    with col_hdr:
        st.subheader("📊 Zerodha Kite Demat & Portfolio")
    with col_btn:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # 1. Fetch Margins & Holdings
    with st.spinner("Fetching live portfolio from Zerodha Kite..."):
        margins_res = kite_mcp.get_margins()
        holdings_res = kite_mcp.get_holdings()
        positions_res = kite_mcp.get_positions()

    if margins_res.get("status") == "error":
        st.error(f"Failed to fetch portfolio data: {margins_res.get('message')}")
        st.info("Tip: If your session expired, go to the **'🔑 Authenticate'** tab to refresh your daily token.")
        return

    # Extract Top Metrics
    cash_bal = margins_res.get("summary", {}).get("equity", {}).get("available_cash", 0.0)
    h_summary = holdings_res.get("summary", {})
    tot_invested = h_summary.get("total_investment", 0.0)
    cur_value = h_summary.get("current_value", 0.0)
    tot_pnl = h_summary.get("total_pnl", 0.0)
    tot_pnl_pct = h_summary.get("total_pnl_percentage", 0.0)

    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Available Cash Balance", f"₹{cash_bal:,.2f}")
    m2.metric("Total Investment", f"₹{tot_invested:,.2f}")
    m3.metric("Current Portfolio Value", f"₹{cur_value:,.2f}")
    m4.metric(
        "Overall Unrealised P&L",
        f"₹{tot_pnl:,.2f}",
        delta=f"{tot_pnl_pct:+.2f}%",
        delta_color="normal",
    )

    st.divider()

    # 2. Holdings Table
    st.markdown("### 📈 Equity & ETF Holdings")
    raw_holdings = holdings_res.get("holdings", [])
    if raw_holdings:
        df_holdings = pd.DataFrame(raw_holdings)
        # Select and rename columns for display
        display_cols = {
            "tradingsymbol": "Stock Symbol",
            "exchange": "Exchange",
            "quantity": "Qty",
            "average_price": "Avg Buy Price (₹)",
            "last_price": "CMP (₹)",
            "pnl": "P&L (₹)",
            "pnl_percentage": "P&L %",
            "day_change_percentage": "Day Change %",
        }
        df_display = df_holdings[list(display_cols.keys())].rename(columns=display_cols)

        # Style dataframe
        st.dataframe(
            df_display.style.format({
                "Avg Buy Price (₹)": "₹{:,.2f}",
                "CMP (₹)": "₹{:,.2f}",
                "P&L (₹)": "₹{:,.2f}",
                "P&L %": "{:+.2f}%",
                "Day Change %": "{:+.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No long-term holdings found in this Demat account.")

    st.divider()

    # 3. Margins & Positions Accordion
    c_pos, c_mar = st.columns(2)

    with c_pos:
        st.markdown("### ⚡ Open Positions")
        open_pos = positions_res.get("open_positions", [])
        if open_pos:
            st.dataframe(pd.DataFrame(open_pos), use_container_width=True)
        else:
            st.caption("No open intraday (MIS) or derivative (F&O) positions.")

    with c_mar:
        st.markdown("### 💼 Margin Details")
        eq_details = margins_res.get("summary", {}).get("equity", {})
        st.write(f"• **Live Balance:** ₹{eq_details.get('live_balance', 0.0):,.2f}")
        st.write(f"• **Used Margin (Debits):** ₹{eq_details.get('used_margin', 0.0):,.2f}")
        st.write(f"• **SPAN Margin:** ₹{eq_details.get('span_margin', 0.0):,.2f}")
        st.write(f"• **Exposure Margin:** ₹{eq_details.get('exposure_margin', 0.0):,.2f}")
        st.write(f"• **Collateral Available:** ₹{eq_details.get('collateral', 0.0):,.2f}")
