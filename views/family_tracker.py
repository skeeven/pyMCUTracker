"""Shared family Marvel progress matrix."""

import streamlit as st

from database.user_movies import get_family_movie_statuses, set_movie_watched
from database.users import get_active_users
from database.watch_paths import PRIORITY_HELP, get_path_movies, get_watch_paths

LEVELS = ["Essential", "Recommended", "Completionist"]


def render_family_tracker(current_user_id: int) -> None:
    """Render family progress for a selected Marvel watch path."""
    users = list(get_active_users())
    statuses = get_family_movie_statuses()

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Marvel Tracker</div>
            <h1>Family Tracker</h1>
            <p>Compare everyone's progress across any Marvel watch path.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    if not users:
        st.info("No active family accounts have been created yet.")
        return

    paths = list(get_watch_paths())
    if not paths:
        st.error("No watch paths are configured.")
        return
    path_names = [str(path[2]) for path in paths]
    selected_name = st.selectbox("Watch path", path_names, key="family_path")
    selected = next(path for path in paths if str(path[2]) == selected_name)
    _, path_slug, _, description = selected
    if description:
        st.caption(str(description))

    level = st.segmented_control(
        "Viewing level", LEVELS, default="Recommended", key="family_level"
    )
    with st.expander("What do Essential, Recommended, and Optional mean?"):
        st.markdown(PRIORITY_HELP)
        st.caption("Completionist includes Essential, Recommended, and Optional titles.")

    movies = list(get_path_movies(str(path_slug), level or "Recommended"))
    st.caption(
        f"**{selected_name}** · **{level or 'Recommended'}** · {len(movies)} movies"
    )

    metric_columns = st.columns(min(len(users), 4))
    for index, user in enumerate(users):
        user_id, name, _, _ = user
        watched = sum(
            1 for movie_id, *_ in movies
            if statuses.get((int(user_id), int(movie_id)), False)
        )
        with metric_columns[index % len(metric_columns)]:
            st.metric(name, f"{watched}/{len(movies)}")

    st.caption("✓ watched · □ not watched · Only your own progress can be changed")

    phases = sorted({int(movie[3]) for movie in movies})
    for phase in phases:
        phase_movies = [movie for movie in movies if int(movie[3]) == phase]
        label = "Supplemental" if phase == 0 else f"Phase {phase}"
        st.subheader(label)

        widths = [4] + [1 for _ in users]
        headers = st.columns(widths)
        headers[0].markdown("**Movie**")
        for index, user in enumerate(users, start=1):
            suffix = " (You)" if int(user[0]) == int(current_user_id) else ""
            headers[index].markdown(f"**{user[1]}{suffix}**")

        for movie_id, title, release_year, _ in phase_movies:
            movie_id = int(movie_id)
            row = st.columns(widths)
            row[0].markdown(
                f"**{title}**  \n{str(release_year) if release_year else 'TBA'}"
            )
            for index, user in enumerate(users, start=1):
                user_id = int(user[0])
                watched = statuses.get((user_id, movie_id), False)
                with row[index]:
                    if user_id == int(current_user_id):
                        new_value = st.checkbox(
                            f"{title} watched",
                            value=watched,
                            key=f"family_{path_slug}_{user_id}_{movie_id}",
                            label_visibility="collapsed",
                        )
                        if new_value != watched:
                            set_movie_watched(
                                current_user_id, user_id, movie_id, new_value
                            )
                            st.rerun()
                    else:
                        st.markdown("✓" if watched else "□")
        st.divider()
