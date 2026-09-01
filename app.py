"""Streamlit entry point for the family MCU watch tracker."""

from datetime import date

import streamlit as st

from data.movies import MOVIES
from ui.theme import apply_theme


DOOMSDAY_DATE = date(2026, 12, 18)


def days_until_doomsday() -> int:
    """Return the number of days remaining until Avengers: Doomsday."""
    return max((DOOMSDAY_DATE - date.today()).days, 0)


def render_dashboard() -> None:
    """Render the initial dashboard shell."""
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
                <div class="metric-value">{len(MOVIES)} titles</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-label">Family Status</div>
                <div class="metric-value">Coming next</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Mission roadmap")
    st.write(
        "The first milestone establishes the visual shell. Account creation, "
        "personal checklists, family tracking, and shared progress will be "
        "added in the next milestones."
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


def main() -> None:
    """Configure and run the Streamlit application."""
    st.set_page_config(
        page_title="Road to Doomsday",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    with st.sidebar:
        st.title("Road to Doomsday")
        st.caption("Family MCU Watch Tracker")
        st.divider()
        st.write("🏠 Dashboard")
        st.write("🎞️ My Movies")
        st.write("👥 Family Tracker")
        st.write("📚 Movie Library")
        st.divider()
        st.caption("Authentication will be added in Milestone 2.")

    render_dashboard()


if __name__ == "__main__":
    main()
