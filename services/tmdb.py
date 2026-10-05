"""Small TMDB API client used only by administrator refresh actions."""

import json
import os
from urllib.parse import quote
from urllib.request import Request, urlopen

from database.media_metadata import upsert_metadata
from database.movies import get_all_movies

API_ROOT = "https://api.themoviedb.org/3"


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
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _best_result(title: str, year: int | None) -> dict | None:
    query = quote(title)
    path = f"/search/movie?query={query}&include_adult=false&language=en-US"
    if year:
        path += f"&year={year}"
    results = _get(path).get("results", [])
    if not results and year:
        results = _get(
            f"/search/movie?query={query}&include_adult=false&language=en-US"
        ).get("results", [])
    return results[0] if results else None


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


def refresh_library() -> tuple[int, list[str]]:
    refreshed = 0
    missed = []
    for movie in get_all_movies():
        movie_id, title, year = int(movie[0]), str(movie[1]), movie[2]
        if not bool(movie[10]):
            continue
        try:
            if refresh_movie(movie_id, title, int(year) if year else None):
                refreshed += 1
            else:
                missed.append(title)
        except Exception:
            missed.append(title)
    return refreshed, missed
