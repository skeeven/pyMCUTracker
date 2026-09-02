"""Recommendation helpers for family movie progress."""

from collections.abc import Iterable
from datetime import date

from database.movies import get_active_movies


UNRELEASED_TITLES = {
    "Avengers: Doomsday",
    "Avengers: Secret Wars",
}


def get_missing_member_names(
    movie_id: int,
    users: Iterable[tuple],
    statuses: dict[tuple[int, int], bool],
) -> list[str]:
    """Return active family member names who have not watched a movie."""
    missing = []
    for user in users:
        user_id = int(user[0])
        name = str(user[1])
        if not statuses.get((user_id, movie_id), False):
            missing.append(name)
    return missing


def get_next_family_movie(
    users: Iterable[tuple],
    statuses: dict[tuple[int, int], bool],
    movies: Iterable[tuple] | None = None,
):
    """Return earliest watch-order movie not watched by every member."""
    movie_list = list(movies) if movies is not None else list(get_active_movies())
    user_list = list(users)
    if not user_list:
        return movie_list[0] if movie_list else None

    user_ids = [int(user[0]) for user in user_list]
    for movie in movie_list:
        movie_id = int(movie[0])
        if not all(
            statuses.get((user_id, movie_id), False)
            for user_id in user_ids
        ):
            return movie
    return None


def get_tonight_recommendation(
    users: Iterable[tuple],
    statuses: dict[tuple[int, int], bool],
    today: date | None = None,
    movies: Iterable[tuple] | None = None,
):
    """Return a released movie that advances the most family members at once."""
    movie_list = list(movies) if movies is not None else list(get_active_movies())
    user_list = list(users)
    if not user_list:
        return None

    current_date = today or date.today()
    candidates = []

    for movie in movie_list:
        movie_id, title, release_year, _ = movie
        if release_year is None:
            continue
        if int(release_year) > current_date.year:
            continue
        if title in UNRELEASED_TITLES:
            continue

        missing = get_missing_member_names(
            int(movie_id),
            user_list,
            statuses,
        )
        if not missing:
            continue

        candidates.append((len(missing), int(movie_id), movie, missing))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (-item[0], item[1]))
    _, _, movie, missing = candidates[0]
    return movie, missing
