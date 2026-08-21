def ermittle_state(jahr: int):
    """
    Prüft den Zustand für ein Jahr:
    - NO_SAISON: keine Saison in der Datenbank vorhanden
    - NO_GROUP: Saison existiert, aber keine Gruppen
    - SHOW_GROUP: es gibt Gruppen
    """
    import legacy_adapter

    saison = legacy_adapter.lade_saison(jahr)
    if saison is None:
        return "NO_SAISON", None

    if not saison.get("groups"):
        return "NO_GROUP", saison

    return "SHOW_GROUP", saison