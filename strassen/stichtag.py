"""Namensstand zu einem Stichtag bestimmen und die Konkordanz ableiten.

Stadien ohne verwertbares Datum werden übersprungen, nicht geschätzt; wo dadurch
kein Stadium bestimmbar ist, entsteht kein Konkordanzeintrag.
"""
import re
from collections import defaultdict


def _vergleichbar(stadium) -> str:
    """Datum in vergleichbarer Form; leer, wenn nicht verwertbar."""
    wert = (stadium.get("gueltig_ab") or "").strip()
    if not wert:
        return ""
    if len(wert) == 4:            # nur Jahr: konservativ auf Jahresende legen
        return f"{wert}-12-31"
    return wert


def _norm_strasse(s: str) -> str:
    """Normalisiert einen Straßennamen für den Adressbuch-Abgleich: kleinschreiben
    und 'str.'/'straße' vereinheitlichen (Adressbuch-Einträge sind oft abgekürzt)."""
    s = (s or "").strip().lower()
    s = re.sub(r"str\.?$", "straße", s)
    return s


def name_am_stichtag(stadien, stichtag: str):
    gueltig = None
    for s in sorted(stadien, key=lambda x: _vergleichbar(x) or "9999"):
        d = _vergleichbar(s)
        if not d:
            continue
        if d <= stichtag:
            gueltig = s
    return gueltig


def messe_erhebungsstand(stadien_je_strasse, adressbuch_namen) -> dict:
    """Zählt je Jahr, ob das Adressbuch die alte oder die neue Namensform nutzt."""
    adressbuch_norm = {_norm_strasse(n) for n in adressbuch_namen}
    befund = defaultdict(lambda: {"alt": 0, "neu": 0})
    for stadien in stadien_je_strasse.values():
        geordnet = sorted(stadien, key=lambda x: _vergleichbar(x) or "9999")
        for i in range(1, len(geordnet)):
            d = _vergleichbar(geordnet[i])
            if not d:
                continue
            jahr = int(d[:4])
            alt = _norm_strasse(geordnet[i - 1]["name"])
            neu = _norm_strasse(geordnet[i]["name"])
            if alt in adressbuch_norm and neu not in adressbuch_norm:
                befund[jahr]["alt"] += 1
            elif neu in adressbuch_norm and alt not in adressbuch_norm:
                befund[jahr]["neu"] += 1
    return dict(sorted(befund.items()))


def messe_erhebungsstand_monatlich(stadien_je_strasse, adressbuch_namen,
                                    von: str, bis: str) -> dict:
    """Wie messe_erhebungsstand, aber monatsscharf (Schlüssel 'JJJJ-MM'), begrenzt
    auf den Bereich [von, bis] (je 'JJJJ-MM'). Nutzt NUR Stadien mit Tagespräzision:
    Jahrespräzision liefert keinen echten Monat — der würde sonst geraten (auf
    Dezember gelegt) statt aus den Daten zu stammen, was gegen precision-first
    verstieße. In den hier ausgewerteten Jahren (1935-1937) sind ohnehin alle
    tatsächlichen Umbenennungs-Übergänge tagesgenau datiert."""
    adressbuch_norm = {_norm_strasse(n) for n in adressbuch_namen}
    befund = defaultdict(lambda: {"alt": 0, "neu": 0})
    for stadien in stadien_je_strasse.values():
        geordnet = sorted(stadien, key=lambda x: _vergleichbar(x) or "9999")
        for i in range(1, len(geordnet)):
            d = _vergleichbar(geordnet[i])
            praezision = geordnet[i].get("datum_praezision", "")
            if not d or praezision != "tag":
                continue
            monat = d[:7]
            if not (von <= monat <= bis):
                continue
            alt = _norm_strasse(geordnet[i - 1]["name"])
            neu = _norm_strasse(geordnet[i]["name"])
            if alt in adressbuch_norm and neu not in adressbuch_norm:
                befund[monat]["alt"] += 1
            elif neu in adressbuch_norm and alt not in adressbuch_norm:
                befund[monat]["neu"] += 1
    return dict(sorted(befund.items()))


def baue_konkordanz(strassen, namen, stichtag: str) -> list:
    je_nr = defaultdict(list)
    for z in namen:
        je_nr[z["schl_nr"]].append(z)
    aus = []
    for s in strassen:
        stadien = je_nr.get(s["schl_nr"], [])
        treffer = name_am_stichtag(stadien, stichtag)
        if not treffer:
            continue
        if treffer["name"].strip() == s["lemma"].strip():
            continue                      # Name unverändert — kein Konkordanzeintrag
        aus.append({"stadtteil": s.get("stadtteile", "").split(";")[0].strip(),
                    "ehemalig": treffer["name"].strip(),
                    "heutig": s["lemma"].strip(),
                    "schl_nr": s["schl_nr"],
                    "datum_praezision": treffer.get("datum_praezision", ""),
                    "quelle": "Dickhoff 2015"})
    return aus
