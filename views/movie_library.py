"""Browse and filter the MCU movie catalog."""

import streamlit as st

from data.movies import MOVIES


def render_movie_library() -> None:
    """Render the searchable MCU movie catalog."""
    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Archive Database</div>
            <h1>Movie Library</h1>
            <p>
                Browse the complete Road to Doomsday movie catalog by title,
                phase, and release year.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    search_column, phase_column = st.columns([3, 1])

    with search_column:
        search_text = st.text_input(
            "Search movies",
            placeholder="Search by title...",
            key="movie_library_search",
        ).strip().lower()

    with phase_column:
        phase_filter = st.selectbox(
            "Phase",
            options=["All", 1, 2, 3, 4, 5, 6],
            key="movie_library_phase",
        )

    filtered_movies = []
    for movie in MOVIES:
        release_order, title, release_year, phase = movie

        if search_text and search_text not in title.lower():
            continue
        if phase_filter != "All" and phase != phase_filter:
            continue

        filtered_movies.append(
            (release_order, title, release_year, phase)
        )

    st.caption(
        f"Showing {len(filtered_movies)} of {len(MOVIES)} movies"
    )

    if not filtered_movies:
        st.info("No movies match the current filters.")
        return

    for release_order, title, release_year, phase in filtered_movies:
        year_text = str(release_year) if release_year else "TBA"
        st.markdown(
            f"""
            <div class="library-card">
                <div class="library-order">#{release_order:02d}</div>
                <div class="library-details">
                    <div class="library-title">{title}</div>
                    <div class="library-meta">
                        Phase {phase} &nbsp;·&nbsp; {year_text}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
