"""Persistence for enriched movie/TV metadata."""

from database.connection import get_connection


def get_metadata_map() -> dict[int, tuple]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT movie_id, media_type, tmdb_id, imdb_id, overview, tagline,
                   poster_path, backdrop_path, runtime_minutes, genres,
                   content_rating, tmdb_rating, tmdb_vote_count, director,
                   cast_names, trailer_key, trailer_name, homepage,
                   last_refreshed_at, season_count, episode_count, status,
                   first_air_date, last_air_date
            FROM media_metadata
            """
        )
        return {int(row[0]): row for row in cursor.fetchall()}
    finally:
        connection.close()


def upsert_metadata(movie_id: int, values: dict) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO media_metadata (
                movie_id, media_type, tmdb_id, imdb_id, overview, tagline,
                poster_path, backdrop_path, runtime_minutes, genres,
                content_rating, tmdb_rating, tmdb_vote_count, director,
                cast_names, trailer_key, trailer_name, homepage, season_count, episode_count, status,
                first_air_date, last_air_date, last_refreshed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                      CURRENT_TIMESTAMP)
            """,
            (
                movie_id, values.get("media_type", "movie"), values.get("tmdb_id"),
                values.get("imdb_id"), values.get("overview"), values.get("tagline"),
                values.get("poster_path"), values.get("backdrop_path"),
                values.get("runtime_minutes"), values.get("genres"),
                values.get("content_rating"), values.get("tmdb_rating"),
                values.get("tmdb_vote_count"), values.get("director"),
                values.get("cast_names"), values.get("trailer_key"),
                values.get("trailer_name"), values.get("homepage"),
                values.get("season_count"), values.get("episode_count"),
                values.get("status"), values.get("first_air_date"),
                values.get("last_air_date"),
            ),
        )
        connection.commit()
    finally:
        connection.close()
