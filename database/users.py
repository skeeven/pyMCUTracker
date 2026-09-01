"""Database operations for application users."""

from database.connection import get_connection


def get_user_by_email(email: str):
    """Return a user row by email, or None when no user exists."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, password_hash, is_active, is_admin
            FROM users
            WHERE email = ? COLLATE NOCASE
            """,
            (email.strip(),),
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_user_by_id(user_id: int):
    """Return a user row by primary key, or None when no user exists."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, password_hash, is_active, is_admin
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_active_users() -> list[tuple]:
    """Return active family members ordered by account creation."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, is_admin
            FROM users
            WHERE is_active = 1
            ORDER BY id
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_all_users() -> list[tuple]:
    """Return all family accounts, including inactive accounts."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, name, email, is_active, is_admin, created_at
            FROM users
            ORDER BY id
            """
        )
        return cursor.fetchall()
    finally:
        connection.close()


def _require_admin(cursor, admin_user_id: int) -> None:
    """Raise when the acting account is not an active administrator."""
    cursor.execute(
        """
        SELECT is_active, is_admin
        FROM users
        WHERE id = ?
        """,
        (admin_user_id,),
    )
    row = cursor.fetchone()
    if not row or not bool(row[0]) or not bool(row[1]):
        raise PermissionError("Administrator access is required.")


def update_user_name(
    admin_user_id: int,
    user_id: int,
    name: str,
) -> None:
    """Update a family member's display name as an administrator."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Display name cannot be empty.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        _require_admin(cursor, admin_user_id)
        cursor.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (clean_name, user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Family member was not found.")
        connection.commit()
    finally:
        connection.close()


def set_user_active(
    admin_user_id: int,
    user_id: int,
    is_active: bool,
) -> None:
    """Activate or deactivate a family account as an administrator."""
    if int(admin_user_id) == int(user_id) and not is_active:
        raise ValueError("You cannot deactivate your own administrator account.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        _require_admin(cursor, admin_user_id)
        cursor.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (int(is_active), user_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Family member was not found.")
        connection.commit()
    finally:
        connection.close()


def create_user(name: str, email: str, password_hash: str):
    """Create a user and return the newly created user row.

    The first account created automatically becomes the administrator.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        is_admin = 1 if user_count == 0 else 0

        cursor.execute(
            """
            INSERT INTO users (
                name,
                email,
                password_hash,
                is_admin
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name.strip(),
                email.strip().lower(),
                password_hash,
                is_admin,
            ),
        )
        connection.commit()

        cursor.execute(
            """
            SELECT id, name, email, password_hash, is_active, is_admin
            FROM users
            WHERE email = ? COLLATE NOCASE
            """,
            (email.strip(),),
        )
        return cursor.fetchone()
    finally:
        connection.close()
