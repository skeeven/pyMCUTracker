"""Personal movie checklist page."""

import streamlit as st

from database.movies import get_active_movies
from database.user_movies import (
    get_user_movie_statuses,
    set_movie_watched,
)

WATCH_PATHS = ["Essential", "Recommended", "Completionist"]


def _phase_label(phase: int) -> str:
    return "Supplemental" if int(phase) == 0 else f"Phase {phase}"


def render_my_movies(user_id: int) -> None:
    """Render the logged-in user's editable movie checklist."""
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Personal Mission Log</div>
            <h1>My Movies</h1>
            <p>
                Check off each Road to Doomsday movie as you watch it. Your
                progress saves automatically to your account.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    watch_mode = st.segmented_control(
        "Watch path",
        options=WATCH_PATHS,
        default="Recommended",
        key="my_movies_watch_mode",
        help=(
            "Essential shows only must-watch titles. Recommended adds useful "
            "context. Completionist includes every active movie."
        ),
    )
    movies = list(get_active_movies(watch_mode or "Recommended"))
    statuses = get_user_movie_statuses(user_id)
    watched_count = sum(
        1 for movie_id, *_ in movies if statuses.get(int(movie_id), False)
    )
    total_movies = len(movies)
    progress = watched_count / total_movies if total_movies else 0.0

    st.caption(f"Current path: **{watch_mode or 'Recommended'}** · {total_movies} movies")

    col1, col2, col3 = st.columns(3)
    col1.metric("Watched", watched_count)
    col2.metric("Remaining", total_movies - watched_count)
    col3.metric("Complete", f"{progress:.0%}")
    st.progress(progress)

    phases = sorted({int(movie[3]) for movie in movies})
    phase_options = ["All"] + [
        "Supplemental" if phase == 0 else str(phase) for phase in phases
    ]
    phase_filter = st.segmented_control(
        "Section",
        options=phase_options,
        default="All",
        key="my_movies_phase_filter",
    )

    for phase in phases:
        filter_value = "Supplemental" if phase == 0 else str(phase)
        if phase_filter != "All" and phase_filter != filter_value:
            continue

        phase_movies = [movie for movie in movies if int(movie[3]) == phase]
        phase_watched = sum(
            1 for movie in phase_movies if statuses.get(int(movie[0]), False)
        )

        st.subheader(
            f"{_phase_label(phase)}  ·  {phase_watched}/{len(phase_movies)} watched"
        )

        for movie_id, title, release_year, _ in phase_movies:
            movie_id = int(movie_id)
            checked = statuses.get(movie_id, False)
            year_text = str(release_year) if release_year else "TBA"
            label = f"{title} — {year_text}"
            key = f"movie_{user_id}_{movie_id}"

            new_value = st.checkbox(label, value=checked, key=key)
            if new_value != checked:
                set_movie_watched(user_id, user_id, movie_id, new_value)
                st.rerun()

        st.divider()
