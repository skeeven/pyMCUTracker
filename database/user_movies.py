"""Database operations for user movie progress."""

from database.connection import get_connection


def get_user_movie_statuses(user_id: int) -> dict[int, bool]:
    """Return watched status keyed by movie ID for one user."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT movie_id, watched
            FROM user_movies
            WHERE user_id = ?
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return {int(row[0]): bool(row[1]) for row in rows}
    finally:
        connection.close()


def get_family_movie_statuses() -> dict[tuple[int, int], bool]:
    """Return watched status keyed by user ID and movie ID."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_id, movie_id, watched
            FROM user_movies
            """
        )
        rows = cursor.fetchall()
        return {
            (int(row[0]), int(row[1])): bool(row[2])
            for row in rows
        }
    finally:
        connection.close()


def set_movie_watched(
    current_user_id: int,
    user_id: int,
    movie_id: int,
    watched: bool,
) -> None:
    """Create or update one movie status for the current user."""
    if int(current_user_id) != int(user_id):
        raise ValueError("Movie status can only be changed for the current user.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO user_movies (
                user_id,
                movie_id,
                watched,
                watched_date,
                updated_at
            )
            VALUES (
                ?,
                ?,
                ?,
                CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                watched = excluded.watched,
                watched_date = CASE
                    WHEN excluded.watched = 1
                        THEN COALESCE(user_movies.watched_date, CURRENT_TIMESTAMP)
                    ELSE NULL
                END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                movie_id,
                int(watched),
                int(watched),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def get_watched_count(user_id: int) -> int:
    """Return the number of movies marked watched by one user."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM user_movies
            WHERE user_id = ? AND watched = 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        connection.close()
