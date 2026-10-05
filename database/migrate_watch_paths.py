"""One-time migration from Doomsday-only priorities to reusable watch paths.

Run this with a SQLiteCloud credential that permits CREATE TABLE and INSERT.
It is idempotent and preserves movies, users, and user_movies history.
"""

from database.connection import get_connection

PRIORITY_OPTIONS = ("Essential", "Recommended", "Optional")

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS watch_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        sort_order INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watch_path_movies (
        watch_path_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Recommended',
        watch_order INTEGER NOT NULL,
        PRIMARY KEY (watch_path_id, movie_id),
        UNIQUE (watch_path_id, watch_order),
        FOREIGN KEY (watch_path_id) REFERENCES watch_paths(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
    )
    """,
)

PATHS = (
    (
        "road-to-doomsday",
        "Road to Doomsday",
        "Movies selected to prepare for Avengers: Doomsday.",
        10,
    ),
    (
        "mcu",
        "MCU",
        "Core Marvel Cinematic Universe theatrical movies.",
        20,
    ),
    (
        "marvel-completionist",
        "Marvel Completionist",
        "Every active Marvel movie in the tracker.",
        90,
    ),
)


def _get_path_id(cursor, slug: str) -> int:
    cursor.execute("SELECT id FROM watch_paths WHERE slug = ?", (slug,))
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError(f"Watch path was not created: {slug}")
    return int(row[0])


def migrate_watch_paths() -> None:
    """Create watch-path tables and seed paths from the existing catalog."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for statement in SCHEMA:
            cursor.execute(statement)

        for slug, name, description, sort_order in PATHS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO watch_paths (
                    slug, name, description, is_active, sort_order
                )
                VALUES (?, ?, ?, 1, ?)
                """,
                (slug, name, description, sort_order),
            )
            cursor.execute(
                """
                UPDATE watch_paths
                SET name = ?, description = ?, sort_order = ?, is_active = 1
                WHERE slug = ?
                """,
                (name, description, sort_order, slug),
            )

        doomsday_id = _get_path_id(cursor, "road-to-doomsday")
        mcu_id = _get_path_id(cursor, "mcu")
        completionist_id = _get_path_id(cursor, "marvel-completionist")

        cursor.execute(
            """
            SELECT id, release_order, doomsday_priority, is_core_mcu, is_active
            FROM movies
            ORDER BY release_order, id
            """
        )
        movies = cursor.fetchall()

        for movie_id, release_order, priority, is_core_mcu, is_active in movies:
            if not bool(is_active):
                continue

            clean_priority = str(priority or "Recommended").title()
            if clean_priority not in PRIORITY_OPTIONS:
                clean_priority = "Recommended"

            cursor.execute(
                """
                INSERT OR REPLACE INTO watch_path_movies (
                    watch_path_id, movie_id, priority, watch_order
                )
                VALUES (?, ?, ?, ?)
                """,
                (doomsday_id, movie_id, clean_priority, release_order),
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO watch_path_movies (
                    watch_path_id, movie_id, priority, watch_order
                )
                VALUES (?, ?, 'Essential', ?)
                """,
                (completionist_id, movie_id, release_order),
            )

            if bool(is_core_mcu):
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO watch_path_movies (
                        watch_path_id, movie_id, priority, watch_order
                    )
                    VALUES (?, ?, 'Essential', ?)
                    """,
                    (mcu_id, movie_id, release_order),
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    migrate_watch_paths()
    print("Watch-path migration complete.")
