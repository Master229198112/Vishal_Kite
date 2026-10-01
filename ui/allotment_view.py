"""
IPO Allotment Checker View
Provides 1-click status checking across all major Indian IPO registrars
(Link Intime, KFintech, Bigshare, Skyline, Maashitla, Cameo, BSE).
"""

import streamlit as st
import allotment_checker
import ipo_mcp
from ui.common import render_back_to_top


def render_allotment_view():
    """Render the 1-click IPO allotment query hub and lifecycle tracker."""
    st.subheader("🔍 1-Click IPO Allotment Status Checker")
    st.caption("Instantly check share allotment across all official SEBI registrars & exchanges.")

    # 1. Fetch IPOs for selection
    with st.spinner("Loading tracked IPO list..."):
        data = ipo_mcp.get_upcoming_ipos()

    ipos = data.get("ipos", [])
    recent_closed = [i for i in ipos if i.get("status") in ["Closed", "Open"]]
    ipo_options = [i.get("company_name") for i in recent_closed] or ["Acme India Industries", "TNA Solutions"]

    c_sel, c_pan = st.columns([1.5, 1])
    with c_sel:
        selected_ipo_name = st.selectbox("Select IPO to Verify:", options=ipo_options)
    with c_pan:
        user_pan = st.text_input("Your PAN Number (Optional):", placeholder="e.g. ABCDE1234F").strip().upper()

    selected_ipo = next((i for i in ipos if i.get("company_name") == selected_ipo_name), {})

    if user_pan:
        is_valid = allotment_checker.validate_pan(user_pan)
        if is_valid:
            st.success(f"✅ Valid PAN: `{user_pan[:2]}*****{user_pan[-2:]}` (Ready for registrar search)")
        else:
            st.warning("⚠️ Please verify PAN format (5 letters, 4 numbers, 1 letter, e.g. ABCDE1234F)")

    st.divider()

    # 2. SEBI T+3 Settlement Timeline
    st.markdown("### ⏱️ IPO Allotment & Settlement Milestones (SEBI T+3)")
    timeline = allotment_checker.get_allotment_timeline(
        ipo_name=selected_ipo_name,
        open_date=selected_ipo.get("open_date", "Day 1"),
        close_date=selected_ipo.get("close_date", "Day 3"),
    )

    t_cols = st.columns(5)
    for idx, step in enumerate(timeline):
        with t_cols[idx]:
            st.markdown(
                f"""
                <div style="background-color: #1e222d; padding: 12px; border-radius: 8px; border: 1px solid #2e3342; height: 100%;">
                    <div style="font-size: 1.4em;">{step['icon']}</div>
                    <b>{step['step']}</b><br>
                    <small style="color: #90caf9;">{step['status']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # 3. Direct Registrar Portal for Selected IPO
    assigned_reg = allotment_checker.get_assigned_registrar_for_ipo(
        ipo_name=selected_ipo_name,
        detail_url=selected_ipo.get("detail_url"),
    )

    st.markdown(f"### 🏢 Designated Official Registrar for **{selected_ipo_name}**")
    st.caption(f"Allotment status for this specific issue is officially hosted on **{assigned_reg['name']}**:")

    c_reg, c_guide = st.columns([1.2, 1], gap="medium")
    with c_reg:
        st.markdown(
            f"""
            <div style="background-color: #161b26; padding: 22px; border-radius: 10px; border: 2px solid #00e676;">
                <div style="color: #00e676; font-size: 0.85rem; font-weight: bold; text-transform: uppercase;">
                    🎯 Official Registrar for {selected_ipo_name}
                </div>
                <h3 style="margin: 8px 0 4px 0; color: #ffffff;">{assigned_reg['name']}</h3>
                <p style="color: #b0bec5; font-size: 0.95rem; margin-bottom: 12px;">{assigned_reg['description']}</p>
                <div style="background-color: #0e1117; padding: 10px 14px; border-radius: 6px; margin-bottom: 16px;">
                    <small><b>Verify Using:</b> {', '.join(assigned_reg['supported_searches'])}</small>
                </div>
                <a href="{assigned_reg['url']}" target="_blank" style="display: block; text-align: center; background-color: #00e676; color: #000000; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; font-size: 1.05rem;">
                    🚀 Open {assigned_reg['name'].split()[0]} Allotment Portal (1-Click)
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_guide:
        st.markdown(
            f"""
            <div style="background-color: #1e222d; padding: 18px; border-radius: 10px; border: 1px solid #2e3342; height: 100%;">
                <h4 style="color: #64b5f6; margin-top: 0;">📋 Step-by-Step Instructions</h4>
                <ol style="color: #cfd8dc; padding-left: 20px; font-size: 0.9rem; line-height: 1.6;">
                    <li>Click the green button to open <b>{assigned_reg['name']}</b>.</li>
                    <li>Select <b>{selected_ipo_name}</b> from the "Company Selection" dropdown.</li>
                    <li>Choose <b>PAN Number</b> (or Application No / DP Client ID).</li>
                    <li>Enter your details and click <b>Submit / Search</b>.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Optional alternative access
    with st.expander("🌐 Need BSE / Alternative Registrar Portals?"):
        all_regs = allotment_checker.get_all_registrars()
        r_cols = st.columns(3)
        for idx, (r_key, r_info) in enumerate(all_regs.items()):
            with r_cols[idx % 3]:
                st.markdown(
                    f"**{r_info['name']}**<br><a href='{r_info['url']}' target='_blank'>Visit Portal ↗</a>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # 4. Pro-Tips Accordion
    with st.expander("💡 3 Instant Ways to Know Your Allotment Before Portals Update"):
        st.markdown(
            """
            1. **Bank ASBA SMS / Email (Fastest)**: If allotted, your bank sends an SMS: *"Debit of ₹XX,XXX for IPO Application"*. If unallotted, you receive: *"ASBA lien removed / Amount unblocked"*.
            2. **CDSL / NSDL Demat Credit Notification**: On T+2 day, depository sends an SMS/Email: *"Credit of XX shares of [Company] into your Demat Account"*.
            3. **Zerodha Kite Holdings**: Check the **📊 Portfolio & Demat** tab on listing day morning at 8:30 AM — allotted shares will automatically appear under your holdings!
            """
        )

    render_back_to_top()
