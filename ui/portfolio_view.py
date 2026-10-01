"""
Zerodha Kite Portfolio & Demat View
Displays live equity & ETF holdings, Zerodha Coin mutual funds,
margins, open positions, and combined net worth metrics.
"""

import pandas as pd
import streamlit as st
import auth_manager
import kite_mcp


def render_portfolio_view():
    """Render the authenticated portfolio, mutual funds, positions, and margins dashboard."""
    if not auth_manager.is_authenticated():
        st.warning("🔒 Personal Portfolio & Demat data is locked.")
        st.info("Please sign in from the sidebar or the Profile tab to view your personal holdings.")
        return

    col_hdr, col_btn = st.columns([4, 1])
    with col_hdr:
        st.subheader("📊 Zerodha Kite Demat & Portfolio")
    with col_btn:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    # 1. Fetch Margins, Holdings, Mutual Funds, and Positions
    with st.spinner("Fetching live portfolio & mutual funds from Zerodha Kite..."):
        margins_res = kite_mcp.get_margins()
        holdings_res = kite_mcp.get_holdings()
        mf_res = kite_mcp.get_mf_holdings()
        positions_res = kite_mcp.get_positions()

    if margins_res.get("status") == "error":
        st.error(f"Failed to fetch portfolio data: {margins_res.get('message')}")
        st.info("Tip: If your session expired, go to the **'🔑 Authenticate'** tab to refresh your daily token.")
        return

    # Extract Metrics
    cash_bal = margins_res.get("summary", {}).get("equity", {}).get("available_cash", 0.0)

    # Equities summary
    h_sum = holdings_res.get("summary", {})
    eq_invested = h_sum.get("total_investment", 0.0)
    eq_cur_val = h_sum.get("current_value", 0.0)
    eq_pnl = h_sum.get("total_pnl", 0.0)
    eq_pnl_pct = h_sum.get("total_pnl_percentage", 0.0)

    # Mutual Funds summary
    mf_sum = mf_res.get("summary", {})
    mf_invested = mf_sum.get("total_investment", 0.0)
    mf_cur_val = mf_sum.get("current_value", 0.0)
    mf_pnl = mf_sum.get("total_pnl", 0.0)
    mf_pnl_pct = mf_sum.get("total_pnl_percentage", 0.0)

    # Combined Net Worth
    total_net_worth = cash_bal + eq_cur_val + mf_cur_val
    combined_invested = eq_invested + mf_invested
    combined_pnl = eq_pnl + mf_pnl
    combined_pnl_pct = (combined_pnl / combined_invested * 100) if combined_invested > 0 else 0.0

    # Top Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Total Demat Net Worth",
        f"₹{total_net_worth:,.2f}",
        delta=f"{combined_pnl_pct:+.2f}% Overall P&L" if combined_invested > 0 else None,
    )
    m2.metric(
        "Equities & ETFs Value",
        f"₹{eq_cur_val:,.2f}",
        delta=f"{eq_pnl_pct:+.2f}% (₹{eq_pnl:,.2f})" if eq_invested > 0 else None,
    )
    m3.metric(
        "Mutual Funds Value",
        f"₹{mf_cur_val:,.2f}",
        delta=f"{mf_pnl_pct:+.2f}% (₹{mf_pnl:,.2f})" if mf_invested > 0 else None,
    )
    m4.metric("Available Cash Margin", f"₹{cash_bal:,.2f}")

    st.divider()

    # Asset Sections Tabs
    tab_eq, tab_mf, tab_pos = st.tabs([
        f"📈 Equities & ETFs ({len(holdings_res.get('holdings', []))})",
        f"🌱 Mutual Funds ({len(mf_res.get('mf_holdings', []))})",
        "⚡ Positions & Margins",
    ])

    # TAB 1: Equities & ETFs
    with tab_eq:
        raw_holdings = holdings_res.get("holdings", [])
        if raw_holdings:
            df_holdings = pd.DataFrame(raw_holdings)
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
            st.info("No long-term equity/ETF holdings found in this Demat account.")

    # TAB 2: Mutual Funds (Zerodha Coin)
    with tab_mf:
        raw_mf = mf_res.get("mf_holdings", [])
        if raw_mf:
            df_mf = pd.DataFrame(raw_mf)
            mf_display_cols = {
                "fund": "Scheme / Fund Name",
                "folio": "Folio Number",
                "quantity": "Units Held",
                "average_price": "Avg NAV (₹)",
                "last_price": "Current NAV (₹)",
                "invested_amount": "Invested Amount (₹)",
                "current_value": "Current Value (₹)",
                "pnl": "Returns P&L (₹)",
                "pnl_percentage": "Returns %",
                "last_price_date": "NAV Date",
            }
            cols_present = [c for c in mf_display_cols.keys() if c in df_mf.columns]
            df_mf_display = df_mf[cols_present].rename(columns=mf_display_cols)

            st.dataframe(
                df_mf_display.style.format({
                    "Units Held": "{:,.3f}",
                    "Avg NAV (₹)": "₹{:,.2f}",
                    "Current NAV (₹)": "₹{:,.2f}",
                    "Invested Amount (₹)": "₹{:,.2f}",
                    "Current Value (₹)": "₹{:,.2f}",
                    "Returns P&L (₹)": "₹{:,.2f}",
                    "Returns %": "{:+.2f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No Zerodha Coin Mutual Fund holdings found in this account.")

    # TAB 3: Positions & Margins
    with tab_pos:
        c_pos, c_mar = st.columns(2)
        with c_pos:
            st.markdown("#### ⚡ Open Day / F&O Positions")
            open_pos = positions_res.get("open_positions", [])
            if open_pos:
                st.dataframe(pd.DataFrame(open_pos), use_container_width=True, hide_index=True)
            else:
                st.caption("No open intraday (MIS) or derivative (F&O) positions.")

        with c_mar:
            st.markdown("#### 💼 Account Margin Breakdown")
            eq_details = margins_res.get("summary", {}).get("equity", {})
            st.write(f"• **Available Cash Balance:** ₹{cash_bal:,.2f}")
            st.write(f"• **Live Balance:** ₹{eq_details.get('live_balance', 0.0):,.2f}")
            st.write(f"• **Used Margin (Debits):** ₹{eq_details.get('used_margin', 0.0):,.2f}")
            st.write(f"• **SPAN Margin:** ₹{eq_details.get('span_margin', 0.0):,.2f}")
            st.write(f"• **Exposure Margin:** ₹{eq_details.get('exposure_margin', 0.0):,.2f}")
            st.write(f"• **Collateral Value:** ₹{eq_details.get('collateral', 0.0):,.2f}")
