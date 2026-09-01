"""SQLiteCloud connection management."""

import os

import sqlitecloud
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnectionError(RuntimeError):
    """Raised when the application cannot connect to SQLiteCloud."""


def get_connection():
    """Return a connection to the configured SQLiteCloud database."""
    connection_string = os.getenv("SQLITECLOUD_URL")
    if not connection_string:
        raise DatabaseConnectionError(
            "The database connection is not configured. "
            "Set SQLITECLOUD_URL and restart the app."
        )

    try:
        return sqlitecloud.connect(connection_string)
    except Exception as exc:
        raise DatabaseConnectionError(
            "The family tracker could not connect to its database. "
            "Please try again in a moment."
        ) from exc
