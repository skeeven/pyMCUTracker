"""One-time DDL migration for TMDB-backed library metadata."""

from database.connection import get_connection

STATEMENT = """
CREATE TABLE IF NOT EXISTS media_metadata (
    movie_id INTEGER PRIMARY KEY,
    media_type TEXT NOT NULL DEFAULT 'movie',
    tmdb_id INTEGER,
    imdb_id TEXT,
    overview TEXT,
    tagline TEXT,
    poster_path TEXT,
    backdrop_path TEXT,
    runtime_minutes INTEGER,
    genres TEXT,
    content_rating TEXT,
    tmdb_rating REAL,
    tmdb_vote_count INTEGER,
    director TEXT,
    cast_names TEXT,
    trailer_key TEXT,
    trailer_name TEXT,
    homepage TEXT,
    last_refreshed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
)
"""


def migrate_media_metadata() -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(STATEMENT)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    migrate_media_metadata()
    print("Media metadata migration complete.")
