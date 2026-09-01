"""Database schema creation and initial movie seeding."""

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
        phase INTEGER NOT NULL,
        release_order INTEGER NOT NULL UNIQUE
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


def seed_movies() -> None:
    """Insert the MCU catalog without duplicating existing movies."""
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
                    release_order
                )
                VALUES (?, ?, ?, ?, ?)
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
    """Create the schema and seed all initial application data."""
    create_schema()
    seed_movies()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully with MCU movie catalog.")
