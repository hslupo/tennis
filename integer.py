import json
from pathlib import Path


def check_and_repair(spieler_datei="spieler.json", saison_datei="2025.json"):
    """Prüft und repariert Inkonsistenzen zwischen spieler.json und Saisondatei"""

    # --- Spieler laden ---
    sp_path = Path(spieler_datei)
    if not sp_path.exists():
        print(f"⚠️ {spieler_datei} nicht gefunden – neue Datei wird angelegt.")
        spieler_liste = []
    else:
        try:
            spieler_liste = json.loads(sp_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Fehler beim Lesen von {spieler_datei}: {e}")
            spieler_liste = []

    # Muss Liste sein
    if not isinstance(spieler_liste, list):
        print(f"❌ Ungültiges Format in {spieler_datei}, erwarte Liste – repariere...")
        spieler_liste = []

    # Sicherstellen, dass jeder Dict die Keys hat
    for sp in spieler_liste:
        if not isinstance(sp, dict):
            continue
        for key in ["id", "name", "telefon", "mobil"]:
            sp.setdefault(key, "")

    # --- Saison prüfen ---
    sa_path = Path(saison_datei)
    if not sa_path.exists():
        print(f"⚠️ {saison_datei} nicht gefunden – überspringe Saisonprüfung.")
    else:
        try:
            saison = json.loads(sa_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ Fehler beim Lesen von {saison_datei}: {e}")
            saison = {}

        if "groups" in saison:
            bekannte_ids = {sp["id"] for sp in spieler_liste if "id" in sp}
            for group_key, group in saison["groups"].items():
                for pid in group.get("players", {}).keys():
                    if pid not in bekannte_ids:
                        print(f"⚠️ Spieler-ID '{pid}' in Gruppe {group_key} fehlt in {spieler_datei} – füge hinzu.")
                        spieler_liste.append({
                            "id": pid,
                            "name": pid,   # Platzhalter
                            "telefon": "",
                            "mobil": ""
                        })
                        bekannte_ids.add(pid)

    # --- Ergebnis speichern ---
    sp_path.write_text(json.dumps(spieler_liste, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ {spieler_datei} geprüft und repariert.")


# Testlauf
if __name__ == "__main__":
    check_and_repair("spieler.json", "2025.json")
