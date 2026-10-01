"""
Zerodha Kite Authentication UI View
Allows one-click daily session generation directly from the dashboard screen.
Supports automatic OAuth redirect handling and manual token submission.
"""

import webbrowser
from kiteconnect import KiteConnect
import kiteconnect.exceptions as kite_exceptions
import streamlit as st

from authenticate import parse_request_token
from config import get_access_token, get_config, set_access_token


def check_auth_status():
    """Verify if the current access token is valid."""
    api_key = get_config("KITE_API_KEY")
    token = get_access_token()

    if not api_key:
        return False, "KITE_API_KEY not configured", None
    if not token:
        return False, "KITE_ACCESS_TOKEN missing (Daily login required)", None

    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(token)
        profile = kite.profile()
        return True, "Connected & Verified", profile
    except kite_exceptions.TokenException:
        return False, "Session Expired (Run daily authentication below)", None
    except Exception as exc:
        return False, f"Connection Check Error: {exc}", None


def auto_handle_oauth_redirect(api_key: str, api_secret: str):
    """Automatically process request_token if redirected to this web app."""
    params = st.query_params
    if "request_token" in params and api_key and api_secret:
        req_token = params.get("request_token")
        try:
            kite = KiteConnect(api_key=api_key)
            session_data = kite.generate_session(request_token=req_token, api_secret=api_secret)
            new_token = session_data.get("access_token")
            if new_token:
                set_access_token(new_token)
                st.query_params.clear()
                st.balloons()
                st.success(f"🎉 Auto-authenticated as {session_data.get('user_name')} via OAuth redirect!")
                st.rerun()
        except Exception as exc:
            st.error(f"Automatic OAuth exchange failed: {exc}")
            st.query_params.clear()


def render_auth_view():
    """Render the one-click authentication screen."""
    st.subheader("🔑 Zerodha Kite Daily Authentication")
    st.markdown(
        "Zerodha enforces SEBI security rules where your access token expires daily at 6:00 AM IST. "
        "Use this screen each morning to refresh your session with one click without opening a terminal."
    )

    api_key = get_config("KITE_API_KEY")
    api_secret = get_config("KITE_API_SECRET")

    # Check for automatic OAuth redirect
    auto_handle_oauth_redirect(api_key, api_secret)

    # Connection Status Banner
    is_valid, msg, profile = check_auth_status()
    if is_valid and profile:
        st.success(
            f"✅ **Connected to Zerodha:** {profile.get('user_name', 'Trader')} "
            f"(`{profile.get('user_id', 'N/A')}`) — Account Active"
        )
    else:
        st.warning(f"⚠️ **Zerodha Status:** {msg}")

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Step 1: Open Login Authorization")
        st.info(
            "Click the button below to open Zerodha Kite in your browser. "
            "Enter your password and 2FA TOTP."
        )

        if not api_key:
            st.error("KITE_API_KEY is not configured in Secrets / .env.")
            return

        kite = KiteConnect(api_key=api_key)
        login_url = kite.login_url()

        if st.button("🚀 Open Zerodha 2FA Login in Browser", use_container_width=True, type="primary"):
            webbrowser.open(login_url)
            st.toast("Opened login URL in browser!", icon="🌐")

        st.caption(f"[Direct Link if pop-up blocked]({login_url})")

    with col2:
        st.markdown("### Step 2: Complete Session Generation")
        st.info(
            "After authorization, your browser redirects to a URL with `?request_token=...`. "
            "Copy that URL (or just the token) and paste it below."
        )

        user_input = st.text_input(
            "Paste Redirected URL or Request Token:",
            placeholder="http://127.0.0.1:8000/?request_token=XXXXXX&action=login",
        )

        if st.button("⚡ Generate & Save Daily Access Token", use_container_width=True):
            if not user_input.strip():
                st.error("Please paste the redirected URL or request token first.")
            else:
                token = parse_request_token(user_input)
                try:
                    with st.spinner("Exchanging token with Zerodha Kite..."):
                        session_data = kite.generate_session(request_token=token, api_secret=api_secret)
                        new_access_token = session_data.get("access_token")

                        if new_access_token:
                            set_access_token(new_access_token)
                            st.balloons()
                            st.success(
                                f"🎉 Successfully authenticated as **{session_data.get('user_name')}** "
                                f"(`{session_data.get('user_id')}`)! Session active."
                            )
                            st.rerun()
                        else:
                            st.error("Could not extract access_token from response.")
                except Exception as exc:
                    st.error(f"Authentication Failed: {exc}")
