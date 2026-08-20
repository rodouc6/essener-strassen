"""Rohe OCR-Seiten zu fortlaufendem, parsebarem Text aufbereiten.

Reihenfolge ist wesentlich: Erst die über Zeilenumbrüche zerrissenen Feldmarker
zusammenziehen, dann die echte Silbentrennung auflösen. Umgekehrt zerstörte die
Silbentrennungsregel die Marker ('Str.-\nKl.:' würde zu 'Str.Kl.:').
"""
import re
from pathlib import Path

# Feldmarker, die im Satz über die Zeile brechen (661 + 55 + 9 Fälle im Material)
_MARKER = [
    (re.compile(r"(Str)\.-\s*\n\s*(Kl)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Str)\.-\s*\n\s*(Gr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Schl)\.-\s*\n\s*(Nr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"Stadt-\s*\n\s*teil"), "Stadtteil"),
]
_KOLUMNENTITEL = re.compile(r"^\s*Essener Straßen\s*$", re.MULTILINE)
_SEITENZAHL = re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE)
# OCR-Fehler: „ß" am Zeilenanfang wird als „B" gelesen. Nur „stra-\nBe…" (Fragment
# beginnt mit „e") wird korrigiert zu „straße…" (9 Fälle). Andere „-\nB"-Fälle
# (Komposita wie „Essen-Bredeney") bleiben unangetastet.
_OCR_FEHLER = re.compile(r"([Ss]tra)-\n\s*B(?=e)")
# Silbentrennung: Trennstrich am Zeilenende vor Kleinbuchstabe.
# Vor Großbuchstabe ist der Strich Namensbestandteil (Franz-Arens-Straße).
_TRENNUNG = re.compile(r"-\n(?=[a-zäöüß])")


def bereinige(text: str) -> str:
    text = _KOLUMNENTITEL.sub("", text)
    return _SEITENZAHL.sub("", text)


def verbinde_zeilen(text: str) -> str:
    for muster, ersatz in _MARKER:
        text = muster.sub(ersatz, text)
    text = _OCR_FEHLER.sub(r"\1ß", text)
    text = _TRENNUNG.sub("", text)
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def lade_seiten(verzeichnis) -> list:
    seiten = []
    for pfad in sorted(Path(verzeichnis).glob("s*.txt")):
        nummer = int(pfad.stem.lstrip("s"))
        seiten.append((nummer, pfad.read_text(encoding="utf-8", errors="replace")))
    return seiten


def aufbereiten(verzeichnis) -> list:
    return [(nr, verbinde_zeilen(bereinige(roh))) for nr, roh in lade_seiten(verzeichnis)]
