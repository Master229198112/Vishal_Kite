"""
AI Research & Video Intelligence View
Generates institutional research reports using Google Gemini and curates YouTube video reviews.
"""

import streamlit as st
import ipo_mcp


def render_ai_research_view():
    """Render the AI synthesis and media intelligence tab."""
    st.subheader("🤖 AI IPO Research & Analyst Intelligence")
    st.markdown(
        "Synthesizes live GMP, subscription demand, issue structure, and analyst video commentary into an "
        "institutional investment research memo powered by **Google Gemini**."
    )

    # 1. Fetch IPO list for dropdown
    ipos_res = ipo_mcp.get_upcoming_ipos()
    ipo_names = [i["company_name"] for i in ipos_res.get("ipos", [])] if ipos_res.get("status") == "success" else []

    col_select, col_lang, col_btn = st.columns([2.5, 1.5, 1])
    with col_select:
        selected_ipo = st.selectbox(
            "Select an IPO to Analyze:",
            options=ipo_names or ["Acme India Industries", "TNA Solutions", "Tata Technologies"],
        )
    with col_lang:
        languages = [
            "English",
            "Hindi (हिंदी)",
            "Marathi (मराठी)",
            "Gujarati (ગુજરાતી)",
            "Telugu (తెలుగు)",
            "Tamil (தமிழ்)",
            "Bengali (বাংলা)",
            "Kannada (ಕನ್ನಡ)",
            "Malayalam (മലയാളം)",
            "Punjabi (ਪੰਜਾਬੀ)",
        ]
        selected_lang = st.selectbox(
            "Analysis Language:",
            options=languages,
            index=0,
            help="Choose the language for the AI investment research report",
        )
    with col_btn:
        st.write("")
        st.write("")
        analyze_btn = st.button("✨ Run Gemini Analysis", type="primary", use_container_width=True)

    # 2. Only execute Gemini API call when the button is explicitly clicked
    if analyze_btn:
        with st.spinner(f"Analyzing {selected_ipo} in {selected_lang} via Google Gemini & YouTube intelligence..."):
            res = ipo_mcp.get_ipo_analysis_summary(selected_ipo, language=selected_lang)
            st.session_state["active_analysis_result"] = res
            st.session_state["active_analysis_target"] = selected_ipo
            st.session_state["active_analysis_lang"] = selected_lang

    # 3. Render analysis results from session state if available
    res = st.session_state.get("active_analysis_result")
    if res:
        if res.get("status") == "error":
            st.error(f"Analysis failed: {res.get('message')}")
            return

        scorecard = res.get("scorecard", {})
        overall_score = scorecard.get("overall_score", 0.0)
        verdict = scorecard.get("quantitative_verdict", "N/A")
        gain_pot = scorecard.get("listing_gain_potential", "N/A")
        risk = scorecard.get("risk_level", "N/A")
        ai_powered_by = res.get("ai_powered_by", "Google Gemini")

        st.divider()

        # Scorecard Row - Custom Responsive Cards to avoid truncation
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(
                f"""
                <div style="background-color: #1e222d; padding: 14px 16px; border-radius: 8px; border: 1px solid #2e3342; height: 100%;">
                    <div style="color: #90caf9; font-size: 0.82rem; font-weight: 500; text-transform: uppercase;">Overall Score</div>
                    <div style="font-size: 1.6rem; font-weight: bold; margin-top: 4px; color: #ffffff;">{overall_score} <span style="font-size: 1rem; color: #78909c;">/ 10</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with sc2:
            st.markdown(
                f"""
                <div style="background-color: #1e222d; padding: 14px 16px; border-radius: 8px; border: 1px solid #2e3342; height: 100%;">
                    <div style="color: #90caf9; font-size: 0.82rem; font-weight: 500; text-transform: uppercase;">Listing Gain Potential</div>
                    <div style="font-size: 1.22rem; font-weight: bold; margin-top: 4px; color: #00e676; line-height: 1.3;">{gain_pot}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with sc3:
            st.markdown(
                f"""
                <div style="background-color: #1e222d; padding: 14px 16px; border-radius: 8px; border: 1px solid #2e3342; height: 100%;">
                    <div style="color: #90caf9; font-size: 0.82rem; font-weight: 500; text-transform: uppercase;">Risk Level</div>
                    <div style="font-size: 1.35rem; font-weight: bold; margin-top: 4px; color: #ffffff;">{risk}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with sc4:
            st.markdown(
                f"""
                <div style="background-color: #1e222d; padding: 14px 16px; border-radius: 8px; border: 1px solid #2e3342; height: 100%;">
                    <div style="color: #90caf9; font-size: 0.82rem; font-weight: 500; text-transform: uppercase;">AI Engine</div>
                    <div style="font-size: 1.05rem; font-weight: 600; margin-top: 6px; color: #81c784;">Google Gemini AI</div>
                    <div style="font-size: 0.72rem; color: #78909c;">Automated Intelligence</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.progress(min(overall_score / 10.0, 1.0))
        st.info(f"**Verdict:** {verdict}")

        # Regulatory & Self-Research Safety Disclaimer
        st.warning(
            "⚠️ **Investor Due Diligence & Self-Research Disclaimer:**\n"
            "This AI synthesis, quantitative score, and listing gain estimate are generated algorithmically by Google Gemini for informational and educational analysis only. "
            "**They do NOT constitute investment advice, buy/sell recommendations, or a financial solicitation.** "
            "IPOs (especially SME issues) carry significant market risks, including listing day volatility, price swings, and potential loss of capital. "
            "Always conduct your own independent due diligence, examine the company's Red Herring Prospectus (RHP), and consult a certified SEBI-registered financial advisor before applying."
        )

        # AI Narrative Memo
        target_name = st.session_state.get("active_analysis_target", "")
        target_lang = st.session_state.get("active_analysis_lang", "English")
        st.markdown(f"### 📋 Executive Research Memo: {target_name} ({target_lang})")
        st.markdown(res.get("ai_narrative_report", "No report available."))

        st.divider()

        # Curated Analyst Videos
        st.markdown("### 🎥 Curated Analyst YouTube Reviews & Coverage")
        videos = res.get("top_analyst_videos", [])
        if videos:
            v_cols = st.columns(len(videos))
            for i, vid in enumerate(videos):
                with v_cols[i]:
                    st.markdown(
                        f"""
                        <div style="padding: 12px; border: 1px solid #333; border-radius: 8px; height: 100%;">
                            <b>{vid.get('channel', 'Analyst')}</b><br>
                            <small>{vid.get('title', '')[:70]}...</small><br><br>
                            <span>👁️ {vid.get('views', '')}</span> | <span>📅 {vid.get('published', '')}</span><br><br>
                            <a href="{vid.get('url')}" target="_blank" style="text-decoration:none; color:#ff4b4b; font-weight:bold;">
                                ▶ Watch on YouTube
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No video reviews found.")
