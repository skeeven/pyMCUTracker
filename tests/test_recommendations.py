"""Tests for family movie recommendation rules."""

from datetime import date

import services.recommendations as recommendations


USERS = [
    (1, "Steve", "steve@example.com", 1),
    (2, "Nisha", "nisha@example.com", 0),
]


def test_missing_member_names_returns_only_unwatched_members() -> None:
    statuses = {
        (1, 1): True,
        (2, 1): False,
    }

    missing = recommendations.get_missing_member_names(1, USERS, statuses)

    assert missing == ["Nisha"]


def test_next_family_movie_uses_watch_order() -> None:
    movies = [
        (1, "Movie One", 2020, 1),
        (2, "Movie Two", 2021, 1),
        (3, "Movie Three", 2022, 1),
    ]
    statuses = {
        (1, 1): True,
        (2, 1): True,
        (1, 2): True,
        (2, 2): False,
    }

    assert recommendations.get_next_family_movie(
        USERS,
        statuses,
        movies,
    ) == movies[1]


def test_tonight_pick_helps_most_people_then_uses_watch_order() -> None:
    movies = [
        (1, "Movie One", 2020, 1),
        (2, "Movie Two", 2021, 1),
        (3, "Movie Three", 2022, 1),
    ]
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
        movies=movies,
    )

    assert movie == movies[1]
    assert missing == ["Steve", "Nisha"]


def test_tonight_pick_ignores_future_and_explicitly_unreleased() -> None:
    movies = [
        (1, "Released Movie", 2025, 1),
        (2, "Future Movie", 2027, 1),
        (3, "Avengers: Doomsday", 2026, 6),
    ]
    statuses = {}

    movie, _ = recommendations.get_tonight_recommendation(
        USERS,
        statuses,
        today=date(2026, 9, 1),
        movies=movies,
    )

    assert movie == movies[0]
