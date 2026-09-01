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
