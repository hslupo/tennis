from dataclasses import dataclass, field
import datetime
from typing import List
from gruppe import Gruppe

@dataclass
class Saison:
    jahr: int
    start_date: datetime.date
    end_date: datetime.date
    groups: List[Gruppe] = field(default_factory=list)

    def build_frame(self, parent):
        import tkinter as tk
        frame = tk.Frame(parent, padx=10, pady=10)
        tk.Label(frame, text=f"Saison {self.jahr} ({self.start_date} – {self.end_date})",
                 font=("Arial", 14, "bold")).pack(anchor="w")
        for grp in self.groups:
            grp.build_frame(frame).pack(fill="x", pady=5)
        return frame
