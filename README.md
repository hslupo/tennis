# Tennis

Desktop-App zur Verwaltung von Tennisrunden mit Gruppen, Terminen, Verfugbarkeiten und Auswertung.

## Funktionen

- Saisonverwaltung (Start-/Enddatum)
- Gruppen nach Wochentag mit Platz und Uhrzeiten
- Spielerverwaltung mit Zuordnung zu Gruppen
- Pflege nicht moglicher Termine pro Spieler
- Auswertung und Kalender-/Excel-Exporte (je nach Modul)

## Projektstruktur

- `tennisrunden_app.py`: Hauptfenster und Navigation
- `neue_saison_dialog.py`: Saison anlegen/bearbeiten
- `neue_gruppe_dialog.py`: Gruppe anlegen
- `spieler_verwalten_dialog.py`: Spieler in Gruppen verwalten
- `auswertung.py`: Auswertung/Kopie der Ergebnisse
- `export_ics.py`, `spieler_ics.py`: Kalenderexport
- `excel_export.py`: Export nach Excel

## Voraussetzungen

- Python 3.11+
- Windows (aktuell primar genutzt)

## Starten

```powershell
python tennisrunden_app.py
```

## Tests

Es gibt derzeit einen einfachen Testlauf uber:

```powershell
python test_calendar.py
```

## GitHub Releases

Die Release-Struktur ist vorbereitet:

- `CHANGELOG.md` fur manuell gepflegte Anderungen
- `.github/release.yml` fur automatische Kategorien in GitHub Release Notes

Empfohlener Ablauf:

1. Anderungen entwickeln und mergen.
2. `CHANGELOG.md` unter `Unreleased` pflegen.
3. Version taggen (z. B. `v0.1.0`).
4. GitHub Release aus dem Tag erstellen.

## Sicherheit

Lokale Geheimnisse wie `credentials.json` und `token.json` sind in `.gitignore` ausgenommen und sollten nie committed werden.
