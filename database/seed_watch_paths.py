"""Seed reusable Marvel watch paths after the expanded catalog is loaded."""

from database.connection import get_connection

PATHS = [
    (
        "spider-man",
        "Spider-Man Saga",
        "The live-action Spider-Man story across Tobey Maguire, Andrew Garfield, and the MCU.",
        30,
        [
            ("Spider-Man", "Essential"),
            ("Spider-Man 2", "Essential"),
            ("Spider-Man 3", "Essential"),
            ("The Amazing Spider-Man", "Essential"),
            ("The Amazing Spider-Man 2", "Essential"),
            ("Captain America: Civil War", "Recommended"),
            ("Spider-Man: Homecoming", "Essential"),
            ("Avengers: Infinity War", "Recommended"),
            ("Avengers: Endgame", "Recommended"),
            ("Spider-Man: Far From Home", "Essential"),
            ("Spider-Man: No Way Home", "Essential"),
            ("Spider-Man: Brand New Day", "Essential"),
        ],
    ),
    (
        "sony-spider-man-universe",
        "Sony Spider-Man Universe",
        "Venom and Sony's Spider-Man-adjacent live-action universe.",
        40,
        [
            ("Venom", "Essential"),
            ("Venom: Let There Be Carnage", "Essential"),
            ("Morbius", "Recommended"),
            ("Madame Web", "Optional"),
            ("Venom: The Last Dance", "Essential"),
            ("Kraven the Hunter", "Optional"),
        ],
    ),
    (
        "x-men",
        "X-Men / Mutant Legacy",
        "Fox X-Men, Wolverine, and Deadpool theatrical legacy.",
        50,
        [
            ("X-Men", "Essential"),
            ("X2: X-Men United", "Essential"),
            ("X-Men: The Last Stand", "Essential"),
            ("X-Men Origins: Wolverine", "Optional"),
            ("X-Men: First Class", "Essential"),
            ("The Wolverine", "Recommended"),
            ("X-Men: Days of Future Past", "Essential"),
            ("Deadpool", "Essential"),
            ("X-Men: Apocalypse", "Recommended"),
            ("Logan", "Essential"),
            ("Deadpool 2", "Essential"),
            ("Dark Phoenix", "Recommended"),
            ("The New Mutants", "Optional"),
            ("Deadpool & Wolverine", "Essential"),
        ],
    ),
    (
        "fantastic-four",
        "Fantastic Four",
        "Fantastic Four theatrical continuities leading into the MCU team.",
        60,
        [
            ("Fantastic Four", "Recommended"),
            ("Fantastic Four: Rise of the Silver Surfer", "Essential"),
            ("Fantastic Four (2015)", "Optional"),
            ("The Fantastic Four: First Steps", "Essential"),
        ],
    ),
    (
        "marvel-legacy",
        "Marvel Legacy",
        "Pre-MCU and standalone Marvel theatrical heroes.",
        70,
        [
            ("Howard the Duck", "Optional"),
            ("Blade", "Essential"),
            ("Blade II", "Essential"),
            ("Daredevil", "Recommended"),
            ("Hulk", "Optional"),
            ("The Punisher", "Recommended"),
            ("Blade: Trinity", "Essential"),
            ("Elektra", "Optional"),
            ("Ghost Rider", "Recommended"),
            ("Punisher: War Zone", "Optional"),
            ("Ghost Rider: Spirit of Vengeance", "Optional"),
        ],
    ),
    (
        "spider-verse",
        "Spider-Verse",
        "Miles Morales animated Spider-Verse films.",
        80,
        [
            ("Spider-Man: Into the Spider-Verse", "Essential"),
            ("Spider-Man: Across the Spider-Verse", "Essential"),
        ],
    ),
]


def seed_watch_paths() -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title FROM movies")
        movie_ids = {str(row[1]): int(row[0]) for row in cursor.fetchall()}

        for slug, name, description, sort_order, movies in PATHS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO watch_paths (
                    slug, name, description, is_active, sort_order
                ) VALUES (?, ?, ?, 1, ?)
                """,
                (slug, name, description, sort_order),
            )
            cursor.execute(
                """
                UPDATE watch_paths
                SET name = ?, description = ?, sort_order = ?, is_active = 1
                WHERE slug = ?
                """,
                (name, description, sort_order, slug),
            )
            cursor.execute("SELECT id FROM watch_paths WHERE slug = ?", (slug,))
            path_id = int(cursor.fetchone()[0])
            cursor.execute(
                "DELETE FROM watch_path_movies WHERE watch_path_id = ?",
                (path_id,),
            )

            order = 0
            for title, priority in movies:
                movie_id = movie_ids.get(title)
                if movie_id is None:
                    continue
                order += 1
                cursor.execute(
                    """
                    INSERT INTO watch_path_movies (
                        watch_path_id, movie_id, priority, watch_order
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (path_id, movie_id, priority, order),
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    seed_watch_paths()
    print("Marvel watch paths seeded.")
