"""Seed MCU/Marvel television series without changing existing movie IDs."""

from database.connection import get_connection

SERIES = [
    ("Agents of S.H.I.E.L.D.", 2013, 2020, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Agent Carter", 2015, 2016, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Daredevil (TV Series)", 2015, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Jessica Jones", 2015, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Luke Cage", 2016, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Iron Fist", 2017, 2018, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("The Defenders", 2017, 2017, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("The Punisher (TV Series)", 2017, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Runaways", 2017, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("Cloak & Dagger", 2018, 2019, "Marvel Television", "Marvel Cinematic Universe", 0),
    ("WandaVision", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("The Falcon and the Winter Soldier", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Loki", 2021, 2023, "MCU Television", "Marvel Cinematic Universe", 1),
    ("What If...?", 2021, 2024, "MCU Animation", "Marvel Cinematic Universe", 1),
    ("Hawkeye", 2021, 2021, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Moon Knight", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Ms. Marvel", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("She-Hulk: Attorney at Law", 2022, 2022, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Secret Invasion", 2023, 2023, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Echo", 2024, 2024, "MCU Television", "Marvel Cinematic Universe", 1),
    ("X-Men '97", 2024, None, "Marvel Animation", "X-Men Animated Universe", 0),
    ("Agatha All Along", 2024, 2024, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Your Friendly Neighborhood Spider-Man", 2025, None, "Marvel Animation", "Marvel Multiverse", 0),
    ("Daredevil: Born Again", 2025, None, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Ironheart", 2025, 2025, "MCU Television", "Marvel Cinematic Universe", 1),
    ("Eyes of Wakanda", 2025, 2025, "MCU Animation", "Marvel Cinematic Universe", 1),
    ("Marvel Zombies", 2025, 2025, "MCU Animation", "Marvel Multiverse", 0),
    ("Wonder Man", 2026, 2026, "MCU Television", "Marvel Cinematic Universe", 1),
]


def seed_tv_series() -> int:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title, media_type FROM movies")
        existing = {(str(r[1]), str(r[2])): int(r[0]) for r in cursor.fetchall()}
        cursor.execute("SELECT COALESCE(MAX(id), 0) FROM movies")
        next_id = int(cursor.fetchone()[0]) + 1
        cursor.execute("SELECT COALESCE(MAX(release_order), 0) FROM movies")
        next_order = int(cursor.fetchone()[0]) + 1
        inserted = 0

        for title, start_year, end_year, category, universe, core_mcu in SERIES:
            if (title, "tv") in existing:
                continue
            cursor.execute(
                """
                INSERT INTO movies (
                    id, title, release_year, phase, release_order, category,
                    universe, is_core_mcu, is_doomsday_relevant,
                    doomsday_priority, is_active, notes, media_type, end_year
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, 0, 'Recommended', 1, ?, 'tv', ?)
                """,
                (
                    next_id, title, start_year, next_order, category, universe,
                    core_mcu, "Marvel television series.", end_year,
                ),
            )
            next_id += 1
            next_order += 1
            inserted += 1

        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    count = seed_tv_series()
    print(f"TV-series seed complete: {count} inserted.")
