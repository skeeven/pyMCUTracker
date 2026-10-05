"""Reusable Marvel watch-path queries and administration."""

from database.connection import get_connection

PRIORITY_OPTIONS = ("Essential", "Recommended", "Optional")
PRIORITY_HELP = (
    "**Essential** — Core viewing needed to understand the major characters and "
    "story for this path.  \n"
    "**Recommended** — Adds important character development, background, or "
    "connections, but is not required.  \n"
    "**Optional** — Part of the broader Marvel story or universe, but not "
    "necessary to understand this path."
)


def get_watch_paths() -> list[tuple]:
    """Return active paths as (id, slug, name, description)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, slug, name, description
            FROM watch_paths
            WHERE is_active = 1
            ORDER BY sort_order, name
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_path_movies(
    path_slug: str = "road-to-doomsday",
    level: str = "Recommended",
) -> list[tuple]:
    """Return movies in path order, filtered to the requested priority level."""
    if level not in ("Essential", "Recommended", "Completionist"):
        level = "Recommended"

    priority_clause = ""
    parameters: list = [path_slug]
    if level == "Essential":
        priority_clause = "AND wpm.priority = ?"
        parameters.append("Essential")
    elif level == "Recommended":
        priority_clause = "AND wpm.priority IN (?, ?)"
        parameters.extend(["Essential", "Recommended"])

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT m.id, m.title, m.release_year, m.phase
            FROM watch_path_movies wpm
            JOIN watch_paths wp ON wp.id = wpm.watch_path_id
            JOIN movies m ON m.id = wpm.movie_id
            WHERE wp.slug = ? AND wp.is_active = 1 AND m.is_active = 1
            {priority_clause}
            ORDER BY wpm.watch_order, m.id
            """,
            tuple(parameters),
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_movie_path_memberships(movie_id: int) -> dict[str, tuple]:
    """Return path slug -> (path id, name, priority, order) for a movie."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT wp.slug, wp.id, wp.name, wpm.priority, wpm.watch_order
            FROM watch_paths wp
            LEFT JOIN watch_path_movies wpm
              ON wpm.watch_path_id = wp.id AND wpm.movie_id = ?
            WHERE wp.is_active = 1
            ORDER BY wp.sort_order, wp.name
            """,
            (movie_id,),
        )
        return {
            str(row[0]): (int(row[1]), str(row[2]), row[3], row[4])
            for row in cursor.fetchall()
        }
    finally:
        connection.close()


def set_movie_path(
    admin_user_id: int,
    movie_id: int,
    path_id: int,
    included: bool,
    priority: str = "Recommended",
    watch_order: int | None = None,
) -> None:
    """Add/update/remove one movie from a watch path."""
    clean_priority = priority.title()
    if clean_priority not in PRIORITY_OPTIONS:
        raise ValueError("Priority must be Essential, Recommended, or Optional.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT is_active, is_admin FROM users WHERE id = ?",
            (admin_user_id,),
        )
        admin = cursor.fetchone()
        if not admin or not bool(admin[0]) or not bool(admin[1]):
            raise PermissionError("Administrator access is required.")

        if not included:
            cursor.execute(
                "DELETE FROM watch_path_movies WHERE watch_path_id = ? AND movie_id = ?",
                (path_id, movie_id),
            )
            connection.commit()
            return

        cursor.execute(
            """
            SELECT watch_order FROM watch_path_movies
            WHERE watch_path_id = ? AND movie_id = ?
            """,
            (path_id, movie_id),
        )
        existing = cursor.fetchone()
        if watch_order is None:
            if existing:
                watch_order = int(existing[0])
            else:
                cursor.execute(
                    """
                    SELECT COALESCE(MAX(watch_order), 0) + 1
                    FROM watch_path_movies WHERE watch_path_id = ?
                    """,
                    (path_id,),
                )
                watch_order = int(cursor.fetchone()[0])

        if existing:
            cursor.execute(
                """
                UPDATE watch_path_movies
                SET priority = ?, watch_order = ?
                WHERE watch_path_id = ? AND movie_id = ?
                """,
                (clean_priority, watch_order, path_id, movie_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO watch_path_movies (
                    watch_path_id, movie_id, priority, watch_order
                ) VALUES (?, ?, ?, ?)
                """,
                (path_id, movie_id, clean_priority, watch_order),
            )
        connection.commit()
    finally:
        connection.close()
