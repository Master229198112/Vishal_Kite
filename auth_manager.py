"""
Authentication & User Management Module
Implements secure bcrypt password hashing, session tracking, and user profile management.
"""

import json
import os
from typing import Any, Dict, Optional, Tuple
import bcrypt

AUTH_STORE_FILE = os.path.join(os.path.dirname(__file__), ".auth_users.json")


def _get_default_users() -> Dict[str, Any]:
    """Generate default initial admin user if store does not exist."""
    # Default initial password is 'admin123'
    default_pass = "admin123"
    hashed = bcrypt.hashpw(default_pass.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return {
        "vishal": {
            "username": "vishal",
            "full_name": "Vishal Kumar Sharma",
            "email": "vishalkumar.sharma37@gmail.com",
            "kite_client_id": "DF2893",
            "password_hash": hashed,
            "role": "owner",
        }
    }


def _load_users() -> Dict[str, Any]:
    """Load users from .auth_users.json or fallback to defaults."""
    if os.path.exists(AUTH_STORE_FILE):
        try:
            with open(AUTH_STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    users = _get_default_users()
    _save_users(users)
    return users


def _save_users(users: Dict[str, Any]) -> bool:
    """Save user records to .auth_users.json."""
    try:
        with open(AUTH_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        return True
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Verify credentials and return user object."""
    users = _load_users()
    u_key = username.strip().lower()

    if u_key not in users:
        return False, "Invalid username or password.", None

    user = users[u_key]
    if check_password(password, user.get("password_hash", "")):
        safe_user = {k: v for k, v in user.items() if k != "password_hash"}
        return True, "Login successful.", safe_user

    return False, "Invalid username or password.", None


def change_user_password(username: str, current_pass: str, new_pass: str) -> Tuple[bool, str]:
    """Change a user's password after validating current password."""
    if len(new_pass.strip()) < 6:
        return False, "New password must be at least 6 characters long."

    users = _load_users()
    u_key = username.strip().lower()

    if u_key not in users:
        return False, "User not found."

    user = users[u_key]
    if not check_password(current_pass, user.get("password_hash", "")):
        return False, "Current password is incorrect."

    user["password_hash"] = hash_password(new_pass.strip())
    users[u_key] = user
    _save_users(users)
    return True, "Password updated successfully!"


def is_authenticated() -> bool:
    """Check if the current Streamlit session is logged in."""
    try:
        import streamlit as st
        return bool(st.session_state.get("authenticated", False))
    except Exception:
        return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the currently logged-in user profile from session state."""
    try:
        import streamlit as st
        return st.session_state.get("user", None)
    except Exception:
        return None


def login_session(user_data: Dict[str, Any]):
    """Set authentication flags in Streamlit session state."""
    try:
        import streamlit as st
        st.session_state["authenticated"] = True
        st.session_state["user"] = user_data
    except Exception:
        pass


def logout_session():
    """Clear authentication flags from Streamlit session state."""
    try:
        import streamlit as st
        st.session_state["authenticated"] = False
        st.session_state["user"] = None
    except Exception:
        pass


if __name__ == "__main__":
    print("Testing auth_manager...")
    ok, msg, u = authenticate_user("vishal", "admin123")
    print(f"Login test: ok={ok}, msg='{msg}', user={u.get('username') if u else None}")
    ok_bad, msg_bad, _ = authenticate_user("vishal", "wrongpassword")
    print(f"Wrong pass test: ok={ok_bad}, msg='{msg_bad}'")
