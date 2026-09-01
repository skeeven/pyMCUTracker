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
from database.user_movies import (
    get_family_movie_statuses,
    get_watched_count,
)
from database.users import get_active_users
from services.recommendations import (
    get_missing_member_names,
    get_next_family_movie,
    get_tonight_recommendation,
)
from ui.theme import apply_theme
from views.family_tracker import render_family_tracker
from views.movie_library import render_movie_library
from views.my_movies import render_my_movies

DOOMSDAY_DATE = date(2026, 12, 18)


def days_until_doomsday() -> int:
    """Return the number of days remaining until Avengers: Doomsday."""
    return max((DOOMSDAY_DATE - date.today()).days, 0)


def get_member_watched_count(
    user_id: int,
    statuses: dict[tuple[int, int], bool],
) -> int:
    """Return watched count for one family member from family status data."""
    return sum(
        1
        for movie_id, *_ in MOVIES
        if statuses.get((int(user_id), int(movie_id)), False)
    )


def get_family_complete_count(
    users: list[tuple],
    statuses: dict[tuple[int, int], bool],
) -> int:
    """Return the number of movies watched by every active family member."""
    if not users:
        return 0

    user_ids = [int(user[0]) for user in users]
    return sum(
        1
        for movie_id, *_ in MOVIES
        if all(
            statuses.get((user_id, int(movie_id)), False)
            for user_id in user_ids
        )
    )


def render_dashboard() -> None:
    """Render the authenticated dashboard."""
    users = list(get_active_users())
    statuses = get_family_movie_statuses()

    watched_count = get_watched_count(st.session_state.user_id)
    total_movies = len(MOVIES)
    progress = watched_count / total_movies if total_movies else 0.0
    family_complete = get_family_complete_count(users, statuses)
    family_progress = family_complete / total_movies if total_movies else 0.0
    next_movie = get_next_family_movie(users, statuses)
    tonight_pick = get_tonight_recommendation(users, statuses)

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

    col1, col2, col3, col4 = st.columns(4)
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
                <div class="metric-label">Your Progress</div>
                <div class="metric-value">{watched_count} / {total_movies}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Family Complete</div>
                <div class="metric-value">{family_complete} / {total_movies}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Family Members</div>
                <div class="metric-value">{len(users)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Your mission progress")
    st.progress(progress)
    st.caption(f"{progress:.0%} of your personal watchlist complete")

    st.subheader("Family mission progress")
    st.progress(family_progress)
    st.caption(
        f"{family_progress:.0%} of the catalog has been watched by everyone"
    )

    if users:
        st.subheader("Family progress")
        for user in users:
            user_id, name, _, _ = user
            member_count = get_member_watched_count(int(user_id), statuses)
            member_progress = member_count / total_movies if total_movies else 0.0
            st.write(f"**{name}** — {member_count}/{total_movies}")
            st.progress(member_progress)

    recommendation_col, tonight_col = st.columns(2)

    with recommendation_col:
        st.subheader("Next Family Movie")
        if next_movie:
            movie_id, title, release_year, phase = next_movie
            year_text = str(release_year) if release_year else "TBA"
            missing_names = get_missing_member_names(
                int(movie_id),
                users,
                statuses,
            )
            missing_text = ", ".join(missing_names) if missing_names else "Nobody"
            st.markdown(
                f"""
                <div class="phase-card">
                    <strong>🎬 {title}</strong><br>
                    Phase {phase} &nbsp;·&nbsp; {year_text}<br><br>
                    <span style="color:#a7afbd;">
                        Still needs it: {missing_text}<br>
                        Earliest release-order title not yet complete for the family.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif total_movies:
            st.success("Everyone has completed the full family watchlist!")

    with tonight_col:
        st.subheader("What Should We Watch Tonight?")
        if tonight_pick:
            movie, missing_names = tonight_pick
            _, title, release_year, phase = movie
            missing_text = ", ".join(missing_names)
            st.markdown(
                f"""
                <div class="phase-card">
                    <strong>🍿 {title}</strong><br>
                    Phase {phase} &nbsp;·&nbsp; {release_year}<br><br>
                    <span style="color:#a7afbd;">
                        Helps {len(missing_names)} family member(s): {missing_text}<br>
                        Chosen to make the biggest shared progress tonight.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.success("No released movie in the catalog is still needed.")

    st.subheader(f"Welcome, {st.session_state.user_name}")
    st.write(
        "Use **My Movies** to update your progress, **Family Tracker** to "
        "compare everyone, and **Movie Library** to browse the full catalog."
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
        render_family_tracker(st.session_state.user_id)
    else:
        render_movie_library()


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
