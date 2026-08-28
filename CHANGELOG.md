# Changelog

Alle nennenswerten Anderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format orientiert sich an Keep a Changelog und Semantic Versioning.

## [Unreleased]

### Added

- GitHub-Repository eingerichtet (`hslupo/tennis`)
- README mit Setup- und Release-Hinweisen
- GitHub Release-Konfiguration fur kategorisierte Release Notes

### Changed

- Die Planung berucksichtigt jetzt mehrere Dinge gleichzeitig: Wer an einem Termin
	gerne spielen mochte, wird bevorzugt eingeplant. Wer schon langer pausiert hat,
	wird ebenfalls bevorzugt berucksichtigt. Ein "Kann nicht" zahlt dabei etwas ab-
	geschwacht als eine normale Pause.
- Wiederholte Paarungen werden nach Moglichkeit vermieden, damit nicht immer die
	gleichen Spieler miteinander spielen.

## [0.1.0] - 2026-03-31

### Added

- Bestehende Basisfunktionen zur Verwaltung von Tennisrunden
- Saison-, Gruppen- und Spielerverwaltung
- Verfugbarkeitsverwaltung und Auswertungs-/Exportmodule
