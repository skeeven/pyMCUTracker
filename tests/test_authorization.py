"""Tests for authorization guards that run before database writes."""

import pytest

from database.user_movies import set_movie_watched
from database.users import set_user_active


def test_user_cannot_update_another_users_movie_status() -> None:
    """Movie writes must reject a target user different from the actor."""
    with pytest.raises(ValueError, match="current user"):
        set_movie_watched(
            current_user_id=1,
            user_id=2,
            movie_id=1,
            watched=True,
        )


def test_admin_cannot_deactivate_self() -> None:
    """The self-deactivation guard should run before any database access."""
    with pytest.raises(ValueError, match="cannot deactivate"):
        set_user_active(
            admin_user_id=1,
            user_id=1,
            is_active=False,
        )
