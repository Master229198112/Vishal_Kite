"""
Configuration and Secrets Helper
Supports local .env loading as well as Streamlit Cloud (st.secrets & st.session_state).
"""

import os
from dotenv import find_dotenv, load_dotenv


def get_config(key: str, default: str = "") -> str:
    """
    Retrieve configuration value from Streamlit secrets (on cloud)
    or os.environ / .env (locally).
    """
    val = ""
    # 1. Try Streamlit secrets (Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = str(st.secrets[key])
    except Exception:
        pass

    # 2. Try os.environ / .env (Local deployment)
    if not val:
        load_dotenv(find_dotenv(), override=False)
        val = os.getenv(key, default)

    return str(val).strip()


def get_access_token() -> str:
    """
    Get the active Kite access token from Streamlit session state,
    environment variables, or .env.
    """
    try:
        import streamlit as st
        if "KITE_ACCESS_TOKEN" in st.session_state and st.session_state["KITE_ACCESS_TOKEN"]:
            return str(st.session_state["KITE_ACCESS_TOKEN"]).strip()
    except Exception:
        pass

    return get_config("KITE_ACCESS_TOKEN", "")


def set_access_token(token: str):
    """
    Store active access token into memory, session state, and .env file.
    """
    token_str = str(token).strip()
    os.environ["KITE_ACCESS_TOKEN"] = token_str

    try:
        import streamlit as st
        st.session_state["KITE_ACCESS_TOKEN"] = token_str
    except Exception:
        pass

    try:
        from dotenv import find_dotenv, set_key
        env_path = find_dotenv() or os.path.join(os.getcwd(), ".env")
        set_key(env_path, "KITE_ACCESS_TOKEN", token_str)
    except Exception:
        pass
