import json
from datetime import datetime, timedelta
import random
from collections import defaultdict

def verteile_spieler(spieler, termine, ausgeschlossene_paarungen=None, spieler_pro_termin=4, bestehende_verteilung=None, ab_datum=None):
    ergebnis = {termin: [] for termin in termine}
    spieler_einsaetze = {s: 0 for s in spieler}
    paarungen = defaultdict(lambda: defaultdict(int))

    if ausgeschlossene_paarungen is None:
        ausgeschlossene_paarungen = set()
    else:
        ausgeschlossene_paarungen = set(tuple(sorted(paar)) for paar in ausgeschlossene_paarungen)

    def bewerte_spieler(kandidat, bereits_ausgewaehlt):
        einsatz_score = spieler_einsaetze[kandidat]
        paarung_score = sum(paarungen[kandidat][s] for s in bereits_ausgewaehlt)
        return (einsatz_score, paarung_score)

    def ist_erlaubte_paarung(spieler1, spieler2):
        return tuple(sorted([spieler1, spieler2])) not in ausgeschlossene_paarungen

    # Wenn eine bestehende Verteilung übergeben wird
    if bestehende_verteilung:
        # Wenn kein ab_datum angegeben ist, übernehme die bestehende Verteilung vollständig
        if not ab_datum:
            ergebnis = bestehende_verteilung
            # Analysiere die Einsätze und Paarungen der bestehenden Verteilung
            for termin, spieler_liste in bestehende_verteilung.items():
                for s in spieler_liste:
                    spieler_einsaetze[s] += 1
                    for other_s in spieler_liste:
                        if s != other_s:
                            paarungen[s][other_s] += 1
            return ergebnis, paarungen, spieler_pro_termin

        # Wenn ein ab_datum vorhanden ist, verteile ab diesem Datum neu
        ab_datum_dt = datetime.strptime(ab_datum, '%d.%m.%Y')
        for termin in termine:
            termin_dt = datetime.strptime(termin, '%d.%m.%Y')
            if termin_dt < ab_datum_dt:
                ergebnis[termin] = bestehende_verteilung.get(termin, [])
                for s in ergebnis[termin]:
                    spieler_einsaetze[s] += 1
                    for other_s in ergebnis[termin]:
                        if s != other_s:
                            paarungen[s][other_s] += 1

    # Verteile die Spieler für alle Termine, die noch nicht durch bestehende Verteilung abgedeckt sind
    nv_spieler = {}
    for termin in termine:
        if ergebnis[termin]:  # Überspringe Termine, die bereits aus bestehender Verteilung übernommen wurden
            continue

        verfuegbare_spieler = [
            s for s in spieler
            if termin not in spieler[s].get('nicht_verfuegbar', []) and len(ergebnis[termin]) < spieler_pro_termin
        ]
        nicht_verfuegbare_spieler = [
            s for s in spieler
            if termin in spieler[s].get('nicht_verfuegbar', [])
        ]
        nv_spieler[termin] = nicht_verfuegbare_spieler

        ausgewaehlte_spieler = []
        while len(ausgewaehlte_spieler) < spieler_pro_termin and verfuegbare_spieler:
            erlaubte_kandidaten = [
                s for s in verfuegbare_spieler
                if all(ist_erlaubte_paarung(s, ausgewaehlter) for ausgewaehlter in ausgewaehlte_spieler)
            ]

            if not erlaubte_kandidaten:
                break  # Keine erlaubten Kandidaten mehr verfügbar

            kandidaten = sorted(erlaubte_kandidaten, key=lambda s: bewerte_spieler(s, ausgewaehlte_spieler))

            min_score = bewerte_spieler(kandidaten[0], ausgewaehlte_spieler)
            beste_kandidaten = [s for s in kandidaten if bewerte_spieler(s, ausgewaehlte_spieler) == min_score]
            ausgewaehlter_spieler = random.choice(beste_kandidaten)

            ausgewaehlte_spieler.append(ausgewaehlter_spieler)
            verfuegbare_spieler.remove(ausgewaehlter_spieler)

        ergebnis[termin] = ausgewaehlte_spieler

        for s in ausgewaehlte_spieler:
            spieler_einsaetze[s] += 1
            for other_s in ausgewaehlte_spieler:
                if s != other_s:
                    paarungen[s][other_s] += 1

    return ergebnis, paarungen, spieler_pro_termin, nv_spieler


