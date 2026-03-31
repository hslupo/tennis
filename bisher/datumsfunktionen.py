import datetime

def letzter_montag_september(jahr: int) -> datetime.date:
    """
    Berechnet den letzten Montag im September eines Jahres.
    """
    # 30. September ist immer im September
    datum = datetime.date(jahr, 9, 30)
    # weekday(): Montag=0 ... Sonntag=6
    tage_zurueck = (datum.weekday() - 0) % 7
    return datum - datetime.timedelta(days=tage_zurueck)


def letzter_sonntag_april(jahr: int) -> datetime.date:
    """
    Berechnet den letzten Sonntag im April eines Jahres.
    """
    datum = datetime.date(jahr, 4, 30)
    tage_zurueck = (datum.weekday() - 6) % 7
    return datum - datetime.timedelta(days=tage_zurueck)


def plus_eine_woche(datum: datetime.date) -> datetime.date:
    """Verschiebt ein Datum um +7 Tage."""
    return datum + datetime.timedelta(weeks=1)

def minus_eine_woche(datum: datetime.date) -> datetime.date:
    """Verschiebt ein Datum um -7 Tage."""
    return datum - datetime.timedelta(weeks=1)

# --- Test ---
if __name__ == "__main__":
    jahr = 2024
    print("Letzter Montag im September:", letzter_montag_september(jahr))
    print("Letzter Sonntag im April:", letzter_sonntag_april(jahr + 1))
