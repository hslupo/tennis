from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Gruppe:
    wochentag: str
    platz: str
    startzeit: str
    endzeit: str
    players: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    verteilung: Dict[str, List[str]] = field(default_factory=dict)

    # GUI Frame zur Anzeige / Bearbeitung
    def build_frame(self, parent):
        import tkinter as tk
        frame = tk.Frame(parent, padx=10, pady=10)
        tk.Label(frame, text=f"{self.wochentag} - {self.platz} {self.startzeit}-{self.endzeit}",
                 font=("Arial", 12, "bold")).pack(anchor="w")
        for pid in self.players.keys():
            tk.Label(frame, text=f"Spieler: {pid}").pack(anchor="w")
        return frame
