"""Antworten der LLM-Lesung mit dem Parser vergleichen (Spec 2026-09-12, Abschnitt 3.3).

Die Modelle sind unabhängige zweite Leser; sie ändern nie den Status. Ausgaben:
daten/pruefung_llm.csv (eine Zeile je abweichendem Feld, Eingabemaske für Korrekturen),
docs/llm_lesung.md (Kennzahlen), docs/goldstandard/ergebnis_llm.md (Messung).

  python3 -m strassen.llm_vergleich pruefliste  [--antworten-dir DIR]
  python3 -m strassen.llm_vergleich goldstandard --modell NAME
  python3 -m strassen.llm_vergleich uebernehmen [--datum JJJJ-MM-TT]
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from strassen.datum import lese_text
from strassen.differenz import als_struktur, vergleiche
from strassen.goldstandard import formatiere_datum

WURZEL = Path(__file__).resolve().parent.parent
ANTWORTEN_DIR = WURZEL / "llm" / "antworten"
DATEN_DIR = WURZEL / "daten"
PRUEFLISTE_PFAD = DATEN_DIR / "pruefung_llm.csv"
KENNZAHLEN_PFAD = WURZEL / "docs" / "llm_lesung.md"
STATUS_MODELL = "modell"
KURZNAMEN = ("qwen", "mistral")
KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf"]
GRUND_DATUM = "Datum nicht normalisierbar"

_UNVOLLSTAENDIG = "_unvollstaendig"   # interne Markierung, wird nicht geschrieben


def kurzname(modell: str) -> str:
    for k in KURZNAMEN:
        if k in modell.lower():
            return k
    raise ValueError(f"kein Kurzname für Modell {modell!r} (erwartet: {', '.join(KURZNAMEN)})")


def _text(wert) -> str:
    if isinstance(wert, list):
        return "; ".join(str(w).strip() for w in wert if str(w).strip())
    return str(wert or "").strip()


def _schl_nr(wert) -> str:
    t = _text(wert)
    return t.zfill(5) if t.isdigit() else t     # führende Nullen sind Formatierung, keine Lesung


def ist_unvollstaendig(strasse: dict) -> bool:
    return bool(strasse.get(_UNVOLLSTAENDIG))


def normalisiere_antwort(antwort: dict):
    """Eine Antwortdatei -> (strassen, namen, probleme) in Datensatzform."""
    eintraege = antwort.get("eintraege")
    buchseite = int(antwort.get("buchseite", 0))
    if not eintraege:
        return [], [], []
    strassen, namen, probleme = [], [], []
    for e in eintraege:
        schl = _schl_nr(e.get("schl_nr"))
        strassen.append({
            "schl_nr": schl, "lemma": _text(e.get("lemma")),
            "stadtteile": _text(e.get("stadtteile")), "strassenklasse": _text(e.get("strassenklasse")),
            "namensgruppe": _text(e.get("namensgruppe")), "verweis_auf": _text(e.get("verweis_auf")),
            "buchseite": buchseite, "status": STATUS_MODELL,
            _UNVOLLSTAENDIG: bool(e.get("unvollstaendig"))})
        for i, s in enumerate(e.get("stadien") or [], 1):
            text = _text(s.get("datum"))
            d = lese_text(text)
            if d is None:
                probleme.append({"schl_nr": schl, "buchseite": buchseite, "feld": f"stadium_{i}_datum",
                                 "text": text, "grund": GRUND_DATUM})
                gueltig_ab, praezision = "", "unbekannt"
            else:
                gueltig_ab, praezision = d.gueltig_ab, d.praezision
            namen.append({"schl_nr": schl, "stadium": i, "gueltig_ab": gueltig_ab,
                          "datum_praezision": praezision, "name": _text(s.get("name")),
                          "ist_urspruenglich": "wahr" if s.get("urspruenglich") else "falsch"})
    return strassen, namen, probleme


def lade_antworten(antworten_dir, modell: str) -> dict:
    """Buchseite -> Antwortdatei (nur vorhandene Seiten)."""
    ordner = Path(antworten_dir) / modell
    antworten = {}
    for pfad in sorted(ordner.glob("s*.json")):
        a = json.loads(pfad.read_text(encoding="utf-8"))
        antworten[int(pfad.stem.lstrip("s"))] = a
    return antworten
