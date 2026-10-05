"""Personal Marvel movie checklist page."""

import streamlit as st

from database.user_movies import get_user_movie_statuses, set_movie_watched
from database.watch_paths import PRIORITY_HELP, get_path_movies, get_watch_paths

LEVELS = ["Essential", "Recommended", "Completionist"]


def _phase_label(phase: int) -> str:
    return "Supplemental" if int(phase) == 0 else f"Phase {phase}"


def render_my_movies(user_id: int) -> None:
    """Render the logged-in user's editable movie checklist."""
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Personal Marvel Log</div>
            <h1>My Movies</h1>
            <p>Choose a Marvel watch path and track your progress.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    paths = list(get_watch_paths())
    if not paths:
        st.error("No watch paths are configured.")
        return

    path_names = [str(path[2]) for path in paths]
    selected_name = st.selectbox("Watch path", path_names, key="my_movies_path")
    selected = next(path for path in paths if str(path[2]) == selected_name)
    _, path_slug, _, description = selected
    if description:
        st.caption(str(description))

    level = st.segmented_control(
        "Viewing level",
        options=LEVELS,
        default="Recommended",
        key="my_movies_level",
    )
    with st.expander("What do Essential, Recommended, and Optional mean?"):
        st.markdown(PRIORITY_HELP)
        st.caption("Completionist includes Essential, Recommended, and Optional titles.")

    movies = list(get_path_movies(str(path_slug), level or "Recommended"))
    statuses = get_user_movie_statuses(user_id)
    watched_count = sum(
        1 for movie_id, *_ in movies if statuses.get(int(movie_id), False)
    )
    total_movies = len(movies)
    progress = watched_count / total_movies if total_movies else 0.0

    st.caption(
        f"**{selected_name}** · **{level or 'Recommended'}** · {total_movies} movies"
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Watched", watched_count)
    col2.metric("Remaining", total_movies - watched_count)
    col3.metric("Complete", f"{progress:.0%}")
    st.progress(progress)

    phases = sorted({int(movie[3]) for movie in movies})
    for phase in phases:
        phase_movies = [movie for movie in movies if int(movie[3]) == phase]
        phase_watched = sum(
            1 for movie in phase_movies if statuses.get(int(movie[0]), False)
        )
        st.subheader(
            f"{_phase_label(phase)} · {phase_watched}/{len(phase_movies)} watched"
        )
        for movie_id, title, release_year, _ in phase_movies:
            movie_id = int(movie_id)
            checked = statuses.get(movie_id, False)
            year_text = str(release_year) if release_year else "TBA"
            new_value = st.checkbox(
                f"{title} — {year_text}",
                value=checked,
                key=f"movie_{user_id}_{movie_id}_{path_slug}",
            )
            if new_value != checked:
                set_movie_watched(user_id, user_id, movie_id, new_value)
                st.rerun()
        st.divider()
