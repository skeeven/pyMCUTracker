"""SQLiteCloud connection management."""

import os

import sqlitecloud
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Return a connection to the configured SQLiteCloud database."""
    connection_string = os.getenv("SQLITECLOUD_URL")
    if not connection_string:
        raise RuntimeError(
            "SQLITECLOUD_URL is not configured. Add it to your .env file."
        )

    return sqlitecloud.connect(connection_string)
