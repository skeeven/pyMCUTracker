"""Browse and filter the Road to Doomsday movie catalog."""

from html import escape

import streamlit as st

from database.movies import get_all_movies


def render_movie_library() -> None:
    """Render the searchable active movie catalog."""
    movies = [movie for movie in get_all_movies() if bool(movie[10])]

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Archive Database</div>
            <h1>Movie Library</h1>
            <p>
                Browse the complete Road to Doomsday catalog, including MCU
                and supplemental multiverse titles.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    categories = sorted({str(movie[6]) for movie in movies})
    search_column, category_column = st.columns([3, 1])

    with search_column:
        search_text = st.text_input(
            "Search movies",
            placeholder="Search by title...",
            key="movie_library_search",
        ).strip().lower()

    with category_column:
        category_filter = st.selectbox(
            "Category",
            options=["All"] + categories,
            key="movie_library_category",
        )

    filtered_movies = []
    for movie in movies:
        title = str(movie[1])
        category = str(movie[6])
        if search_text and search_text not in title.lower():
            continue
        if category_filter != "All" and category != category_filter:
            continue
        filtered_movies.append(movie)

    st.caption(f"Showing {len(filtered_movies)} of {len(movies)} movies")
    if not filtered_movies:
        st.info("No movies match the current filters.")
        return

    for movie in filtered_movies:
        (
            _movie_id,
            title,
            release_year,
            _release_date,
            phase,
            watch_order,
            category,
            universe,
            is_core_mcu,
            is_doomsday_relevant,
            _is_active,
            notes,
        ) = movie

        year_text = str(release_year) if release_year else "TBA"
        section_text = "Supplemental" if int(phase) == 0 else f"Phase {phase}"
        tags = [str(category), str(universe), section_text]
        if bool(is_core_mcu):
            tags.append("Core MCU")
        if bool(is_doomsday_relevant):
            tags.append("Doomsday Relevant")

        title_html = escape(str(title))
        meta_html = escape(f"{year_text} · {' · '.join(tags)}")
        notes_html = (
            f'<div class="library-meta">{escape(str(notes))}</div>'
            if notes
            else ""
        )

        card_html = (
            '<div class="library-card">'
            f'<div class="library-order">#{int(watch_order):02d}</div>'
            '<div class="library-details">'
            f'<div class="library-title">{title_html}</div>'
            f'<div class="library-meta">{meta_html}</div>'
            f'{notes_html}'
            '</div>'
            '</div>'
        )

        st.markdown(card_html, unsafe_allow_html=True)
