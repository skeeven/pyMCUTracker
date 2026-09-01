"""Personal movie checklist page."""

import streamlit as st

from data.movies import MOVIES
from database.user_movies import (
    get_user_movie_statuses,
    set_movie_watched,
)


def render_my_movies(user_id: int) -> None:
    """Render the logged-in user's editable MCU movie checklist."""
    statuses = get_user_movie_statuses(user_id)
    watched_count = sum(1 for watched in statuses.values() if watched)
    total_movies = len(MOVIES)
    progress = watched_count / total_movies if total_movies else 0.0

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Personal Mission Log</div>
            <h1>My Movies</h1>
            <p>
                Check off each movie as you watch it. Your progress saves
                automatically to your account.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Watched", watched_count)
    with col2:
        st.metric("Remaining", total_movies - watched_count)
    with col3:
        st.metric("Complete", f"{progress:.0%}")

    st.progress(progress)

    phase_filter = st.segmented_control(
        "Phase",
        options=["All", "1", "2", "3", "4", "5", "6"],
        default="All",
        key="my_movies_phase_filter",
    )

    for phase in range(1, 7):
        if phase_filter != "All" and phase_filter != str(phase):
            continue

        phase_movies = [movie for movie in MOVIES if movie[3] == phase]
        phase_watched = sum(
            1 for movie in phase_movies if statuses.get(movie[0], False)
        )

        st.subheader(
            f"Phase {phase}  ·  {phase_watched}/{len(phase_movies)} watched"
        )

        for movie_id, title, release_year, _ in phase_movies:
            checked = statuses.get(movie_id, False)
            year_text = str(release_year) if release_year else "TBA"
            label = f"{movie_id}. {title} — {year_text}"
            key = f"movie_{user_id}_{movie_id}"

            new_value = st.checkbox(
                label,
                value=checked,
                key=key,
            )

            if new_value != checked:
                set_movie_watched(user_id, user_id, movie_id, new_value)
                st.rerun()

        st.divider()
