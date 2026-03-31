from dataclasses import dataclass

@dataclass
class Spieler:
    id: str
    name: str
    telefon: str = ""
    mobil: str = ""
