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

    if analyze_btn or "last_analyzed_ipo" in st.session_state:
        target = selected_ipo if analyze_btn else st.session_state.get("last_analyzed_ipo")
        active_lang = selected_lang if analyze_btn else st.session_state.get("last_analyzed_lang", "English")
        st.session_state["last_analyzed_ipo"] = target
        st.session_state["last_analyzed_lang"] = active_lang

        with st.spinner(f"Analyzing {target} in {active_lang} via Google Gemini & YouTube intelligence..."):
            res = ipo_mcp.get_ipo_analysis_summary(target, language=active_lang)

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

        # Scorecard Row
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Overall Score", f"{overall_score} / 10")
        sc2.metric("Listing Gain Potential", gain_pot)
        sc3.metric("Risk Level", risk)
        sc4.metric("AI Engine", ai_powered_by)

        st.progress(min(overall_score / 10.0, 1.0))
        st.info(f"**Verdict:** {verdict}")

        # AI Narrative Memo
        st.markdown("### 📋 Executive Research Memo")
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
