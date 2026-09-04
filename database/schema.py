"""Database schema creation, validation, and initial movie seeding."""

from data.movies import MOVIES
from database.connection import get_connection

SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL UNIQUE,
        release_year INTEGER,
        phase INTEGER NOT NULL DEFAULT 0,
        release_order INTEGER NOT NULL UNIQUE,
        release_date TEXT,
        category TEXT NOT NULL DEFAULT 'MCU',
        universe TEXT NOT NULL DEFAULT 'Marvel Cinematic Universe',
        is_core_mcu INTEGER NOT NULL DEFAULT 1,
        is_doomsday_relevant INTEGER NOT NULL DEFAULT 1,
        doomsday_priority TEXT NOT NULL DEFAULT 'Essential',
        is_active INTEGER NOT NULL DEFAULT 1,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        watched INTEGER NOT NULL DEFAULT 0,
        watched_date TEXT,
        rating INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, movie_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
    )
    """,
)

MOVIE_COLUMNS = {
    "release_date": "TEXT",
    "category": "TEXT NOT NULL DEFAULT 'MCU'",
    "universe": "TEXT NOT NULL DEFAULT 'Marvel Cinematic Universe'",
    "is_core_mcu": "INTEGER NOT NULL DEFAULT 1",
    "is_doomsday_relevant": "INTEGER NOT NULL DEFAULT 1",
    "doomsday_priority": "TEXT NOT NULL DEFAULT 'Essential'",
    "is_active": "INTEGER NOT NULL DEFAULT 1",
    "notes": "TEXT",
}


class DatabaseSchemaError(RuntimeError):
    """Raised when the deployed database schema is behind the application."""


def create_schema() -> None:
    """Create all application tables if they do not already exist."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for statement in SCHEMA_STATEMENTS:
            cursor.execute(statement)
        connection.commit()
    finally:
        connection.close()


def migrate_movie_schema() -> None:
    """Add newer catalog fields using a credential that permits DDL."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(movies)")
        existing_columns = {str(row[1]) for row in cursor.fetchall()}

        for column_name, definition in MOVIE_COLUMNS.items():
            if column_name not in existing_columns:
                cursor.execute(
                    f"ALTER TABLE movies ADD COLUMN {column_name} {definition}"
                )
        connection.commit()
    finally:
        connection.close()


def validate_schema() -> None:
    """Validate required movie fields without attempting schema changes."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(movies)")
        existing_columns = {str(row[1]) for row in cursor.fetchall()}
        required_columns = {
            "id",
            "title",
            "release_year",
            "phase",
            "release_order",
            *MOVIE_COLUMNS.keys(),
        }
        missing = sorted(required_columns - existing_columns)
        if missing:
            raise DatabaseSchemaError(
                "The database needs a one-time schema update. Missing movie "
                "columns: " + ", ".join(missing)
            )
    finally:
        connection.close()


def seed_movies() -> None:
    """Insert the original MCU catalog without duplicating existing movies."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for release_order, title, release_year, phase in MOVIES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO movies (
                    id,
                    title,
                    release_year,
                    phase,
                    release_order,
                    category,
                    universe,
                    is_core_mcu,
                    is_doomsday_relevant,
                    doomsday_priority,
                    is_active
                )
                VALUES (
                    ?, ?, ?, ?, ?, 'MCU', 'Marvel Cinematic Universe',
                    1, 1, 'Essential', 1
                )
                """,
                (
                    release_order,
                    title,
                    release_year,
                    phase,
                    release_order,
                ),
            )
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    """Create, migrate, and seed application data for setup/admin use."""
    create_schema()
    migrate_movie_schema()
    seed_movies()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully with movie catalog support.")
