"""Idempotently seed MCU/Marvel television series without changing movie IDs."""

from database.connection import get_connection

# catalog title, TMDB search title, start year, end year, category, universe, core MCU
SERIES = [
    ("Agents of S.H.I.E.L.D.", "Agents of S.H.I.E.L.D.", 2013, 2020, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Agent Carter", "Agent Carter", 2015, 2016, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Daredevil (TV Series)", "Daredevil", 2015, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Jessica Jones", "Jessica Jones", 2015, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Luke Cage", "Luke Cage", 2016, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Iron Fist", "Iron Fist", 2017, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("The Defenders", "The Defenders", 2017, 2017, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("The Punisher (TV Series)", "The Punisher", 2017, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Runaways", "Runaways", 2017, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Cloak & Dagger", "Cloak & Dagger", 2018, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("WandaVision", "WandaVision", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("The Falcon and the Winter Soldier", "The Falcon and the Winter Soldier", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Loki", "Loki", 2021, 2023, "MCU Television", "Marvel Cinematic Universe", 1),
    ("What If...?", "What If...?", 2021, 2024, "MCU Animation", "Marvel Cinematic Universe", 1),
    ("Hawkeye", "Hawkeye", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Moon Knight", "Moon Knight", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Ms. Marvel", "Ms. Marvel", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("She-Hulk: Attorney at Law", "She-Hulk: Attorney at Law", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Secret Invasion", "Secret Invasion", 2023, 2023, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Echo (TV Series)", "Echo", 2024, 2024, "MCU Television", "Marvel Cinematic Universe", 1),
    ("X-Men '97", "X-Men '97", 2024, None, "Marvel Animation", "X-Men Animated Universe", 0),
    ("Agatha All Along", "Agatha All Along", 2024, 2024, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Your Friendly Neighborhood Spider-Man", "Your Friendly Neighborhood Spider-Man", 2025, None, "Marvel Animation", "Marvel Multiverse", 0),
    ("Daredevil: Born Again", "Daredevil: Born Again", 2025, None, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Ironheart", "Ironheart", 2025, 2025, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Eyes of Wakanda", "Eyes of Wakanda", 2025, 2025, "MCU Animation", "Marvel Cinematic Universe", 1),
    ("Marvel Zombies", "Marvel Zombies", 2025, 2025, "MCU Animation", "Marvel Multiverse", 0),
    ("Wonder Man", "Wonder Man", 2026, 2026, "MCU Television", "Marvel Cinematic Universe", 1),
]


def seed_tv_series() -> tuple[int, int, list[str]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title, media_type FROM movies")
        rows = cursor.fetchall()
        existing_by_title = {
            str(row[1]).casefold(): (int(row[0]), str(row[2] or "movie"))
            for row in rows
        }

        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
        next_id = int(cursor.fetchone()[0]) + 1
        cursor.execute("SELECT COALESCE(MAX(release_order), 0) FROM movies")
        next_order = int(cursor.fetchone()[0]) + 1

        inserted = 0
        existing_tv = 0
        collisions = []

        for (
            catalog_title, search_title, start_year, end_year,
            category, universe, core_mcu,
        ) in SERIES:
            key = catalog_title.casefold()
            existing = existing_by_title.get(key)

            if existing:
                existing_id, existing_type = existing
                if existing_type == "tv":
                    cursor.execute(
                        """
                        UPDATE movies
                        SET release_year = ?, end_year = ?, category = ?,
                            universe = ?, is_core_mcu = ?, is_active = 1,
                            notes = ?
                        WHERE id = ?
                        """,
                        (
                            start_year, end_year, category, universe, core_mcu,
                            f"Marvel television series. TMDB search: {search_title}",
                            existing_id,
                        ),
                    )
                    existing_tv += 1
                    continue

                # A movie or legacy record already owns this globally unique title.
                # Generate a deterministic TV-specific catalog title.
                base_title = catalog_title
                if not base_title.endswith("(TV Series)"):
                    base_title = f"{base_title} (TV Series)"
                candidate = base_title
                suffix = 2
                while candidate.casefold() in existing_by_title:
                    candidate = f"{base_title} {suffix}"
                    suffix += 1
                collisions.append(f"{catalog_title} -> {candidate}")
                catalog_title = candidate
                key = catalog_title.casefold()

            cursor.execute(
                """
                INSERT INTO movies (
                    id, title, release_year, phase, release_order, category,
                    universe, is_core_mcu, is_doomsday_relevant,
                    doomsday_priority, is_active, notes, media_type, end_year
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, 0, 'Recommended', 1, ?, 'tv', ?)
                """,
                (
                    next_id, catalog_title, start_year, next_order, category,
                    universe, core_mcu,
                    f"Marvel television series. TMDB search: {search_title}",
                    end_year,
                ),
            )
            existing_by_title[key] = (next_id, "tv")
            next_id += 1
            next_order += 1
            inserted += 1

        connection.commit()
        return inserted, existing_tv, collisions
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    added, found, renamed = seed_tv_series()
    print(f"TV-series seed complete: {added} inserted, {found} already present.")
    if renamed:
        print("Automatically disambiguated title collisions:")
        for item in renamed:
            print(f"  - {item}")
