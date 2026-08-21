PRAGMA foreign_keys = ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE saison (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jahr INTEGER NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL
);

-- wochentag: 0=Montag .. 6=Sonntag (Python date.weekday())
CREATE TABLE gruppe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    saison_id INTEGER NOT NULL REFERENCES saison(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    wochentag INTEGER NOT NULL CHECK (wochentag BETWEEN 0 AND 6),
    platz TEXT NOT NULL,
    startzeit TEXT NOT NULL,
    endzeit TEXT NOT NULL,
    seed INTEGER
);

CREATE TABLE spieler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    telefon TEXT NOT NULL DEFAULT '',
    mobil TEXT NOT NULL DEFAULT ''
);

CREATE TABLE gruppen_mitglied (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gruppe_id INTEGER NOT NULL REFERENCES gruppe(id) ON DELETE CASCADE,
    spieler_id INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
    UNIQUE (gruppe_id, spieler_id)
);

CREATE TABLE termin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gruppe_id INTEGER NOT NULL REFERENCES gruppe(id) ON DELETE CASCADE,
    datum TEXT NOT NULL,
    UNIQUE (gruppe_id, datum)
);

CREATE TABLE nicht_verfuegbar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termin_id INTEGER NOT NULL REFERENCES termin(id) ON DELETE CASCADE,
    spieler_id INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
    UNIQUE (termin_id, spieler_id)
);

CREATE TABLE verteilung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termin_id INTEGER NOT NULL REFERENCES termin(id) ON DELETE CASCADE,
    spieler_id INTEGER NOT NULL REFERENCES spieler(id) ON DELETE CASCADE,
    UNIQUE (termin_id, spieler_id)
);

CREATE INDEX idx_gruppe_saison ON gruppe(saison_id);
CREATE INDEX idx_gruppen_mitglied_gruppe ON gruppen_mitglied(gruppe_id);
CREATE INDEX idx_termin_gruppe ON termin(gruppe_id);
CREATE INDEX idx_nicht_verfuegbar_termin ON nicht_verfuegbar(termin_id);
CREATE INDEX idx_verteilung_termin ON verteilung(termin_id);
