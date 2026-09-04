"""Streamlit authentication interface."""

import streamlit as st

from auth.service import (
    authenticate_user,
    invite_code_required,
    register_user,
)
from database.users import get_user_by_id


def initialize_auth_state() -> None:
    """Initialize authentication-related Streamlit session values."""
    defaults = {
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "is_admin": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_logged_in() -> bool:
    """Return whether a user is currently authenticated."""
    return st.session_state.get("user_id") is not None


def set_authenticated_user(user) -> None:
    """Store an authenticated database user in session state."""
    user_id, name, email, _, _, is_admin = user
    st.session_state.user_id = user_id
    st.session_state.user_name = name
    st.session_state.user_email = email
    st.session_state.is_admin = bool(is_admin)


def logout() -> None:
    """Clear the current authentication session."""
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.is_admin = False


def refresh_authenticated_user() -> bool:
    """Refresh the logged-in account from the database and enforce activity."""
    user_id = st.session_state.get("user_id")
    if user_id is None:
        return False

    user = get_user_by_id(int(user_id))
    if user is None or not bool(user[4]):
        logout()
        return False

    set_authenticated_user(user)
    return True


def render_login_form() -> None:
    """Render the login form."""
    with st.form("login_form"):
        email = st.text_input("Email", autocomplete="email")
        password = st.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "Enter the Initiative",
            use_container_width=True,
        )

    if submitted:
        user = authenticate_user(email, password)
        if user is None:
            st.error("Email or password is incorrect.")
            return

        set_authenticated_user(user)
        st.rerun()

    with st.expander("Forgot password?"):
        st.write(
            "Ask your family administrator to reset your password from "
            "**Administration → Family**. Your movie progress will not be affected."
        )


def render_signup_form() -> None:
    """Render the account creation form."""
    requires_invite = invite_code_required()

    with st.form("signup_form"):
        name = st.text_input("Display name")
        email = st.text_input("Email", autocomplete="email")
        password = st.text_input(
            "Password",
            type="password",
            autocomplete="new-password",
        )
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            autocomplete="new-password",
        )
        invite_code = ""
        if requires_invite:
            invite_code = st.text_input(
                "Family invite code",
                type="password",
                help="Ask your family administrator for the private signup code.",
            )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True,
        )

    if submitted:
        user, errors = register_user(
            name,
            email,
            password,
            confirm_password,
            invite_code,
        )
        if errors:
            for error in errors:
                st.error(error)
            return

        set_authenticated_user(user)
        st.success("Account created. Welcome to the initiative.")
        st.rerun()


def render_auth_page() -> None:
    """Render login and signup tabs for signed-out visitors."""
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Watch Initiative</div>
            <h1>Assemble Your Watchlist</h1>
            <p>
                Sign in to track your progress toward Avengers: Doomsday,
                or create an account to join the family challenge.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])
    with login_tab:
        render_login_form()
    with signup_tab:
        render_signup_form()
