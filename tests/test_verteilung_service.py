import unittest

from services.verteilung_service import plane_verteilung, verteile_gruppe


def _gruppe(spieler_nicht_moeglich: dict) -> dict:
    return {
        "wochentag": "Freitag",
        "players": {pid: {"nicht_moeglich": nm} for pid, nm in spieler_nicht_moeglich.items()},
    }


class VerteilungServiceTest(unittest.TestCase):
    def test_ist_deterministisch_bei_festem_seed(self):
        gruppe = _gruppe({1: [], 2: [], 3: [], 4: [], 5: []})
        e1 = verteile_gruppe(gruppe, "2025-09-15", "2025-10-15", spieler_pro_termin=4, seed=42)
        e2 = verteile_gruppe(gruppe, "2025-09-15", "2025-10-15", spieler_pro_termin=4, seed=42)
        self.assertEqual(e1, e2)

    def test_respektiert_nicht_moeglich(self):
        gruppe = _gruppe({
            1: ["19.09.2025"],
            2: [],
            3: [],
            4: [],
            5: [],
        })
        ergebnis = verteile_gruppe(gruppe, "2025-09-15", "2025-09-19", spieler_pro_termin=4, seed=1)
        self.assertNotIn(1, ergebnis["19.09.2025"])

    def test_ueberschreitet_spieler_pro_termin_nicht(self):
        gruppe = _gruppe({i: [] for i in range(1, 9)})
        ergebnis = verteile_gruppe(gruppe, "2025-09-15", "2025-10-15", spieler_pro_termin=4, seed=7)
        for spieler in ergebnis.values():
            self.assertLessEqual(len(spieler), 4)

    def test_respektiert_ausgeschlossene_paarungen(self):
        gruppe = _gruppe({1: [], 2: [], 3: [], 4: [], 5: []})
        ergebnis = verteile_gruppe(
            gruppe, "2025-09-15", "2025-10-15", spieler_pro_termin=4,
            ausgeschlossene_paarungen={(1, 2)}, seed=3,
        )
        for spieler in ergebnis.values():
            self.assertFalse(1 in spieler and 2 in spieler)

    def test_neue_termine_begrenzt_anzahl_termine(self):
        gruppe = _gruppe({1: [], 2: [], 3: [], 4: []})
        ergebnis = verteile_gruppe(
            gruppe, "2025-09-15", "2026-04-26", spieler_pro_termin=4, neue_termine=3, seed=1,
        )
        self.assertEqual(len(ergebnis), 3)

    def test_plane_verteilung_liefert_ergebnis_je_seed(self):
        gruppe = _gruppe({1: [], 2: [], 3: [], 4: [], 5: []})
        saison = {"start_date": "2025-09-15", "end_date": "2026-04-26"}
        termine, vorschlaege = plane_verteilung(gruppe, saison, seeds=(1, 2))
        self.assertEqual(len(termine), 4)
        self.assertEqual(set(vorschlaege.keys()), {1, 2})
        for v in vorschlaege.values():
            self.assertEqual(set(v.keys()), set(termine))


if __name__ == "__main__":
    unittest.main()
