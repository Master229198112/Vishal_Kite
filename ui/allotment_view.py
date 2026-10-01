"""
IPO Allotment Checker View
Provides 1-click status checking across all major Indian IPO registrars
(Link Intime, KFintech, Bigshare, Skyline, Maashitla, Cameo, BSE).
"""

import streamlit as st
import allotment_checker
import ipo_mcp


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

    # 3. Direct Registrar Portals
    st.markdown("### 🏢 Direct Registrar Allotment Portals (1-Click)")
    st.caption("Click to launch the official registrar query portal directly in a new window:")

    registrars = allotment_checker.get_all_registrars()
    r_cols = st.columns(3)

    for idx, (r_key, r_info) in enumerate(registrars.items()):
        col = r_cols[idx % 3]
        with col:
            st.markdown(
                f"""
                <div style="background-color: #161b26; padding: 16px; border-radius: 8px; border: 1px solid #2e3342; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #64b5f6;">{r_info['name']}</h4>
                    <p style="font-size: 0.85em; color: #cfd8dc; margin: 6px 0;">{r_info['description']}</p>
                    <small><b>Supported:</b> {', '.join(r_info['supported_searches'])}</small><br><br>
                    <a href="{r_info['url']}" target="_blank" style="display: inline-block; background-color: #00e676; color: #000; padding: 8px 14px; border-radius: 6px; font-weight: bold; text-decoration: none;">
                        🚀 Open {r_info['name'].split()[0]} Portal
                    </a>
                </div>
                """,
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
