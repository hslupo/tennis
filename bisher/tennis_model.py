# tennis_model.py
import json
from pathlib import Path
from typing import List, Dict, Optional


class Spieler:
    """
    Stammdaten eines Spielers (dauerhaft gültig).
    """
    def __init__(self, id: str, name: str, telefon: str = "", mobil: str = ""):
        self.id = id
        self.name = name
        self.telefon = telefon
        self.mobil = mobil

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "telefon": self.telefon,
            "mobil": self.mobil,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Spieler":
        return Spieler(
            id=data["id"],
            name=data["name"],
            telefon=data.get("telefon", ""),
            mobil=data.get("mobil", ""),
        )


class SaisonSpieler:
    """
    Spieler innerhalb einer Saison/Gruppe mit zusätzlichen Kontextdaten.
    """
    def __init__(self, spieler_id: str, dummyname: str = "", nicht_verfuegbare_termine: Optional[List[str]] = None):
        self.spieler_id = spieler_id
        self.dummyname = dummyname
        self.nicht_verfuegbare_termine = nicht_verfuegbare_termine or []

    def to_dict(self) -> Dict:
        return {
            "id": self.spieler_id,
            "dummyname": self.dummyname,
            "nicht_verfuegbare_termine": self.nicht_verfuegbare_termine,
        }

    @staticmethod
    def from_dict(data: Dict) -> "SaisonSpieler":
        return SaisonSpieler(
            spieler_id=data["id"],
            dummyname=data.get("dummyname", ""),
            nicht_verfuegbare_termine=data.get("nicht_verfuegbare_termine", []),
        )


class Saison:
    """
    Eine Saison, die aus einer Gruppe besteht.
    """
    def __init__(self, jahr: int, gruppe: str, start_date: str, end_date: str,
                 players: List[SaisonSpieler], verteilung: Optional[Dict[str, List[str]]] = None):
        self.jahr = jahr
        self.gruppe = gruppe
        self.start_date = start_date
        self.end_date = end_date
        self.players = players
        self.verteilung = verteilung or {}

    def to_dict(self) -> Dict:
        return {
            "jahr": self.jahr,
            "gruppe": self.gruppe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "players": [p.to_dict() for p in self.players],
            "verteilung": self.verteilung,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Saison":
        return Saison(
            jahr=data["jahr"],
            gruppe=data["gruppe"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            players=[SaisonSpieler.from_dict(p) for p in data["players"]],
            verteilung=data.get("verteilung", {}),
        )


# Hilfsfunktionen für JSON-Speicherung
def save_json(path: Path, data: Dict):
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    # Beispiel-Stammdaten
    spieler = [
        Spieler("erna", "Erna"),
        Spieler("meiki", "Meiki"),
        Spieler("biene", "Biene"),
    ]

    save_json(Path("../spieler.json"), {"players": [s.to_dict() for s in spieler]})

    # Beispiel-Saison
    saison = Saison(
        jahr=2024,
        gruppe="Freitag",
        start_date="2024-10-04",
        end_date="2025-04-25",
        players=[
            SaisonSpieler("erna", dummyname="Spieler 1", nicht_verfuegbare_termine=["04.10.2024"]),
            SaisonSpieler("meiki", dummyname="Spieler 2"),
        ],
        verteilung={"04.10.2024": ["erna", "meiki"]},
    )

    save_json(Path("saison_freitag_2024.json"), saison.to_dict())

    # Test: Laden
    data = load_json(Path("saison_freitag_2024.json"))
    saison2 = Saison.from_dict(data)
    print(saison2.to_dict())
