"""Idempotent loader for Mutant Legacy Doomsday supplemental movies."""

from database.connection import get_connection

SUPPLEMENTAL_MOVIES = [
    ("X-Men", 2000, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("X2: X-Men United", 2003, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("X-Men: The Last Stand", 2006, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("X-Men Origins: Wolverine", 2009, "Mutant Legacy", "Fox X-Men Universe", "Optional"),
    ("X-Men: First Class", 2011, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("The Wolverine", 2013, "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("X-Men: Days of Future Past", 2014, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Deadpool", 2016, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("X-Men: Apocalypse", 2016, "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("Logan", 2017, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Deadpool 2", 2018, "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Dark Phoenix", 2019, "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("The New Mutants", 2020, "Mutant Legacy", "Fox X-Men Universe", "Optional"),
]

# Combined theatrical release order. This preserves the original audience journey
# while interleaving the Fox/X-Men legacy films with the MCU catalog.
MASTER_WATCH_ORDER = [
    "X-Men",
    "X2: X-Men United",
    "X-Men: The Last Stand",
    "Iron Man",
    "The Incredible Hulk",
    "X-Men Origins: Wolverine",
    "Iron Man 2",
    "Thor",
    "X-Men: First Class",
    "Captain America: The First Avenger",
    "The Avengers",
    "Iron Man 3",
    "The Wolverine",
    "Thor: The Dark World",
    "Captain America: The Winter Soldier",
    "X-Men: Days of Future Past",
    "Guardians of the Galaxy",
    "Avengers: Age of Ultron",
    "Ant-Man",
    "Deadpool",
    "Captain America: Civil War",
    "X-Men: Apocalypse",
    "Doctor Strange",
    "Logan",
    "Guardians of the Galaxy Vol. 2",
    "Spider-Man: Homecoming",
    "Thor: Ragnarok",
    "Black Panther",
    "Avengers: Infinity War",
    "Deadpool 2",
    "Ant-Man and the Wasp",
    "Captain Marvel",
    "Avengers: Endgame",
    "Dark Phoenix",
    "Spider-Man: Far From Home",
    "The New Mutants",
    "Black Widow",
    "Shang-Chi and the Legend of the Ten Rings",
    "Eternals",
    "Spider-Man: No Way Home",
    "Doctor Strange in the Multiverse of Madness",
    "Thor: Love and Thunder",
    "Black Panther: Wakanda Forever",
    "Ant-Man and the Wasp: Quantumania",
    "Guardians of the Galaxy Vol. 3",
    "The Marvels",
    "Deadpool & Wolverine",
    "Captain America: Brave New World",
    "Thunderbolts* / The New Avengers",
    "The Fantastic Four: First Steps",
    "Spider-Man: Brand New Day",
    "Avengers: Doomsday",
    "Avengers: Secret Wars",
]


def _validate_movie_schema(cursor) -> None:
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
        "doomsday_priority",
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
    """Insert/update Mutant Legacy movies and apply the master watch order."""
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

        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
        next_id = int(cursor.fetchone()[0]) + 1

        inserted = 0
        updated = 0

        # Move all current watch-order values out of the way so resequencing
        # cannot collide with the UNIQUE constraint on release_order.
        cursor.execute("UPDATE movies SET release_order = release_order + 10000")

        for title, release_year, category, universe, priority in SUPPLEMENTAL_MOVIES:
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
                        doomsday_priority,
                        is_active,
                        notes
                    )
                    VALUES (?, ?, ?, 0, ?, NULL, ?, ?, 0, 1, ?, 1, ?)
                    """,
                    (
                        movie_id,
                        title,
                        release_year,
                        20000 + movie_id,
                        category,
                        universe,
                        priority,
                        "Supplemental legacy title for the Road to Doomsday.",
                    ),
                )
                existing_by_title[title] = movie_id
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
                        doomsday_priority = ?,
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
                        priority,
                        movie_id,
                    ),
                )
                updated += 1

        master_titles = set(MASTER_WATCH_ORDER)
        master_movie_ids = [
            existing_by_title[title]
            for title in MASTER_WATCH_ORDER
            if title in existing_by_title
        ]
        extra_movie_ids = [
            int(row[0])
            for row in existing_rows
            if str(row[1]) not in master_titles
        ]

        final_order = master_movie_ids + extra_movie_ids
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
