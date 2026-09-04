"""Streamlit entry point for the family MCU watch tracker."""

from datetime import date

import streamlit as st

from auth.ui import (
    initialize_auth_state,
    is_logged_in,
    logout,
    refresh_authenticated_user,
    render_auth_page,
)
from database.connection import DatabaseConnectionError
from database.movies import get_active_movies
from database.schema import DatabaseSchemaError, validate_schema
from database.user_movies import get_family_movie_statuses
from database.users import get_active_users
from services.recommendations import (
    get_missing_member_names,
    get_next_family_movie,
    get_tonight_recommendation,
)
from ui.theme import apply_theme
from views.admin import render_admin_page
from views.family_tracker import render_family_tracker
from views.movie_library import render_movie_library
from views.my_movies import render_my_movies

DOOMSDAY_DATE = date(2026, 12, 18)


@st.cache_resource
def prepare_database() -> None:
    """Validate the database once per application process without running DDL."""
    validate_schema()


def days_until_doomsday() -> int:
    return max((DOOMSDAY_DATE - date.today()).days, 0)


def get_member_watched_count(user_id: int, statuses, movies) -> int:
    return sum(
        1
        for movie_id, *_ in movies
        if statuses.get((int(user_id), int(movie_id)), False)
    )


def get_family_complete_count(users: list[tuple], statuses, movies) -> int:
    if not users:
        return 0

    user_ids = [int(user[0]) for user in users]
    return sum(
        1
        for movie_id, *_ in movies
        if all(statuses.get((user_id, int(movie_id)), False) for user_id in user_ids)
    )


def get_phase_family_progress(phase: int, users, statuses, movies) -> tuple[int, int]:
    phase_movies = [movie for movie in movies if int(movie[3]) == int(phase)]
    if not users:
        return 0, len(phase_movies)

    user_ids = [int(user[0]) for user in users]
    complete = sum(
        1
        for movie_id, *_ in phase_movies
        if all(statuses.get((user_id, int(movie_id)), False) for user_id in user_ids)
    )
    return complete, len(phase_movies)


