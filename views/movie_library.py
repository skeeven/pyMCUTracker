"""Rich Marvel movie library backed by cached TMDB metadata."""

import streamlit as st

from database.media_metadata import get_metadata_map
from database.movies import get_all_movies
from services.tmdb import TMDBError, refresh_library, test_connection

IMAGE_ROOT = "https://image.tmdb.org/t/p/w342"


def render_movie_library() -> None:
    """Render searchable movie cards with cached TMDB details."""
    movies = [movie for movie in get_all_movies() if bool(movie[10])]

    st.markdown(
        """
        <section class="hero">
            <div class="eyebrow">Marvel Archive</div>
            <h1>Movie Library</h1>
            <p>Browse the Marvel catalog with cast, ratings, story details, and trailers.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if bool(st.session_state.get("is_admin", False)):
        refresh_col, note_col = st.columns([1, 3])
        with refresh_col:
            if st.button("🔄 Refresh Library", use_container_width=True):
                status = st.status("Checking TMDB connection...", expanded=True)
                progress = st.progress(0.0)
                current = st.empty()

                def report(index, total, title, stage):
                    percent = index / total if total else 1.0
                    progress.progress(percent)
                    labels = {
                        "retrieving": "Retrieving",
                        "saved": "Updated",
                        "unmatched": "No match for",
                        "failed": "Error updating",
                    }
                    current.write(
                        f"{labels.get(stage, stage.title())}: "
                        f"**{title}** ({index}/{total})"
                    )

                try:
                    message = test_connection()
                    status.write(f"✅ {message}")
                    status.write("📡 Retrieving library metadata...")
                    result = refresh_library(report)
                    refreshed = int(result["refreshed"])
                    unmatched = result["unmatched"]
                    failed = result["failed"]
                    progress.progress(1.0)
                    current.empty()

                    status.write(
                        f"✅ Updated **{refreshed} of {result['total']}** active titles."
                    )
                    if unmatched:
                        status.write(
                            "⚠️ No TMDB match: " + ", ".join(unmatched)
                        )
                    if failed:
                        status.write(
                            f"❌ {len(failed)} title(s) failed while saving."
                        )
                        for failed_title, error in failed[:10]:
                            status.write(f"- {failed_title}: {error}")
                    state = "complete" if not failed else "error"
                    status.update(
                        label=(
                            f"Library refresh finished — {refreshed} titles updated"
                        ),
                        state=state,
                        expanded=bool(unmatched or failed),
                    )
                    st.session_state["library_refresh_result"] = result
                except TMDBError as exc:
                    progress.empty()
                    current.empty()
                    status.write(f"❌ {exc}")
                    status.update(
                        label="Unable to refresh library",
                        state="error",
                        expanded=True,
                    )
                except Exception as exc:
                    progress.empty()
                    current.empty()
                    status.write(
                        "❌ The refresh stopped because of an application or "
                        f"database error: {exc}"
                    )
                    status.update(
                        label="Library refresh failed",
                        state="error",
                        expanded=True,
                    )
        with note_col:
            st.caption(
                "Administrator only · Updates cached ratings, cast, artwork, "
                "synopses, and trailers."
            )

    try:
        metadata = get_metadata_map()
    except Exception:
        metadata = {}
        st.info(
            "Rich metadata is not initialized yet. Run the one-time media "
            "metadata migration, then use Refresh Library."
        )

    categories = sorted({str(movie[6]) for movie in movies})
    search_col, category_col = st.columns([3, 1])
    search_text = search_col.text_input(
        "Search", placeholder="Movie, actor, director, universe..."
    ).strip().lower()
    category_filter = category_col.selectbox("Category", ["All"] + categories)

    filtered = []
    for movie in movies:
        movie_id = int(movie[0])
        meta = metadata.get(movie_id)
        searchable = " ".join(
            [
                str(movie[1]), str(movie[6]), str(movie[7]), str(movie[11] or ""),
                str(meta[13] if meta else ""), str(meta[14] if meta else ""),
            ]
        ).lower()
        if search_text and search_text not in searchable:
            continue
        if category_filter != "All" and str(movie[6]) != category_filter:
            continue
        filtered.append(movie)

    st.caption(f"Showing {len(filtered)} of {len(movies)} movies")

    for movie in filtered:
        movie_id, title, year = int(movie[0]), str(movie[1]), movie[2]
        category, universe, notes = str(movie[6]), str(movie[7]), movie[11]
        meta = metadata.get(movie_id)

        with st.expander(f"🎬 {title} ({year or 'TBA'})"):
            if not meta:
                st.caption(f"{category} · {universe}")
                if notes:
                    st.write(notes)
                st.info("No enriched information cached yet.")
                continue

            (
                _, media_type, tmdb_id, imdb_id, overview, tagline, poster_path,
                backdrop_path, runtime, genres, content_rating, rating,
                vote_count, director, cast_names, trailer_key, trailer_name,
                homepage, refreshed_at,
            ) = meta

            poster_col, detail_col = st.columns([1, 3])
            with poster_col:
                if poster_path:
                    st.image(IMAGE_ROOT + str(poster_path), use_container_width=True)
                if rating:
                    st.metric("TMDB Rating", f"{float(rating):.1f}/10")
                    if vote_count:
                        st.caption(f"{int(vote_count):,} votes")
            with detail_col:
                if tagline:
                    st.markdown(f"*{tagline}*")
                facts = [category, universe]
                if runtime:
                    facts.append(f"{runtime} min")
                if content_rating:
                    facts.append(str(content_rating))
                if genres:
                    facts.append(str(genres))
                st.caption(" · ".join(facts))
                if overview:
                    st.write(overview)
                if director:
                    st.write(f"**Director:** {director}")
                if cast_names:
                    st.write(f"**Cast:** {cast_names}")

            if trailer_key:
                st.markdown(f"**Trailer:** {trailer_name or 'Official Trailer'}")
                st.video(f"https://www.youtube.com/watch?v={trailer_key}")

            st.caption(
                f"Metadata: TMDB #{tmdb_id} · Last refreshed {refreshed_at}"
            )

    st.caption(
        "Movie information and imagery provided using TMDB. "
        "This product uses the TMDB API but is not endorsed or certified by TMDB."
    )
