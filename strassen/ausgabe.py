"""CSV-Ausgaben des Datensatzes. Enthält ausschließlich Fakten, keine Fließtexte."""
import csv
from pathlib import Path

FELDER_STRASSEN = ["schl_nr", "lemma", "stadtteile", "strassenklasse",
                   "namensgruppe", "verweis_auf", "buchseite", "status"]
FELDER_NAMEN = ["schl_nr", "stadium", "gueltig_ab", "datum_praezision",
                "name", "ist_urspruenglich"]
FELDER_PRUEFUNG = ["buchseite", "lemma_roh", "grund", "rohtext"]


def _schreibe(zeilen, pfad, felder):
    with open(Path(pfad), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def schreibe_strassen(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_STRASSEN)


def schreibe_namen(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_NAMEN)


def schreibe_pruefung(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_PRUEFUNG)
