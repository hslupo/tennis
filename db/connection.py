import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
SCHEMA_VERSION = 2


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
    conn.commit()


def migrate(conn: sqlite3.Connection) -> None:
    """Bringt eine bereits bestehende Datenbank inkrementell auf SCHEMA_VERSION,
    ohne bestehende Daten anzufassen (create_schema läuft nur bei brandneuer DB)."""
    version_row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
    version = version_row["v"] if version_row and version_row["v"] is not None else 0

    if version < 2:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS spielt_bestaetigt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                termin_id INTEGER NOT NULL REFERENCES termin(id) ON DELETE CASCADE,
                spieler_id INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
                UNIQUE (termin_id, spieler_id)
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spielt_bestaetigt_termin ON spielt_bestaetigt(termin_id)"
        )

    if version < SCHEMA_VERSION:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
