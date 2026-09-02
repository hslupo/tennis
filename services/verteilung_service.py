"""Kern des Verteilungsalgorithmus (vorher in verteilen.py mit Tk-UI und
direktem Datei-I/O vermischt). Reine Funktionen: nehmen Gruppe/Termine/
Verfügbarkeit entgegen, liefern die Verteilung zurück – keine Persistenz."""

import random
from collections import defaultdict

from services.termine_service import generiere_termine

PAUSEN_GEWICHTUNG = 3
KANN_NICHT_PAUSENFAKTOR = 0.5
GRUENER_WUNSCH_STRAFE = 2


def ermittle_ersatzspieler(gruppe: dict, termin: str, spieler_ids: list) -> list:
    """Liefert verfügbare, für den Termin nicht eingeteilte Gruppenmitglieder."""
    return [
        spieler_id
        for spieler_id, eintrag in gruppe.get("players", {}).items()
        if termin not in eintrag.get("nicht_moeglich", []) and spieler_id not in spieler_ids
    ]


def verteile_gruppe(
    gruppe: dict,
    start_date: str,
    end_date: str,
    *,
    ausgeschlossene_paarungen=None,
    spieler_pro_termin=4,
    neue_termine=0,
    seed=None,
) -> dict:
    """Verteilt Spieler auf Termine für eine Gruppe. Gibt {termin: [spieler_id, ...]} zurück."""

    if ausgeschlossene_paarungen is None:
        ausgeschlossene_paarungen = set()
    else:
        ausgeschlossene_paarungen = set(tuple(sorted(paar)) for paar in ausgeschlossene_paarungen)

    termine = generiere_termine(start_date, end_date, gruppe["wochentag"])
    if neue_termine and neue_termine > 0:
        termine = termine[:neue_termine]

    ergebnis = {termin: [] for termin in termine}
    spieler_einsaetze = {s: 0 for s in gruppe["players"].keys()}
    paarungen = defaultdict(lambda: defaultdict(int))
    pausenkoeffizient = {s: 0.0 for s in gruppe["players"].keys()}

    if seed is not None:
        random.seed(seed)

    def bewerte_spieler(kandidat, bereits_ausgewaehlt):
        termin_wunsch = 0 if termin in gruppe["players"][kandidat].get("spielt", []) else GRUENER_WUNSCH_STRAFE
        pause_score = -pausenkoeffizient[kandidat]
        paarung_score = sum(paarungen[kandidat][s] for s in bereits_ausgewaehlt)
        einsatz_score = spieler_einsaetze[kandidat]
        ausgeglichener_score = pause_score * PAUSEN_GEWICHTUNG + paarung_score
        return (ausgeglichener_score + termin_wunsch, einsatz_score)

    def ist_erlaubte_paarung(spieler1, spieler2):
        return tuple(sorted([spieler1, spieler2])) not in ausgeschlossene_paarungen

    for termin in termine:
        verfuegbare_spieler = [
            s for s in gruppe["players"].keys()
            if termin not in gruppe["players"][s].get("nicht_moeglich", [])
        ]
        ausgewaehlte_spieler = []

        while len(ausgewaehlte_spieler) < spieler_pro_termin and verfuegbare_spieler:
            erlaubte_kandidaten = [
                s for s in verfuegbare_spieler
                if all(ist_erlaubte_paarung(s, a) for a in ausgewaehlte_spieler)
            ]
            if not erlaubte_kandidaten:
                break

            kandidaten = sorted(erlaubte_kandidaten, key=lambda s: bewerte_spieler(s, ausgewaehlte_spieler))
            min_score = bewerte_spieler(kandidaten[0], ausgewaehlte_spieler)
            beste_kandidaten = [s for s in kandidaten if bewerte_spieler(s, ausgewaehlte_spieler) == min_score]

            gewaehlter = random.choice(beste_kandidaten)
            ausgewaehlte_spieler.append(gewaehlter)
            verfuegbare_spieler.remove(gewaehlter)

        ergebnis[termin] = ausgewaehlte_spieler

        for s in gruppe["players"].keys():
            if s in ausgewaehlte_spieler:
                spieler_einsaetze[s] += 1
                pausenkoeffizient[s] = 0.0
                for other in ausgewaehlte_spieler:
                    if s != other:
                        paarungen[s][other] += 1
            elif termin in gruppe["players"][s].get("nicht_moeglich", []):
                pausenkoeffizient[s] += KANN_NICHT_PAUSENFAKTOR
            else:
                pausenkoeffizient[s] += 1.0

    return ergebnis


def plane_verteilung(gruppe: dict, saison: dict, seeds=(9, 16, 54, 61)):
    """Für jeden übergebenen Seed eine Vorschau-Verteilung der ersten 4 Termine berechnen."""
    start, ende = saison["start_date"], saison["end_date"]
    termine = generiere_termine(start, ende, gruppe["wochentag"])[:4]

    vorschlaege = {}
    for seed in seeds:
        vorschlaege[seed] = verteile_gruppe(gruppe, start, ende, neue_termine=4, seed=seed)
    return termine, vorschlaege
