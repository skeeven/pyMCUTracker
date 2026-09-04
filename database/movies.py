"""Database operations for the Road to Doomsday movie catalog."""

from database.connection import get_connection

ORDER_OFFSET = 100000
PRIORITY_OPTIONS = ("Essential", "Recommended", "Optional")


def get_active_movies(watch_mode: str = "Completionist") -> list[tuple]:
    """Return active movies in watch order using the legacy four-field shape."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        where_clause = "WHERE is_active = 1"
        parameters: tuple = ()

        if watch_mode == "Essential":
            where_clause += " AND doomsday_priority = ?"
            parameters = ("Essential",)
        elif watch_mode == "Recommended":
            where_clause += " AND doomsday_priority IN (?, ?)"
            parameters = ("Essential", "Recommended")

        cursor.execute(
            f"""
            SELECT id, title, release_year, phase
            FROM movies
            {where_clause}
            ORDER BY release_order, id
            """,
            parameters,
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_all_movies() -> list[tuple]:
    """Return the full movie catalog with administrative metadata."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                title,
                release_year,
                release_date,
                phase,
                release_order,
                category,
                universe,
                is_core_mcu,
                is_doomsday_relevant,
                doomsday_priority,
                is_active,
                notes
            FROM movies
            ORDER BY release_order, id
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def _require_admin(cursor, admin_user_id: int) -> None:
    cursor.execute(
        "SELECT is_active, is_admin FROM users WHERE id = ?",
        (admin_user_id,),
    )
    row = cursor.fetchone()
    if not row or not bool(row[0]) or not bool(row[1]):
        raise PermissionError("Administrator access is required.")


def _next_movie_id(cursor) -> int:
    cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM movies")
    return int(cursor.fetchone()[0])


def _make_room_for_order(cursor, release_order: int) -> None:
    cursor.execute(
        "UPDATE movies SET release_order = release_order + ? WHERE release_order >= ?",
        (ORDER_OFFSET, release_order),
    )
    cursor.execute(
        """
        UPDATE movies
        SET release_order = release_order - ?
        WHERE release_order >= ?
        """,
        (ORDER_OFFSET - 1, ORDER_OFFSET + release_order),
    )


def _move_movie(cursor, movie_id: int, old_order: int, new_order: int) -> None:
    if old_order == new_order:
        return

    cursor.execute(
        "UPDATE movies SET release_order = ? WHERE id = ?",
        (-int(movie_id), movie_id),
    )

    if new_order < old_order:
        cursor.execute(
            """
            UPDATE movies
            SET release_order = release_order + ?
            WHERE release_order >= ? AND release_order < ?
            """,
            (ORDER_OFFSET, new_order, old_order),
        )
        cursor.execute(
            """
            UPDATE movies
            SET release_order = release_order - ?
            WHERE release_order >= ? AND release_order < ?
            """,
            (
                ORDER_OFFSET - 1,
                ORDER_OFFSET + new_order,
                ORDER_OFFSET + old_order,
            ),
        )
    else:
        cursor.execute(
            """
            UPDATE movies
            SET release_order = release_order + ?
            WHERE release_order > ? AND release_order <= ?
            """,
            (ORDER_OFFSET, old_order, new_order),
        )
        cursor.execute(
            """
            UPDATE movies
            SET release_order = release_order - ?
            WHERE release_order > ? AND release_order <= ?
            """,
            (
                ORDER_OFFSET + 1,
                ORDER_OFFSET + old_order,
                ORDER_OFFSET + new_order,
            ),
        )

    cursor.execute(
        "UPDATE movies SET release_order = ? WHERE id = ?",
        (new_order, movie_id),
    )


def _validate_priority(priority: str) -> str:
    clean_priority = priority.strip().title()
    if clean_priority not in PRIORITY_OPTIONS:
        raise ValueError("Priority must be Essential, Recommended, or Optional.")
    return clean_priority


def add_movie(
    admin_user_id: int,
    title: str,
    release_year: int | None,
    release_date: str | None,
    phase: int,
    release_order: int,
    category: str,
    universe: str,
    is_core_mcu: bool,
    is_doomsday_relevant: bool,
    notes: str,
    doomsday_priority: str = "Recommended",
) -> None:
    """Add a movie to the catalog as an administrator."""
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("Movie title is required.")
    if release_order < 1:
        raise ValueError("Watch order must be at least 1.")
    if phase < 0 or phase > 6:
        raise ValueError("Phase must be between 0 and 6.")
    priority = _validate_priority(doomsday_priority)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        _require_admin(cursor, admin_user_id)
        movie_id = _next_movie_id(cursor)
        _make_room_for_order(cursor, release_order)
        cursor.execute(
            """
            INSERT INTO movies (
                id, title, release_year, release_date, phase, release_order,
                category, universe, is_core_mcu, is_doomsday_relevant,
                doomsday_priority, is_active, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                movie_id,
                clean_title,
                release_year,
                release_date or None,
                phase,
                release_order,
                category.strip() or "MCU",
                universe.strip() or "Marvel Cinematic Universe",
                int(is_core_mcu),
                int(is_doomsday_relevant),
                priority,
                notes.strip(),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def update_movie(
    admin_user_id: int,
    movie_id: int,
    title: str,
    release_year: int | None,
    release_date: str | None,
    phase: int,
    release_order: int,
    category: str,
    universe: str,
    is_core_mcu: bool,
    is_doomsday_relevant: bool,
    notes: str,
    doomsday_priority: str = "Recommended",
) -> None:
    """Update an existing movie as an administrator."""
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("Movie title is required.")
    if release_order < 1:
        raise ValueError("Watch order must be at least 1.")
    if phase < 0 or phase > 6:
        raise ValueError("Phase must be between 0 and 6.")
    priority = _validate_priority(doomsday_priority)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        _require_admin(cursor, admin_user_id)
        cursor.execute(
            "SELECT release_order FROM movies WHERE id = ?",
            (movie_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError("Movie was not found.")

        old_order = int(row[0])
        _move_movie(cursor, movie_id, old_order, release_order)
        cursor.execute(
            """
            UPDATE movies
            SET title = ?, release_year = ?, release_date = ?, phase = ?,
                category = ?, universe = ?, is_core_mcu = ?,
                is_doomsday_relevant = ?, doomsday_priority = ?, notes = ?
            WHERE id = ?
            """,
            (
                clean_title,
                release_year,
                release_date or None,
                phase,
                category.strip() or "MCU",
                universe.strip() or "Marvel Cinematic Universe",
                int(is_core_mcu),
                int(is_doomsday_relevant),
                priority,
                notes.strip(),
                movie_id,
            ),
        )
        connection.commit()
    finally:
        connection.close()


def set_movie_active(admin_user_id: int, movie_id: int, is_active: bool) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        _require_admin(cursor, admin_user_id)
        cursor.execute("SELECT id FROM movies WHERE id = ?", (movie_id,))
        if cursor.fetchone() is None:
            raise ValueError("Movie was not found.")
        cursor.execute(
            "UPDATE movies SET is_active = ? WHERE id = ?",
            (int(is_active), movie_id),
        )
        connection.commit()
    finally:
        connection.close()
