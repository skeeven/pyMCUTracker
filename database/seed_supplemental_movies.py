"""One-time/idempotent loader for Mutant Legacy Doomsday supplemental movies."""

from database.connection import get_connection

SUPPLEMENTAL_MOVIES = [
    ("X-Men", 2000, "Mutant Legacy", "Fox X-Men Universe"),
    ("X2: X-Men United", 2003, "Mutant Legacy", "Fox X-Men Universe"),
    ("X-Men: The Last Stand", 2006, "Mutant Legacy", "Fox X-Men Universe"),
    ("X-Men Origins: Wolverine", 2009, "Mutant Legacy", "Fox X-Men Universe"),
    ("X-Men: First Class", 2011, "Mutant Legacy", "Fox X-Men Universe"),
    ("The Wolverine", 2013, "Mutant Legacy", "Fox X-Men Universe"),
    ("X-Men: Days of Future Past", 2014, "Mutant Legacy", "Fox X-Men Universe"),
    ("Deadpool", 2016, "Mutant Legacy", "Fox X-Men Universe"),
    ("X-Men: Apocalypse", 2016, "Mutant Legacy", "Fox X-Men Universe"),
    ("Logan", 2017, "Mutant Legacy", "Fox X-Men Universe"),
    ("Deadpool 2", 2018, "Mutant Legacy", "Fox X-Men Universe"),
    ("Dark Phoenix", 2019, "Mutant Legacy", "Fox X-Men Universe"),
    ("The New Mutants", 2020, "Mutant Legacy", "Fox X-Men Universe"),
]


def _validate_movie_schema(cursor) -> None:
    """Ensure the movie catalog migration has been applied before loading."""
    cursor.execute("PRAGMA table_info(movies)")
    columns = {str(row[1]) for row in cursor.fetchall()}
    required = {
        "id",
        "title",
        "release_year",
        "phase",
        "release_order",
        "release_date",
        "category",
        "universe",
        "is_core_mcu",
        "is_doomsday_relevant",
        "is_active",
        "notes",
    }
    missing = sorted(required - columns)
    if missing:
        raise RuntimeError(
            "The movies table is missing required columns: "
            + ", ".join(missing)
            + ". Apply the catalog migration before running this loader."
        )


def seed_supplemental_movies() -> tuple[int, int]:
    """Insert/update Mutant Legacy movies and place them first in watch order.

    The loader is safe to run repeatedly. Existing movie rows are reused by title,
    new rows receive IDs above the current maximum, and all non-supplemental
    movies retain their relative order after the supplemental block.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        _validate_movie_schema(cursor)

        cursor.execute(
            """
            SELECT id, title, release_order
            FROM movies
            ORDER BY release_order, id
            """
        )
        existing_rows = cursor.fetchall()
        existing_by_title = {str(row[1]): int(row[0]) for row in existing_rows}

        supplemental_titles = {movie[0] for movie in SUPPLEMENTAL_MOVIES}
        other_movie_ids = [
            int(row[0])
            for row in existing_rows
            if str(row[1]) not in supplemental_titles
        ]

        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
        next_id = int(cursor.fetchone()[0]) + 1

        inserted = 0
        updated = 0
        supplemental_ids = []

        # Move all existing order values out of the way before resequencing so
        # the UNIQUE constraint on release_order cannot collide mid-update.
        cursor.execute("UPDATE movies SET release_order = release_order + 10000")

        for title, release_year, category, universe in SUPPLEMENTAL_MOVIES:
            movie_id = existing_by_title.get(title)
            if movie_id is None:
                movie_id = next_id
                next_id += 1
                cursor.execute(
                    """
                    INSERT INTO movies (
                        id,
                        title,
                        release_year,
                        phase,
                        release_order,
                        release_date,
                        category,
                        universe,
                        is_core_mcu,
                        is_doomsday_relevant,
                        is_active,
                        notes
                    )
                    VALUES (?, ?, ?, 0, ?, NULL, ?, ?, 0, 1, 1, ?)
                    """,
                    (
                        movie_id,
                        title,
                        release_year,
                        20000 + movie_id,
                        category,
                        universe,
                        "Supplemental legacy title for the Road to Doomsday.",
                    ),
                )
                inserted += 1
            else:
                cursor.execute(
                    """
                    UPDATE movies
                    SET release_year = ?,
                        phase = 0,
                        category = ?,
                        universe = ?,
                        is_core_mcu = 0,
                        is_doomsday_relevant = 1,
                        is_active = 1,
                        notes = COALESCE(
                            NULLIF(notes, ''),
                            'Supplemental legacy title for the Road to Doomsday.'
                        )
                    WHERE id = ?
                    """,
                    (
                        release_year,
                        category,
                        universe,
                        movie_id,
                    ),
                )
                updated += 1

            supplemental_ids.append(movie_id)

        final_order = supplemental_ids + other_movie_ids
        for release_order, movie_id in enumerate(final_order, start=1):
            cursor.execute(
                "UPDATE movies SET release_order = ? WHERE id = ?",
                (release_order, movie_id),
            )

        connection.commit()
        return inserted, updated
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    added, refreshed = seed_supplemental_movies()
    print(
        "Supplemental movie load complete: "
        f"{added} inserted, {refreshed} refreshed."
    )
