"""Shared family movie progress matrix."""

import streamlit as st

from data.movies import MOVIES
from database.user_movies import (
    get_family_movie_statuses,
    set_movie_watched,
)
from database.users import get_active_users


def _member_progress(
    user_id: int,
    statuses: dict[tuple[int, int], bool],
) -> int:
    """Return watched count for one family member."""
    return sum(
        1
        for movie_id, *_ in MOVIES
        if statuses.get((user_id, movie_id), False)
    )


def render_family_tracker(current_user_id: int) -> None:
    """Render the shared matrix with only the current user's column editable."""
    users = get_active_users()
    statuses = get_family_movie_statuses()

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Family Mission Control</div>
            <h1>Family Tracker</h1>
            <p>
                See everyone's progress in one place. Your column is
                interactive; every other family member is read-only.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not users:
        st.info("No active family accounts have been created yet.")
        return

    metric_columns = st.columns(len(users))
    for column, user in zip(metric_columns, users):
        user_id, name, _, _ = user
        watched_count = _member_progress(int(user_id), statuses)
        with column:
            st.metric(name, f"{watched_count}/{len(MOVIES)}")

    st.caption(
        "✓ watched  ·  □ not watched  ·  Only your own column can be changed"
    )

    phase_filter = st.segmented_control(
        "Phase",
        options=["All", "1", "2", "3", "4", "5", "6"],
        default="All",
        key="family_phase_filter",
    )

    column_widths = [4] + [1 for _ in users]

    for phase in range(1, 7):
        if phase_filter != "All" and phase_filter != str(phase):
            continue

        phase_movies = [movie for movie in MOVIES if movie[3] == phase]
        st.subheader(f"Phase {phase}")

        header_columns = st.columns(column_widths)
        header_columns[0].markdown("**Movie**")
        for index, user in enumerate(users, start=1):
            user_id, name, _, _ = user
            suffix = " (You)" if int(user_id) == int(current_user_id) else ""
            header_columns[index].markdown(f"**{name}{suffix}**")

        for movie_id, title, release_year, _ in phase_movies:
            year_text = str(release_year) if release_year else "TBA"
            row_columns = st.columns(column_widths)
            row_columns[0].markdown(f"**{title}**  \n{year_text}")

            for index, user in enumerate(users, start=1):
                user_id = int(user[0])
                watched = statuses.get((user_id, movie_id), False)

                with row_columns[index]:
                    if user_id == int(current_user_id):
                        new_value = st.checkbox(
                            f"{title} watched",
                            value=watched,
                            key=f"family_{user_id}_{movie_id}",
                            label_visibility="collapsed",
                        )
                        if new_value != watched:
                            set_movie_watched(
                                current_user_id,
                                user_id,
                                movie_id,
                                new_value,
                            )
                            st.rerun()
                    else:
                        st.markdown(
                            "<div class='family-status'>✓</div>"
                            if watched
                            else "<div class='family-status family-status-off'>□</div>",
                            unsafe_allow_html=True,
                        )

        st.divider()
