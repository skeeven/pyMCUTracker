"""Idempotently expand the tracker into a broad Marvel theatrical catalog.

Preserves existing movie IDs and user watch history. New titles are inserted only
when absent. Global catalog order is theatrical release order; individual watch
paths can define their own order independently.
"""

from database.connection import get_connection

LEGACY_MOVIES = [
    ("Howard the Duck", 1986, "1986-08-01", "Marvel Legacy", "Standalone Marvel", "Optional"),
    ("Blade", 1998, "1998-08-21", "Marvel Legacy", "Blade Trilogy", "Recommended"),
    ("X-Men", 2000, "2000-07-14", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Blade II", 2002, "2002-03-22", "Marvel Legacy", "Blade Trilogy", "Recommended"),
    ("Spider-Man", 2002, "2002-05-03", "Sony Spider-Man", "Raimi Spider-Man Universe", "Essential"),
    ("Daredevil", 2003, "2003-02-14", "Marvel Legacy", "Fox Marvel Legacy", "Recommended"),
    ("X2: X-Men United", 2003, "2003-05-02", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Hulk", 2003, "2003-06-20", "Marvel Legacy", "Universal Hulk", "Optional"),
    ("The Punisher", 2004, "2004-04-16", "Marvel Legacy", "Punisher Legacy", "Recommended"),
    ("Spider-Man 2", 2004, "2004-06-30", "Sony Spider-Man", "Raimi Spider-Man Universe", "Essential"),
    ("Blade: Trinity", 2004, "2004-12-08", "Marvel Legacy", "Blade Trilogy", "Recommended"),
    ("Elektra", 2005, "2005-01-14", "Marvel Legacy", "Fox Marvel Legacy", "Optional"),
    ("Fantastic Four", 2005, "2005-07-08", "Fantastic Four Legacy", "Fox Fantastic Four", "Recommended"),
    ("X-Men: The Last Stand", 2006, "2006-05-26", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Ghost Rider", 2007, "2007-02-16", "Marvel Legacy", "Ghost Rider Legacy", "Recommended"),
    ("Spider-Man 3", 2007, "2007-05-04", "Sony Spider-Man", "Raimi Spider-Man Universe", "Essential"),
    ("Fantastic Four: Rise of the Silver Surfer", 2007, "2007-06-15", "Fantastic Four Legacy", "Fox Fantastic Four", "Recommended"),
    ("Punisher: War Zone", 2008, "2008-12-05", "Marvel Legacy", "Punisher Legacy", "Optional"),
    ("X-Men Origins: Wolverine", 2009, "2009-05-01", "Mutant Legacy", "Fox X-Men Universe", "Optional"),
    ("X-Men: First Class", 2011, "2011-06-03", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Ghost Rider: Spirit of Vengeance", 2012, "2012-02-17", "Marvel Legacy", "Ghost Rider Legacy", "Optional"),
    ("The Amazing Spider-Man", 2012, "2012-07-03", "Sony Spider-Man", "Amazing Spider-Man Universe", "Essential"),
    ("The Wolverine", 2013, "2013-07-26", "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("The Amazing Spider-Man 2", 2014, "2014-05-02", "Sony Spider-Man", "Amazing Spider-Man Universe", "Essential"),
    ("X-Men: Days of Future Past", 2014, "2014-05-23", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Fantastic Four (2015)", 2015, "2015-08-07", "Fantastic Four Legacy", "Fox Fantastic Four Reboot", "Optional"),
    ("Deadpool", 2016, "2016-02-12", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("X-Men: Apocalypse", 2016, "2016-05-27", "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("Logan", 2017, "2017-03-03", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Deadpool 2", 2018, "2018-05-18", "Mutant Legacy", "Fox X-Men Universe", "Essential"),
    ("Venom", 2018, "2018-10-05", "Sony Spider-Man", "Sony's Spider-Man Universe", "Recommended"),
    ("Spider-Man: Into the Spider-Verse", 2018, "2018-12-14", "Sony Spider-Man", "Spider-Verse", "Recommended"),
    ("Dark Phoenix", 2019, "2019-06-07", "Mutant Legacy", "Fox X-Men Universe", "Recommended"),
    ("The New Mutants", 2020, "2020-08-28", "Mutant Legacy", "Fox X-Men Universe", "Optional"),
    ("Venom: Let There Be Carnage", 2021, "2021-10-01", "Sony Spider-Man", "Sony's Spider-Man Universe", "Recommended"),
    ("Morbius", 2022, "2022-04-01", "Sony Spider-Man", "Sony's Spider-Man Universe", "Optional"),
    ("Spider-Man: Across the Spider-Verse", 2023, "2023-06-02", "Sony Spider-Man", "Spider-Verse", "Recommended"),
    ("Madame Web", 2024, "2024-02-14", "Sony Spider-Man", "Sony's Spider-Man Universe", "Optional"),
    ("Venom: The Last Dance", 2024, "2024-10-25", "Sony Spider-Man", "Sony's Spider-Man Universe", "Recommended"),
    ("Kraven the Hunter", 2024, "2024-12-13", "Sony Spider-Man", "Sony's Spider-Man Universe", "Optional"),
]


def seed_marvel_catalog() -> tuple[int, int]:
    """Insert missing legacy titles and resequence the catalog by release date."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title FROM movies")
        existing = {str(row[1]): int(row[0]) for row in cursor.fetchall()}
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
        next_id = int(cursor.fetchone()[0]) + 1
        inserted = 0
        refreshed = 0

        cursor.execute("UPDATE movies SET release_order = release_order + 10000")

        for title, year, release_date, category, universe, priority in LEGACY_MOVIES:
            movie_id = existing.get(title)
            if movie_id is None:
                movie_id = next_id
                next_id += 1
                cursor.execute(
                    """
                    INSERT INTO movies (
                        id, title, release_year, phase, release_order, release_date,
                        category, universe, is_core_mcu, is_doomsday_relevant,
                        doomsday_priority, is_active, notes
                    ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, 0, 0, ?, 1, ?)
                    """,
                    (
                        movie_id, title, year, 20000 + movie_id, release_date,
                        category, universe, priority,
                        "Legacy Marvel theatrical title.",
                    ),
                )
                existing[title] = movie_id
                inserted += 1
            else:
                cursor.execute(
                    """
                    UPDATE movies
                    SET release_year = ?, release_date = ?, category = ?,
                        universe = ?, is_active = 1
                    WHERE id = ?
                    """,
                    (year, release_date, category, universe, movie_id),
                )
                refreshed += 1

        cursor.execute(
            """
            SELECT id, release_date, release_year, title
            FROM movies
            ORDER BY
                CASE WHEN release_date IS NULL OR release_date = '' THEN 1 ELSE 0 END,
                release_date,
                release_year,
                id
            """
        )
        ordered = cursor.fetchall()
        for order, row in enumerate(ordered, start=1):
            cursor.execute(
                "UPDATE movies SET release_order = ? WHERE id = ?",
                (order, int(row[0])),
            )

        # Every active catalog title belongs to Marvel Completionist.
        cursor.execute(
            "SELECT id FROM watch_paths WHERE slug = 'marvel-completionist'"
        )
        path = cursor.fetchone()
        if path:
            path_id = int(path[0])
            cursor.execute(
                "DELETE FROM watch_path_movies WHERE watch_path_id = ?",
                (path_id,),
            )
            cursor.execute(
                "SELECT id, release_order FROM movies WHERE is_active = 1 ORDER BY release_order"
            )
            for movie_id, order in cursor.fetchall():
                cursor.execute(
                    """
                    INSERT INTO watch_path_movies (
                        watch_path_id, movie_id, priority, watch_order
                    ) VALUES (?, ?, 'Essential', ?)
                    """,
                    (path_id, movie_id, order),
                )

        connection.commit()
        return inserted, refreshed
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    added, updated = seed_marvel_catalog()
    print(f"Marvel catalog expansion complete: {added} inserted, {updated} refreshed.")
