"""Prüfbilder je Prüfzeile: Seitenausschnitte am Scan zur Sichtung der Prüfliste
(Spec 2026-09-13, Abschnitt W1).

Liest `daten/pruefung_llm.csv` (Spalten `schl_nr, buchseite, feld, ..., einig`),
fasst je `(schl_nr, buchseite)` die zu prüfenden Felder zusammen, rendert je
Eintrag genau einen Scan-Ausschnitt (idempotent — vorhandene Bilder werden nicht
neu gerendert) nach `llm/pruefbilder/` (gitignored — Seitenbilder sind
urheberrechtlich geschützt) und schreibt daneben eine `index.md` mit einer
Übersichtstabelle zur bequemen Sichtung.

  python3 -m strassen.pruefbilder [--einig beide] [--quelle DIR] [--ziel DIR]
"""
import argparse
import csv
from pathlib import Path

from strassen.goldstandard import (QUELLE_PFAD, buchseite_zu_scan,
                                    rendere_ausschnitt, scan_dateiname)

WURZEL = Path(__file__).resolve().parent.parent
ZIEL_DIR = WURZEL / "llm" / "pruefbilder"
PRUEFLISTE_PFAD = WURZEL / "daten" / "pruefung_llm.csv"

_EINIG_RANG = {"beide": 0, "eines": 1, "unlesbar": 2, "keines": 3}

bilddateiname = scan_dateiname


def eintraege_aus_pruefliste(zeilen, einig=("beide",)) -> list:
    """Fasst die Prüflisten-Zeilen je (schl_nr, buchseite) zusammen; nur Zeilen,
    deren `einig`-Wert in `einig` liegt. Felder je Eintrag sortiert, dedupliziert.
    Reihenfolge: Rang von `einig` (beide < eines < unlesbar < keines), dann schl_nr."""
    je_schluessel = {}
    for z in zeilen:
        if z["einig"] not in einig:
            continue
        schluessel = (z["schl_nr"], int(z["buchseite"]))
        eintrag = je_schluessel.setdefault(schluessel, {
            "schl_nr": z["schl_nr"], "buchseite": int(z["buchseite"]),
            "einig": z["einig"], "felder": set()})
        eintrag["felder"].add(z["feld"])
        if _EINIG_RANG[z["einig"]] < _EINIG_RANG[eintrag["einig"]]:
            eintrag["einig"] = z["einig"]

    eintraege = []
    for (schl_nr, buchseite), e in je_schluessel.items():
        eintraege.append({"schl_nr": schl_nr, "buchseite": buchseite,
                          "felder": sorted(e["felder"]), "einig": e["einig"]})
    eintraege.sort(key=lambda e: (_EINIG_RANG[e["einig"]], e["schl_nr"]))
    return eintraege


def formatiere_index(eintraege) -> str:
    """Markdown-Tabelle: schl_nr, buchseite, Felder, Bilddatei."""
    zeilen = ["| schl_nr | buchseite | Felder | Bild |",
              "| --- | --- | --- | --- |"]
    for e in eintraege:
        felder = ", ".join(e["felder"])
        bild = bilddateiname(e["schl_nr"], e["buchseite"])
        zeilen.append(f"| {e['schl_nr']} | {e['buchseite']} | {felder} | {bild} |")
    return "\n".join(zeilen) + "\n"


def erzeuge(pruefliste_pfad=PRUEFLISTE_PFAD, ziel_dir=ZIEL_DIR, quelle_dir=QUELLE_PFAD,
            einig=("beide",), render=rendere_ausschnitt) -> int:
    """Liest die Prüfliste, rendert je Eintrag den fehlenden Scan-Ausschnitt
    (dpi=150) und schreibt die index.md neu. Gibt die Zahl neu gerenderter
    Bilder zurück (idempotent)."""
    ziel_dir = Path(ziel_dir)
    ziel_dir.mkdir(parents=True, exist_ok=True)
    with open(Path(pruefliste_pfad), encoding="utf-8", newline="") as f:
        zeilen = list(csv.DictReader(f))
    eintraege = eintraege_aus_pruefliste(zeilen, einig=einig)

    neu = 0
    for e in eintraege:
        ziel_png = ziel_dir / bilddateiname(e["schl_nr"], e["buchseite"])
        if ziel_png.exists():
            continue
        band, pdf_seite, haelfte = buchseite_zu_scan(e["buchseite"])
        render(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi=150)
        neu += 1

    (ziel_dir / "index.md").write_text(formatiere_index(eintraege), encoding="utf-8")
    return neu


def _cli():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--einig", action="append",
                   help="einig-Wert(e) einschließen (Standard: beide), mehrfach angebbar")
    p.add_argument("--quelle", default=QUELLE_PFAD, help="Verzeichnis mit den beiden Dickhoff-PDFs")
    p.add_argument("--ziel", default=str(ZIEL_DIR))
    p.add_argument("--pruefliste", default=str(PRUEFLISTE_PFAD),
                   help="andere Prüfliste (z. B. daten/pruefung_unsicher.csv)")
    a = p.parse_args()
    einig = tuple(a.einig) if a.einig else ("beide",)
    neu = erzeuge(a.pruefliste, a.ziel, a.quelle, einig)
    print(f"{neu} Prüfbilder neu gerendert nach {a.ziel}")


if __name__ == "__main__":
    _cli()
