"""Small TMDB API client used only by administrator refresh actions."""

import json
import os
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from database.media_metadata import upsert_metadata
from database.movies import get_all_movies

API_ROOT = "https://api.themoviedb.org/3"

TV_SEARCH_ALIASES = {
    "Daredevil (TV Series)": "Daredevil",
    "The Punisher (TV Series)": "The Punisher",
}


class TMDBError(RuntimeError):
    """Friendly TMDB connectivity/authentication error."""


def test_connection() -> str:
    """Validate credentials before starting a full library refresh."""
    try:
        data = _get("/configuration")
        if not data.get("images"):
            raise TMDBError("TMDB connected, but returned an unexpected response.")
        return "Connected to TMDB."
    except TMDBError:
        raise
    except Exception as exc:
        raise TMDBError(f"Unable to connect to TMDB: {exc}") from exc


def _token() -> str:
    token = os.getenv("TMDB_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TMDB_ACCESS_TOKEN is not configured.")
    return token


def _get(path: str) -> dict:
    request = Request(
        API_ROOT + path,
        headers={
            "Authorization": f"Bearer {_token()}",
            "accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 401:
            raise TMDBError(
                "TMDB rejected the access token (401 Unauthorized). "
                "Check TMDB_ACCESS_TOKEN in this environment."
            ) from exc
        if exc.code == 403:
            raise TMDBError(
                "TMDB denied access (403 Forbidden). Check the token permissions."
            ) from exc
        raise TMDBError(f"TMDB returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise TMDBError(f"Network error contacting TMDB: {exc.reason}") from exc
    except TimeoutError as exc:
        raise TMDBError("TMDB connection timed out.") from exc


def _normalize_title(value: str) -> str:
    """Normalize a title for conservative TMDB result matching."""
    return "".join(character.casefold() for character in value if character.isalnum())


def _result_year(result: dict, media_type: str) -> int | None:
    date_key = "first_air_date" if media_type == "tv" else "release_date"
    value = str(result.get(date_key) or "")
    if len(value) >= 4 and value[:4].isdigit():
        return int(value[:4])
    return None


def _best_result(
    title: str,
    year: int | None,
    media_type: str = "movie",
) -> dict | None:
    query = quote(title)
    endpoint = "tv" if media_type == "tv" else "movie"
    year_param = "first_air_date_year" if media_type == "tv" else "year"
    title_key = "name" if media_type == "tv" else "title"
    original_key = "original_name" if media_type == "tv" else "original_title"
    base_path = (
        f"/search/{endpoint}?query={query}&include_adult=false&language=en-US"
    )
    path = base_path
    if year:
        path += f"&{year_param}={year}"

    results = _get(path).get("results", [])
    if not results and year:
        results = _get(base_path).get("results", [])
    if not results:
        return None

    wanted = _normalize_title(title)
    exact_title = [
        result for result in results
        if wanted in {
            _normalize_title(str(result.get(title_key) or "")),
            _normalize_title(str(result.get(original_key) or "")),
        }
    ]
    if year:
        exact_title_and_year = [
            result for result in exact_title
            if _result_year(result, media_type) == year
        ]
        if exact_title_and_year:
            return max(
                exact_title_and_year,
                key=lambda result: int(result.get("vote_count") or 0),
            )
    if exact_title:
        return max(
            exact_title,
            key=lambda result: int(result.get("vote_count") or 0),
        )

    # Do not silently cache a similarly named title. Ambiguous entries should
    # be reported as unmatched so they can be given an explicit alias/ID.
    return None


def refresh_movie(movie_id: int, title: str, year: int | None) -> bool:
    match = _best_result(title, year)
    if not match:
        return False

    tmdb_id = int(match["id"])
    detail = _get(
        f"/movie/{tmdb_id}?language=en-US&append_to_response="
        "credits,videos,release_dates,external_ids"
    )
    crew = detail.get("credits", {}).get("crew", [])
    director = next(
        (person.get("name") for person in crew if person.get("job") == "Director"),
        None,
    )
    cast = detail.get("credits", {}).get("cast", [])[:8]
    cast_names = ", ".join(
        f"{person.get('name')} as {person.get('character')}"
        if person.get("character") else str(person.get("name"))
        for person in cast
    )

    trailer = next(
        (
            video for video in detail.get("videos", {}).get("results", [])
            if video.get("site") == "YouTube"
            and video.get("type") == "Trailer"
            and video.get("official")
        ),
        None,
    )
    if trailer is None:
        trailer = next(
            (
                video for video in detail.get("videos", {}).get("results", [])
                if video.get("site") == "YouTube"
                and video.get("type") == "Trailer"
            ),
            None,
        )

    certification = None
    for country in detail.get("release_dates", {}).get("results", []):
        if country.get("iso_3166_1") == "US":
            certification = next(
                (
                    release.get("certification")
                    for release in country.get("release_dates", [])
                    if release.get("certification")
                ),
                None,
            )
            break

    values = {
        "media_type": "movie",
        "tmdb_id": tmdb_id,
        "imdb_id": detail.get("external_ids", {}).get("imdb_id"),
        "overview": detail.get("overview"),
        "tagline": detail.get("tagline"),
        "poster_path": detail.get("poster_path"),
        "backdrop_path": detail.get("backdrop_path"),
        "runtime_minutes": detail.get("runtime"),
        "genres": ", ".join(g.get("name", "") for g in detail.get("genres", [])),
        "content_rating": certification,
        "tmdb_rating": detail.get("vote_average"),
        "tmdb_vote_count": detail.get("vote_count"),
        "director": director,
        "cast_names": cast_names,
        "trailer_key": trailer.get("key") if trailer else None,
        "trailer_name": trailer.get("name") if trailer else None,
        "homepage": detail.get("homepage"),
    }
    upsert_metadata(movie_id, values)
    return True


def refresh_tv_series(movie_id: int, title: str, year: int | None) -> bool:
    search_title = TV_SEARCH_ALIASES.get(title, title)
    if search_title.endswith(" (TV Series)"):
        search_title = search_title[:-12]
    match = _best_result(search_title, year, "tv")
    if not match:
        return False
    tmdb_id = int(match["id"])
    detail = _get(
        f"/tv/{tmdb_id}?language=en-US&append_to_response="
        "aggregate_credits,videos,content_ratings,external_ids"
    )
    creators = ", ".join(
        person.get("name", "") for person in detail.get("created_by", [])
    )
    cast = detail.get("aggregate_credits", {}).get("cast", [])[:8]
    cast_names = ", ".join(str(person.get("name")) for person in cast)
    trailer = next(
        (
            video for video in detail.get("videos", {}).get("results", [])
            if video.get("site") == "YouTube"
            and video.get("type") == "Trailer"
            and video.get("official")
        ),
        None,
    )
    rating = next(
        (
            item.get("rating")
            for item in detail.get("content_ratings", {}).get("results", [])
            if item.get("iso_3166_1") == "US"
        ),
        None,
    )
    runtimes = detail.get("episode_run_time", [])
    values = {
        "media_type": "tv",
        "tmdb_id": tmdb_id,
        "imdb_id": detail.get("external_ids", {}).get("imdb_id"),
        "overview": detail.get("overview"),
        "tagline": detail.get("tagline"),
        "poster_path": detail.get("poster_path"),
        "backdrop_path": detail.get("backdrop_path"),
        "runtime_minutes": runtimes[0] if runtimes else None,
        "genres": ", ".join(g.get("name", "") for g in detail.get("genres", [])),
        "content_rating": rating,
        "tmdb_rating": detail.get("vote_average"),
        "tmdb_vote_count": detail.get("vote_count"),
        "director": creators or None,
        "cast_names": cast_names,
        "trailer_key": trailer.get("key") if trailer else None,
        "trailer_name": trailer.get("name") if trailer else None,
        "homepage": detail.get("homepage"),
        "season_count": detail.get("number_of_seasons"),
        "episode_count": detail.get("number_of_episodes"),
        "status": detail.get("status"),
        "first_air_date": detail.get("first_air_date"),
        "last_air_date": detail.get("last_air_date"),
    }
    upsert_metadata(movie_id, values)
    return True


def refresh_library(progress_callback=None) -> dict:
    """Refresh active titles and retain useful diagnostics for the UI."""
    active = [movie for movie in get_all_movies() if bool(movie[10])]
    total = len(active)
    refreshed = 0
    unmatched = []
    failed = []

    for index, movie in enumerate(active, start=1):
        movie_id, title, year = int(movie[0]), str(movie[1]), movie[2]
        media_type = str(movie[12]) if len(movie) > 12 else "movie"
        if progress_callback:
            progress_callback(index, total, title, "retrieving")
        try:
            refresh_fn = refresh_tv_series if media_type == "tv" else refresh_movie
            matched = refresh_fn(
                movie_id, title, int(year) if year else None
            )
            if matched:
                refreshed += 1
                if progress_callback:
                    progress_callback(index, total, title, "saved")
            else:
                unmatched.append(title)
                if progress_callback:
                    progress_callback(index, total, title, "unmatched")
        except TMDBError:
            raise
        except Exception as exc:
            failed.append((title, str(exc)))
            if progress_callback:
                progress_callback(index, total, title, "failed")

    return {
        "total": total,
        "refreshed": refreshed,
        "unmatched": unmatched,
        "failed": failed,
    }
