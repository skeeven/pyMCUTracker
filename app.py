"""Streamlit entry point for the family MCU watch tracker."""

from datetime import date

import streamlit as st

from auth.ui import (
    initialize_auth_state,
    is_logged_in,
    logout,
    render_auth_page,
)
from data.movies import MOVIES
from database.user_movies import get_watched_count
from ui.theme import apply_theme
from views.my_movies import render_my_movies

DOOMSDAY_DATE = date(2026, 12, 18)


def days_until_doomsday() -> int:
    """Return the number of days remaining until Avengers: Doomsday."""
    return max((DOOMSDAY_DATE - date.today()).days, 0)


def render_dashboard() -> None:
    """Render the authenticated dashboard."""
    watched_count = get_watched_count(st.session_state.user_id)
    total_movies = len(MOVIES)
    progress = watched_count / total_movies if total_movies else 0.0

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Watch Initiative</div>
            <h1>Road to Doomsday</h1>
            <p>
                Track every movie, compare family progress, and get everyone
                ready for the next Avengers event.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Countdown</div>
                <div class="metric-value">{days_until_doomsday()} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Movie Challenge</div>
                <div class="metric-value">{total_movies} titles</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Your Progress</div>
                <div class="metric-value">{watched_count} / {total_movies}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.progress(progress)
    st.caption(f"{progress:.0%} of your Road to Doomsday watchlist complete")

    st.subheader(f"Welcome, {st.session_state.user_name}")
    st.write(
        "Open **My Movies** from the sidebar to update your personal "
        "watchlist. Your checked movies are saved to SQLiteCloud."
    )

    for phase in range(1, 7):
        count = sum(1 for movie in MOVIES if movie[3] == phase)
        st.markdown(
            f"""
            <div class="phase-card">
                <strong>Phase {phase}</strong><br>
                {count} movies in the tracker
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_placeholder(title: str, message: str) -> None:
    """Render a placeholder for a future application section."""
    st.markdown(
        f"""
        <section class="hero">
            <div class="eyebrow">Coming Soon</div>
            <h1>{title}</h1>
            <p>{message}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> str:
    """Render navigation and return the selected page."""
    with st.sidebar:
        st.title("Road to Doomsday")
        st.caption("Family MCU Watch Tracker")
        st.divider()

        page = st.radio(
            "Navigation",
            options=[
                "🏠 Dashboard",
                "🎞️ My Movies",
                "👥 Family Tracker",
                "📚 Movie Library",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("SIGNED IN AS")
        st.write(f"**{st.session_state.user_name}**")
        st.caption(st.session_state.user_email)

        if st.session_state.is_admin:
            st.caption("🛡️ Administrator")

        if st.button("Log Out", use_container_width=True):
            logout()
            st.rerun()

        return page


def render_selected_page(page: str) -> None:
    """Render the page selected in the authenticated sidebar."""
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "🎞️ My Movies":
        render_my_movies(st.session_state.user_id)
    elif page == "👥 Family Tracker":
        render_placeholder(
            "Family Tracker",
            "The shared family watch matrix is the next milestone.",
        )
    else:
        render_placeholder(
            "Movie Library",
            "Movie details and browsing tools will be added after the "
            "family tracker.",
        )


def main() -> None:
    """Configure and run the Streamlit application."""
    st.set_page_config(
        page_title="Road to Doomsday",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()
    initialize_auth_state()

    if not is_logged_in():
        render_auth_page()
        return

    page = render_sidebar()
    render_selected_page(page)


if __name__ == "__main__":
    main()
