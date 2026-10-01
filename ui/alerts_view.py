"""
Alerts & Morning Briefing View
Provides controls to dispatch automated daily morning briefings
via Telegram Bot and 1-click WhatsApp sharing.
"""

import streamlit as st
from config import get_config
import notifications
from ui.common import render_back_to_top


def render_alerts_view():
    """Render the Telegram / WhatsApp notification briefing hub."""
    st.subheader("📢 Morning Market & IPO Briefing Bot")
    st.caption("Receive automated daily morning alerts with top IPO GMP shifts and your Demat net worth.")

    # 1. Generate Live Preview
    briefing_text = notifications.generate_morning_briefing(include_demat=True)

    col_preview, col_action = st.columns([1.2, 1], gap="large")

    with col_preview:
        st.markdown("### 📝 Today's Briefing Preview")
        st.text_area(
            "Message Preview",
            value=briefing_text,
            height=340,
            disabled=True,
            label_visibility="collapsed",
        )

        # 1-Click WhatsApp Share Button
        wa_url = notifications.get_whatsapp_share_url(briefing_text)
        st.markdown(
            f"""
            <a href="{wa_url}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: #ffffff; padding: 12px; border-radius: 8px; font-weight: bold; text-decoration: none; margin-top: 10px;">
                💬 Share Briefing via WhatsApp (1-Click)
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col_action:
        st.markdown("### ✈️ Telegram Bot Delivery")
        st.info("Deliver this briefing directly to your Telegram phone or private group every morning.")

        saved_token = get_config("TELEGRAM_BOT_TOKEN", "")
        saved_chat_id = get_config("TELEGRAM_CHAT_ID", "")

        with st.form("telegram_send_form"):
            bot_token = st.text_input(
                "Telegram Bot Token:",
                value=saved_token,
                type="password",
                placeholder="e.g. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
            )
            chat_id = st.text_input(
                "Telegram Chat ID:",
                value=saved_chat_id,
                placeholder="e.g. 987654321",
            )
            send_btn = st.form_submit_button("🚀 Send Test Briefing to Telegram", type="primary", use_container_width=True)

            if send_btn:
                if not bot_token or not chat_id:
                    st.error("Please provide both Telegram Bot Token and Chat ID.")
                else:
                    with st.spinner("Dispatching Telegram notification..."):
                        ok, msg = notifications.send_telegram_briefing(
                            message=briefing_text,
                            bot_token=bot_token,
                            chat_id=chat_id,
                        )
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("ℹ️ How to Set Up Your Free Telegram Bot (2 Minutes)"):
            st.markdown(
                """
                1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
                2. Send `/newbot`, name your bot (e.g. *VishalKiteBot*), and copy the HTTP API **Bot Token**.
                3. Search for **[@userinfobot](https://t.me/userinfobot)** and press Start to get your **Chat ID** (Numbers).
                4. Start a chat with your new bot and send `/start`.
                5. Paste the Token and Chat ID above, or save in `.env` / Streamlit Secrets:
                   ```
                   TELEGRAM_BOT_TOKEN="your_token_here"
                   TELEGRAM_CHAT_ID="your_chat_id_here"
                   ```
                """
            )

    render_back_to_top()
