import json
from pathlib import Path


def rename_player_id(saison_datei: str, alte_id: str, neue_id: str):
    path = Path(saison_datei)
    if not path.exists():
        print(f"❌ Datei {saison_datei} nicht gefunden")
        return

    saison = json.loads(path.read_text(encoding="utf-8"))

    if "groups" not in saison:
        print(f"❌ Keine Gruppen in {saison_datei} gefunden")
        return

    for group_key, group in saison["groups"].items():
        # --- players dict ---
        if alte_id in group.get("players", {}):
            group["players"][neue_id] = group["players"].pop(alte_id)

        # --- nicht_moeglich Listen prüfen ---
        for pid, pdata in group.get("players", {}).items():
            nm = pdata.get("nicht_moeglich", [])
            if isinstance(nm, list):
                pdata["nicht_moeglich"] = [d for d in nm]  # bleibt unverändert

        # --- verteilung ---
        if "verteilung" in group:
            for termin, ids in group["verteilung"].items():
                group["verteilung"][termin] = [neue_id if x == alte_id else x for x in ids]

    # Speichern
    path.write_text(json.dumps(saison, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ ID {alte_id} → {neue_id} in {saison_datei} geändert.")


# Testlauf
if __name__ == "__main__":
    rename_player_id("2025.json", "biene", "bine")
