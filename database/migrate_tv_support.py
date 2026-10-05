"""One-time migration adding TV-series support to the shared catalog."""

from database.connection import get_connection

MOVIE_COLUMNS = {
    "media_type": "TEXT NOT NULL DEFAULT 'movie'",
    "tmdb_id": "INTEGER",
    "end_year": "INTEGER",
}


def migrate_tv_support() -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(movies)")
        existing = {str(row[1]) for row in cursor.fetchall()}
        for name, definition in MOVIE_COLUMNS.items():
            if name not in existing:
                cursor.execute(f"ALTER TABLE movies ADD COLUMN {name} {definition}")

        cursor.execute("PRAGMA table_info(media_metadata)")
        metadata = {str(row[1]) for row in cursor.fetchall()}
        additions = {
            "season_count": "INTEGER",
            "episode_count": "INTEGER",
            "status": "TEXT",
            "first_air_date": "TEXT",
            "last_air_date": "TEXT",
        }
        for name, definition in additions.items():
            if name not in metadata:
                cursor.execute(
                    f"ALTER TABLE media_metadata ADD COLUMN {name} {definition}"
                )
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    migrate_tv_support()
    print("TV-series support migration complete.")