def render_phase_progress(users, statuses, movies) -> None:
    phases = sorted({int(movie[3]) for movie in movies})
    st.subheader("Family progress by section")
    phase_columns = st.columns(3)

    for index, phase in enumerate(phases):
        complete, total = get_phase_family_progress(phase, users, statuses, movies)
        progress = complete / total if total else 0.0
        width = int(progress * 100)
        label = "Supplemental" if phase == 0 else f"Phase {phase}"
        with phase_columns[index % 3]:
            st.markdown(
                f"""
                <div class="phase-progress-card">
                    <div class="phase-progress-label">{label}</div>
                    <div class="phase-progress-value">{complete} / {total}</div>
                    <div class="progress-track">
                        <div class="progress-fill" style="width:{width}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_dashboard() -> None:
    users = list(get_active_users())
    statuses = get_family_movie_statuses()

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Watch Initiative</div>
            <h1>Road to Doomsday</h1>
            <p>
                Track MCU and supplemental Marvel movies, compare family
                progress, and get everyone ready for Avengers: Doomsday.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    watch_mode = st.segmented_control(
        "Watch path",
        options=["Essential", "Recommended", "Completionist"],
        default="Recommended",
        key="dashboard_watch_mode",
        help=(
            "Essential shows only must-watch titles. Recommended adds useful "
            "context. Completionist includes every active movie."
        ),
    )
    movies = list(get_active_movies(watch_mode or "Recommended"))

    watched_count = get_member_watched_count(
        int(st.session_state.user_id),
        statuses,
        movies,
    )
    total_movies = len(movies)
    progress = watched_count / total_movies if total_movies else 0.0
    family_complete = get_family_complete_count(users, statuses, movies)
    family_progress = family_complete / total_movies if total_movies else 0.0
    next_movie = get_next_family_movie(users, statuses, movies)
    tonight_pick = get_tonight_recommendation(users, statuses, movies=movies)

    st.caption(f"Current path: **{watch_mode or 'Recommended'}** · {total_movies} movies")

    col1, col2, col3, col4 = st.columns(4)
    metrics = (
        (col1, "Countdown", f"{days_until_doomsday()} days"),
        (col2, "Your Progress", f"{watched_count} / {total_movies}"),
        (col3, "Family Complete", f"{family_complete} / {total_movies}"),
        (col4, "Family Members", str(len(users))),
    )
    for column, label, value in metrics:
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    progress_col, family_col = st.columns(2)
    with progress_col:
        st.subheader("Your mission progress")
        st.progress(progress)
        st.caption(f"{progress:.0%} of this watch path complete")
    with family_col:
        st.subheader("Family mission progress")
        st.progress(family_progress)
        st.caption(f"{family_progress:.0%} of this path watched by everyone")

    render_phase_progress(users, statuses, movies)

    if users:
        st.subheader("Family members")
        member_columns = st.columns(min(len(users), 4))
        for index, user in enumerate(users):
            user_id, name, _, _ = user
            member_count = get_member_watched_count(int(user_id), statuses, movies)
            member_progress = member_count / total_movies if total_movies else 0.0
            with member_columns[index % len(member_columns)]:
                st.write(f"**{name}**")
                st.progress(member_progress)
                st.caption(f"{member_count}/{total_movies} · {member_progress:.0%}")

    recommendation_col, tonight_col = st.columns(2)

    with recommendation_col:
        st.subheader("Next Family Movie")
        if next_movie:
            movie_id, title, release_year, phase = next_movie
            year_text = str(release_year) if release_year else "TBA"
            section = "Supplemental" if int(phase) == 0 else f"Phase {phase}"
            missing_names = get_missing_member_names(int(movie_id), users, statuses)
            missing_text = ", ".join(missing_names) if missing_names else "Nobody"
            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-label">Watch Order Mission</div>
                    <div class="recommendation-title">🎬 {title}</div>
                    <div class="recommendation-meta">{section} · {year_text}</div>
                    <div class="recommendation-detail">
                        <strong>Still needs it:</strong> {missing_text}<br>
                        Earliest title in the selected watch path not yet complete.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif total_movies:
            st.success("Everyone has completed this watch path!")

    with tonight_col:
        st.subheader("What Should We Watch Tonight?")
        if tonight_pick:
            movie, missing_names = tonight_pick
            _, title, release_year, phase = movie
            section = "Supplemental" if int(phase) == 0 else f"Phase {phase}"
            missing_text = ", ".join(missing_names)
            st.markdown(
                f"""
                <div class="recommendation-card">
                    <div class="recommendation-label">Biggest Shared Win</div>
                    <div class="recommendation-title">🍿 {title}</div>
                    <div class="recommendation-meta">{section} · {release_year}</div>
                    <div class="recommendation-detail">
                        <strong>Helps {len(missing_names)}:</strong> {missing_text}<br>
                        Chosen to make the biggest shared progress in this path.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.success("No released movie in this path is still needed.")

    st.subheader(f"Welcome, {st.session_state.user_name}")
    st.write(
        "Use **My Movies** to update your progress, **Family Tracker** to compare "
        "everyone, and **Movie Library** to browse the full catalog."
    )


def render_sidebar() -> str:
    with st.sidebar:
        st.title("Road to Doomsday")
        st.caption("Family Marvel Watch Tracker")
        st.divider()

        options = [
            "🏠 Dashboard",
            "🎞️ My Movies",
            "👥 Family Tracker",
            "📚 Movie Library",
        ]
        if st.session_state.is_admin:
            options.append("🛡️ Administration")

        page = st.radio("Navigation", options=options, label_visibility="collapsed")

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
    if page == "🏠 Dashboard":
        render_dashboard()
    elif page == "🎞️ My Movies":
        render_my_movies(st.session_state.user_id)
    elif page == "👥 Family Tracker":
        render_family_tracker(st.session_state.user_id)
    elif page == "📚 Movie Library":
        render_movie_library()
    elif page == "🛡️ Administration":
        render_admin_page(st.session_state.user_id)


def render_database_error(error: Exception) -> None:
    st.error(str(error))
    st.info(
        "Your saved watch data has not been changed. Check the database "
        "configuration or apply the required one-time schema update."
    )


def main() -> None:
    st.set_page_config(
        page_title="Road to Doomsday",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()
    initialize_auth_state()

    try:
        prepare_database()
        if not is_logged_in():
            render_auth_page()
            return

        if not refresh_authenticated_user():
            st.warning("Your account is no longer active. Please sign in again.")
            render_auth_page()
            return

        page = render_sidebar()
        render_selected_page(page)
    except (DatabaseConnectionError, DatabaseSchemaError) as error:
        render_database_error(error)


if __name__ == "__main__":
    main()
