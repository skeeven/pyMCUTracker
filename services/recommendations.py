"""Recommendation helpers for family movie progress."""

from collections.abc import Iterable
from datetime import date

from data.movies import MOVIES


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
):
    """Return earliest release-order movie not watched by every member."""
    user_list = list(users)
    if not user_list:
        return MOVIES[0] if MOVIES else None

    user_ids = [int(user[0]) for user in user_list]
    for movie in MOVIES:
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
):
    """Return a movie that advances the most family members at once.

    Candidates must have a known release year no later than the current year
    and must not be explicitly marked as unreleased. Ties are broken by the
    catalog's release order.
    """
    user_list = list(users)
    if not user_list:
        return None

    current_date = today or date.today()
    candidates = []

    for movie in MOVIES:
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
