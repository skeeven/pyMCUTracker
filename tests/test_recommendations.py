"""Tests for family movie recommendation rules."""

from datetime import date

import services.recommendations as recommendations


USERS = [
    (1, "Steve", "steve@example.com", 1),
    (2, "Nisha", "nisha@example.com", 0),
]


def test_missing_member_names_returns_only_unwatched_members() -> None:
    """Missing-member labels should reflect per-user watch status."""
    statuses = {
        (1, 1): True,
        (2, 1): False,
    }

    missing = recommendations.get_missing_member_names(1, USERS, statuses)

    assert missing == ["Nisha"]


def test_next_family_movie_uses_release_order(monkeypatch) -> None:
    """The next family movie should be the first title not complete by all."""
    movies = [
        (1, "Movie One", 2020, 1),
        (2, "Movie Two", 2021, 1),
        (3, "Movie Three", 2022, 1),
    ]
    monkeypatch.setattr(recommendations, "MOVIES", movies)
    statuses = {
        (1, 1): True,
        (2, 1): True,
        (1, 2): True,
        (2, 2): False,
    }

    assert recommendations.get_next_family_movie(USERS, statuses) == movies[1]


def test_tonight_pick_helps_most_people_then_uses_release_order(monkeypatch) -> None:
    """Tonight's pick should maximize family progress and break ties by order."""
    movies = [
        (1, "Movie One", 2020, 1),
        (2, "Movie Two", 2021, 1),
        (3, "Movie Three", 2022, 1),
    ]
    monkeypatch.setattr(recommendations, "MOVIES", movies)
    statuses = {
        (1, 1): True,
        (2, 1): False,
        (1, 2): False,
        (2, 2): False,
        (1, 3): False,
        (2, 3): False,
    }

    movie, missing = recommendations.get_tonight_recommendation(
        USERS,
        statuses,
        today=date(2026, 9, 1),
    )

    assert movie == movies[1]
    assert missing == ["Steve", "Nisha"]


def test_tonight_pick_ignores_future_and_explicitly_unreleased(monkeypatch) -> None:
    """Future or explicitly unreleased catalog entries should not be suggested."""
    movies = [
        (1, "Released Movie", 2025, 1),
        (2, "Future Movie", 2027, 1),
        (3, "Avengers: Doomsday", 2026, 6),
    ]
    monkeypatch.setattr(recommendations, "MOVIES", movies)
    statuses = {}

    movie, _ = recommendations.get_tonight_recommendation(
        USERS,
        statuses,
        today=date(2026, 9, 1),
    )

    assert movie == movies[0]
