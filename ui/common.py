"""
Common UI components and navigation helpers for Antigravity Kite & IPO Terminal.
"""

import streamlit as st


def render_back_to_top():
    """Render a clean, styled 'Back to Top' navigation button at the bottom of views."""
    st.markdown(
        """
        <div style="text-align: center; margin: 35px 0 20px 0;">
            <a href="#top-of-page" target="_self" class="back-to-top-inline">
                ⬆️ Back to Top
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