def analysiere_verteilung(verteilung, paarungen, ausgeschlossene_paarungen = []):
    einsaetze = defaultdict(int)
    for spieler_liste in verteilung.values():
        for name in spieler_liste:
            einsaetze[name] += 1

    print("\nAnzahl der Einsätze pro Spieler:")
    for name, anzahl in sorted(einsaetze.items()):
        print(f"{name}: {anzahl}")

    print("\nHäufigkeit der Paarungen:")
    for spieler1 in sorted(paarungen.keys()):
        print(f"\n{spieler1} wurde eingeteilt mit:")
        for spieler2, anzahl in sorted(paarungen[spieler1].items(), key=lambda x: x[1], reverse=True):
            print(f"  {spieler2}: {anzahl} mal")

    print("\nÜberprüfung der ausgeschlossenen Paarungen:")
    for paar in ausgeschlossene_paarungen:
        s1, s2 = paar
        if paarungen[s1][s2] > 0:
            print(f"Warnung: Ausgeschlossene Paarung {s1} und {s2} wurde {paarungen[s1][s2]} mal eingeteilt.")
        else:
            print(f"Ausgeschlossene Paarung {s1} und {s2} wurde erfolgreich vermieden.")

def speichere_verteilung_in_json(original_datei, neue_datei, verteilung):
    # Lade die ursprüngliche JSON-Datei
    with open(original_datei, 'r') as file:
        data = json.load(file)

    # Füge die Verteilung zur ursprünglichen Datenstruktur hinzu
    data['verteilung'] = verteilung

    # Speichere die erweiterte Datenstruktur in einer neuen Datei
    with open(neue_datei, 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# Nur ausführen, wenn das Modul direkt gestartet wird
if __name__ == "__main__":
    # Load the JSON data
    with open('24-Freitag.json', 'r') as file:
        data = json.load(file)

    # Extract players and their unavailable dates
    players = {player['name']: {'nicht_verfuegbar': player['nicht_verfuegbare_termine']} for player in data['players']}

    # Generate all Fridays between start_date and end_date
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    termine = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() == 4:  # Friday
            termine.append(current_date.strftime('%d.%m.%Y'))
        current_date += timedelta(days=1)

    # Definieren Sie hier die auszuschließenden Paarungen (falls nötig)
    ausgeschlossene_paarungen = []

    # Funktion aufrufen
    verteilung, paarungen, spieler_pro_termin, nv_spieler = verteile_spieler(players, termine, ausgeschlossene_paarungen)

    # Ergebnis ausgeben
    print("\nVerteilung der Spieler auf Termine:")
    for termin, spieler_liste in verteilung.items():
        print(f"{termin}: {', '.join(sorted(spieler_liste))}")

    print("\nTermine mit Spielern die nicht können")
    for termin, liste in nv_spieler.items():
        print(f"{termin}: {', '.join(liste)}")

    # Analyse der Verteilung und Paarungen
    analysiere_verteilung(verteilung, paarungen, ausgeschlossene_paarungen)

    # Zusätzliche Statistiken
    print("\nZusätzliche Statistiken:")
    print(f"Gesamtzahl der Termine: {len(termine)}")
    print(f"Durchschnittliche Anzahl von Spielern pro Termin: {sum(len(sl) for sl in verteilung.values()) / len(termine):.2f}")
    print(f"Termine mit weniger als {spieler_pro_termin} Spielern: {sum(1 for sl in verteilung.values() if len(sl) < spieler_pro_termin)}")

    # Überprüfung der Nichtverfügbarkeiten
    print("\nÜberprüfung der Nichtverfügbarkeiten:")
    for s, info in players.items():
        nicht_verfuegbar = info.get('nicht_verfuegbar', [])
        verletzungen = [t for t in nicht_verfuegbar if s in verteilung[t]]
        if verletzungen:
            print(f"Warnung: Spieler {s} wurde für Termin(e) {', '.join(verletzungen)} eingeteilt, obwohl nicht verfügbar.")
        else:
            print(f"Spieler {s}: Alle Nichtverfügbarkeiten wurden berücksichtigt.")


    # speichere_verteilung_in_json('24-Freitag.json', '24-Freitag1.json', verteilung)