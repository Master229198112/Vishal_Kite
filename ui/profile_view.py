"""
User Profile & Security View
Displays authenticated user information, Demat account linkage,
and secure bcrypt password management.
"""

import streamlit as st
import auth_manager
from ui.common import render_back_to_top


def render_profile_view():
    """Render user profile and change password management view."""
    st.subheader("👤 User Profile & Security Settings")

    if not auth_manager.is_authenticated():
        st.warning("🔒 You are not currently logged in.")
        st.info("Please log in using the sidebar or login form to manage your profile.")
        return

    user = auth_manager.get_current_user() or {}
    username = user.get("username", "vishal")
    full_name = user.get("full_name", "Vishal Kumar Sharma")
    email = user.get("email", "vishalkumar.sharma37@gmail.com")
    kite_id = user.get("kite_client_id", "DF2893")
    role = user.get("role", "Owner")

    col_info, col_pwd = st.columns([1, 1], gap="large")

    with col_info:
        st.markdown("### 📋 Account Details")
        st.markdown(
            f"""
            <div style="background-color: #1e222d; padding: 20px; border-radius: 8px; border: 1px solid #2e3342;">
                <p><strong>Full Name:</strong> {full_name}</p>
                <p><strong>Username:</strong> <code>{username}</code></p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Zerodha Client ID:</strong> <code>{kite_id}</code></p>
                <p><strong>Role:</strong> <span style="background-color: #1b5e20; color: #a5d6a7; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{role.upper()}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🛡️ Security & Privacy Architecture")
        st.info(
            "• **Password Storage:** Salted SHA/bcrypt hash (`$2b$12$...`), never saved in plain text.\n"
            "• **Role Isolation:** Private Demat, Mutual Funds & Kite Auth are strictly locked.\n"
            "• **Guest Access:** External visitors can only view public IPO GMP & AI tools.\n"
            "• **Session Security:** In-memory authenticated session state with instant logout."
        )

        if st.button("🚪 Sign Out", type="secondary", use_container_width=True):
            auth_manager.logout_session()
            st.success("Signed out successfully.")
            st.rerun()

    with col_pwd:
        st.markdown("### 🔐 Change Password")
        st.caption("Update your access password. Passwords are encrypted with bcrypt.")

        with st.form("change_password_form", clear_on_submit=True):
            current_pwd = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter current password",
            )
            new_pwd = st.text_input(
                "New Password",
                type="password",
                placeholder="Minimum 6 characters",
            )
            confirm_pwd = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter new password",
            )

            submit_btn = st.form_submit_button("Update Password", type="primary", use_container_width=True)

            if submit_btn:
                if not current_pwd or not new_pwd:
                    st.error("Please fill in all password fields.")
                elif new_pwd != confirm_pwd:
                    st.error("New password and confirm password do not match.")
                elif len(new_pwd.strip()) < 6:
                    st.error("New password must be at least 6 characters long.")
                else:
                    success, msg = auth_manager.change_user_password(
                        username=username,
                        current_pass=current_pwd,
                        new_pass=new_pwd,
                    )
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    render_back_to_top()
