"""Phase 2 - SQLite database layer (OOP) with Country Name as the natural primary key."""

import sqlite3
from contextlib import contextmanager

DEFAULT_DB_PATH = "countries.db"


class CountryDatabaseManager:
    """Handles all CRUD operations on the `countries` table."""

    UPDATABLE_FIELDS = ("capital", "population", "area")

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.create_table()

    @contextmanager
    def _connect(self):
        """Open a short-lived connection per operation (safe to use from FastAPI threads)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_table(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS countries (
                    country_name TEXT PRIMARY KEY COLLATE NOCASE,
                    capital      TEXT    NOT NULL,
                    population   INTEGER NOT NULL CHECK (population >= 0),
                    area         REAL    NOT NULL CHECK (area >= 0)
                )
                """
            )

    # ---------- CREATE ----------
    def create_country(self, country_name: str, capital: str, population: int, area: float) -> bool:
        """Insert a new country. Returns False if a country with that name already exists."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO countries (country_name, capital, population, area) VALUES (?, ?, ?, ?)",
                    (country_name, capital, population, area),
                )
            return True
        except sqlite3.IntegrityError as exc:
            if "UNIQUE" in str(exc):
                return False
            raise

    def upsert_many(self, countries: list[dict]) -> int:
        """Insert or refresh many countries at once (used by the scraper so re-runs are safe)."""
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO countries (country_name, capital, population, area)
                VALUES (:country_name, :capital, :population, :area)
                ON CONFLICT(country_name) DO UPDATE SET
                    capital = excluded.capital,
                    population = excluded.population,
                    area = excluded.area
                """,
                countries,
            )
        return len(countries)

    # ---------- READ ----------
    def get_all_countries(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT country_name, capital, population, area FROM countries ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_country(self, country_name: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT country_name, capital, population, area FROM countries WHERE country_name = ?",
                (country_name,),
            ).fetchone()
        return dict(row) if row else None

    # ---------- UPDATE ----------
    def update_country(self, country_name: str, **fields) -> bool:
        """Update capital/population/area of an existing country. Returns False if not found."""
        updates = {key: value for key, value in fields.items() if key in self.UPDATABLE_FIELDS}
        if not updates:
            raise ValueError(f"Nothing to update. Allowed fields: {', '.join(self.UPDATABLE_FIELDS)}")

        # Column names come from the whitelist above, values are bound as parameters.
        set_clause = ", ".join(f"{column} = ?" for column in updates)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE countries SET {set_clause} WHERE country_name = ?",
                (*updates.values(), country_name),
            )
            return cursor.rowcount > 0

    # ---------- DELETE ----------
    def delete_country(self, country_name: str) -> bool:
        """Delete a country by name. Returns False if not found."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM countries WHERE country_name = ?", (country_name,))
            return cursor.rowcount > 0
