"""Goldstandard-Stichprobe: 50 Einträge Zeichen für Zeichen gegen den Original-Scan
prüfen, um eine bezifferte Feldfehlerquote zu ermitteln (Spec, Abschnitt 3, Stufe 3).

Zwei Unterbefehle:

  ziehen     zieht deterministisch 50 Einträge aus daten/strassen.csv (geschichtet:
             40 status=automatisch, 10 status=unsicher — beide Gruppen müssen
             vertreten sein, weil sie unterschiedliche Fehlerprofile haben dürften),
             schreibt je geprüftem Prüffeld eine Zeile nach
             docs/goldstandard/stichprobe.csv (Prüfspalten korrekt/korrektur LEER —
             Eingabemaske für die manuelle Prüfung) und rendert je Eintrag einen
             Scan-Ausschnitt zur bequemen Prüfung nach docs/goldstandard/scans/
             (gitignored — urheberrechtlich geschützte Seitenbilder, nur lokal).

  auswerten  liest die vom Prüfer ausgefüllte stichprobe.csv, berechnet je Feldtyp
             und gesamt geprüft/korrekt/Fehlerquote und schreibt
             docs/goldstandard/ergebnis.md.

Die Prüfung selbst ist ein manueller Schritt (macht der Projektinhaber); dieses
Modul bereitet nur Ziehung, Scan-Ausschnitte und Auswertung vor.
"""
import argparse
import csv
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from strassen.ocr_lauf import BAENDE, finde_bundsteg

HIER = Path(__file__).resolve().parent      # strassen/
WURZEL = HIER.parent                        # Repo-Wurzel

STRASSEN_PFAD = WURZEL / "daten" / "strassen.csv"
NAMEN_PFAD = WURZEL / "daten" / "namen.csv"
GOLDSTANDARD_DIR = WURZEL / "docs" / "goldstandard"
STICHPROBE_PFAD = GOLDSTANDARD_DIR / "stichprobe.csv"
SCANS_DIR = GOLDSTANDARD_DIR / "scans"
ERGEBNIS_PFAD = GOLDSTANDARD_DIR / "ergebnis.md"

# Externe Quelle (nicht Teil dieses Repos, wie ADRESSBUCH_PFAD in
# veroeffentlichen.py) — die beiden Dickhoff-PDFs, per --quelle überschreibbar.
QUELLE_PFAD = ("/home/christos/Projekte/00_Datensammlung/"
               "Dickhoff_Essener Straßen_2015_zusammenfügen")

SEED = 1936                # Erhebungsstand des Adressbuchs — s. CLAUDE.md/README
ANZAHL_AUTOMATISCH = 40
ANZAHL_UNSICHER = 10

FELDER_STICHPROBE = ["schl_nr", "lemma", "buchseite", "band", "pdf_seite", "haelfte",
                     "feld", "wert", "korrekt", "korrektur"]

# Reihenfolge der Kopf-Prüffelder je Eintrag (immer geprüft, auch wenn leer —
# eine leere Angabe im Datensatz gegen eine tatsächlich leere Stelle im Scan zu
# verifizieren ist selbst eine Prüfung, kein Nichts).
_KOPF_FELDER = ["schl_nr", "lemma", "stadtteile", "strassenklasse",
                "namensgruppe", "verweis_auf"]

_FELDTYP_STADIUM = re.compile(r"^stadium_\d+_(datum|name)$")


def buchseite_zu_scan(buchseite) -> tuple:
    """(band, pdf_seite, haelfte) für eine Buchseite.

    Buchseite b -> Band 1 (b<=201), PDF-Seite (b-2)//2+1, sonst Band 2,
    PDF-Seite (b-202)//2+1. Je PDF-Seite: links = gerade Buchseite, rechts =
    ungerade (s. Auftragsbeschreibung / BAENDE in ocr_lauf.py)."""
    b = int(buchseite)
    if b <= 201:
        band, basis = 1, 2
    else:
        band, basis = 2, 202
    pdf_seite = (b - basis) // 2 + 1
    haelfte = "links" if b % 2 == 0 else "rechts"
    return band, pdf_seite, haelfte


def formatiere_datum(praezision: str, gueltig_ab: str) -> str:
    """Menschenlesbare Form eines Namensstadien-Datums zur Prüfung gegen den Scan."""
    if praezision == "unbekannt":
        return "(urspr., kein Datum)"
    if praezision in ("vor", "nach"):
        return f"{praezision} {gueltig_ab}"
    return gueltig_ab  # 'tag' (volles ISO-Datum) oder 'jahr'


def lade_strassen(pfad=STRASSEN_PFAD) -> list:
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def lade_namen_je_schluessel(pfad=NAMEN_PFAD) -> dict:
    je_schluessel = defaultdict(list)
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        for zeile in csv.DictReader(f):
            je_schluessel[zeile["schl_nr"]].append(zeile)
    for schl_nr, stadien in je_schluessel.items():
        stadien.sort(key=lambda z: int(z["stadium"]))
    return dict(je_schluessel)


def ziehe_schichtung(strassen: list, seed: int = SEED,
                      anzahl_automatisch: int = ANZAHL_AUTOMATISCH,
                      anzahl_unsicher: int = ANZAHL_UNSICHER) -> list:
    """Deterministisch geschichtete Stichprobe: anzahl_automatisch Einträge mit
    status=automatisch + anzahl_unsicher mit status=unsicher. Beide Gruppen müssen
    im Ergebnis vertreten sein, sonst wird abgebrochen (zu wenige Einträge einer
    Gruppe wäre ein Datenfehler, kein Stichprobenproblem)."""
    automatisch = [z for z in strassen if z["status"] == "automatisch"]
    unsicher = [z for z in strassen if z["status"] == "unsicher"]
    if len(automatisch) < anzahl_automatisch:
        raise ValueError(f"nur {len(automatisch)} status=automatisch, "
                          f"{anzahl_automatisch} gefordert")
    if len(unsicher) < anzahl_unsicher:
        raise ValueError(f"nur {len(unsicher)} status=unsicher, "
                          f"{anzahl_unsicher} gefordert")
    rng = random.Random(seed)
    gezogen = (rng.sample(automatisch, anzahl_automatisch)
               + rng.sample(unsicher, anzahl_unsicher))
    gezogen.sort(key=lambda z: int(z["schl_nr"]))
    return gezogen


def baue_pruefzeilen(eintrag: dict, stadien: list) -> list:
    """Eine Zeile je Prüffeld für einen gezogenen Eintrag (ohne korrekt/korrektur —
    die füllt der Prüfer). band/pdf_seite/haelfte aus der Buchseite abgeleitet."""
    band, pdf_seite, haelfte = buchseite_zu_scan(eintrag["buchseite"])
    basis = {"schl_nr": eintrag["schl_nr"], "lemma": eintrag["lemma"],
              "buchseite": eintrag["buchseite"], "band": band,
              "pdf_seite": pdf_seite, "haelfte": haelfte,
              "korrekt": "", "korrektur": ""}
    zeilen = []
    for feld in _KOPF_FELDER:
        zeilen.append({**basis, "feld": feld, "wert": eintrag.get(feld, "")})
    for stadium in stadien:
        n = stadium["stadium"]
        zeilen.append({**basis, "feld": f"stadium_{n}_datum",
                        "wert": formatiere_datum(stadium["datum_praezision"],
                                                  stadium["gueltig_ab"])})
        zeilen.append({**basis, "feld": f"stadium_{n}_name", "wert": stadium["name"]})
    return zeilen


def scan_dateiname(schl_nr: str, buchseite) -> str:
    return f"schlnr_{schl_nr}_s{int(buchseite):03d}.png"


def rendere_ausschnitt(band: int, pdf_seite: int, haelfte: str, quelle_dir,
                        ziel_png: Path) -> None:
    """Rendert die PDF-Seite bei 150 dpi, findet den Bundsteg (s. ocr_lauf.py) und
    schneidet die passende Hälfte als PNG nach ziel_png zu."""
    pdf_name = BAENDE[band - 1][0]
    tmp_praefix = ziel_png.parent / f"_tmp_{band}_{pdf_seite}"
    subprocess.run(
        ["pdftoppm", "-f", str(pdf_seite), "-l", str(pdf_seite), "-r", "150",
         "-gray", "-png", str(Path(quelle_dir) / pdf_name), str(tmp_praefix)],
        check=True, capture_output=True)
    treffer = sorted(ziel_png.parent.glob(f"_tmp_{band}_{pdf_seite}-*.png"))
    if not treffer:
        raise RuntimeError(f"kein Rendering für Band {band}, PDF-Seite {pdf_seite}")
    png = treffer[0]
    try:
        bild = Image.open(png).convert("L")
        x, _, _ = finde_bundsteg(np.asarray(bild))
        w, h = bild.size
        ausschnitt = bild.crop((0, 0, x, h) if haelfte == "links" else (x, 0, w, h))
        ausschnitt.save(ziel_png)
    finally:
        png.unlink()


def ziehen(quelle_dir=QUELLE_PFAD, strassen_pfad=STRASSEN_PFAD, namen_pfad=NAMEN_PFAD,
           stichprobe_pfad=STICHPROBE_PFAD, scans_dir=SCANS_DIR) -> list:
    strassen = lade_strassen(strassen_pfad)
    namen_je_schluessel = lade_namen_je_schluessel(namen_pfad)
    gezogen = ziehe_schichtung(strassen)

    scans_dir = Path(scans_dir)
    scans_dir.mkdir(parents=True, exist_ok=True)
    Path(stichprobe_pfad).parent.mkdir(parents=True, exist_ok=True)

    alle_zeilen = []
    for i, eintrag in enumerate(gezogen, 1):
        stadien = namen_je_schluessel.get(eintrag["schl_nr"], [])
        alle_zeilen.extend(baue_pruefzeilen(eintrag, stadien))

        band, pdf_seite, haelfte = buchseite_zu_scan(eintrag["buchseite"])
        ziel = scans_dir / scan_dateiname(eintrag["schl_nr"], eintrag["buchseite"])
        rendere_ausschnitt(band, pdf_seite, haelfte, quelle_dir, ziel)
        print(f"{i}/{len(gezogen)}: Schl.-Nr. {eintrag['schl_nr']} "
              f"({eintrag['status']}) -> {ziel.name}", flush=True)

    with open(Path(stichprobe_pfad), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FELDER_STICHPROBE, extrasaction="ignore")
        w.writeheader()
        w.writerows(alle_zeilen)

    n_automatisch = sum(1 for z in gezogen if z["status"] == "automatisch")
    n_unsicher = sum(1 for z in gezogen if z["status"] == "unsicher")
    print(f"\nGezogen: {len(gezogen)} Einträge ({n_automatisch} automatisch, "
          f"{n_unsicher} unsicher), {len(alle_zeilen)} Prüfzeilen -> {stichprobe_pfad}")
    return gezogen


def _feldtyp(feld: str) -> str:
    """stadium_3_datum -> stadium_datum (Gruppierung über alle Stadiennummern)."""
    if _FELDTYP_STADIUM.match(feld):
        return re.sub(r"^stadium_\d+_", "stadium_", feld)
    return feld


def lade_stichprobe(pfad=STICHPROBE_PFAD) -> list:
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def berechne_statistik(zeilen: list) -> dict:
    """Je Feldtyp und gesamt: geprüft, korrekt, Fehlerquote (%). Zeilen mit leerem
    korrekt-Feld (noch nicht geprüft) werden ignoriert."""
    ausgefuellt = [z for z in zeilen if (z.get("korrekt") or "").strip()]
    je_feldtyp = defaultdict(lambda: {"geprueft": 0, "korrekt": 0})
    for z in ausgefuellt:
        typ = _feldtyp(z["feld"])
        je_feldtyp[typ]["geprueft"] += 1
        if z["korrekt"].strip().lower() == "ja":
            je_feldtyp[typ]["korrekt"] += 1

    def _mit_fehlerquote(d):
        geprueft, korrekt = d["geprueft"], d["korrekt"]
        fehlerquote = (geprueft - korrekt) / geprueft * 100 if geprueft else 0.0
        return {"geprueft": geprueft, "korrekt": korrekt, "fehlerquote": fehlerquote}

    gesamt = _mit_fehlerquote({"geprueft": len(ausgefuellt),
                                "korrekt": sum(1 for z in ausgefuellt
                                               if z["korrekt"].strip().lower() == "ja")})
    return {"je_feldtyp": {typ: _mit_fehlerquote(d) for typ, d in sorted(je_feldtyp.items())},
            "gesamt": gesamt,
            "zeilen_gesamt": len(zeilen),
            "zeilen_ausgefuellt": len(ausgefuellt)}


def formatiere_ergebnis_md(statistik: dict) -> str:
    zeilen = ["# Goldstandard-Ergebnis\n",
              f"{statistik['zeilen_ausgefuellt']} von {statistik['zeilen_gesamt']} "
              "Prüfzeilen ausgefüllt.\n",
              "| Feldtyp | geprüft | korrekt | Fehlerquote |",
              "|---|--:|--:|--:|"]
    for typ, d in statistik["je_feldtyp"].items():
        zeilen.append(f"| {typ} | {d['geprueft']} | {d['korrekt']} | "
                       f"{d['fehlerquote']:.1f} % |")
    g = statistik["gesamt"]
    zeilen.append(f"| **gesamt** | **{g['geprueft']}** | **{g['korrekt']}** | "
                   f"**{g['fehlerquote']:.1f} %** |")
    return "\n".join(zeilen) + "\n"


def auswerten(stichprobe_pfad=STICHPROBE_PFAD, ergebnis_pfad=ERGEBNIS_PFAD) -> str:
    zeilen = lade_stichprobe(stichprobe_pfad)
    if not zeilen:
        raise SystemExit(f"{stichprobe_pfad} ist leer — erst 'ziehen' ausführen.")
    unausgefuellt = sum(1 for z in zeilen if not (z.get("korrekt") or "").strip())
    anteil = unausgefuellt / len(zeilen)
    if anteil > 0.10:
        raise SystemExit(
            f"Abbruch: {unausgefuellt}/{len(zeilen)} Prüfzeilen ({anteil:.0%}) "
            "haben noch kein 'korrekt' (ja/nein) — mehr als 10 % offen. Erst "
            f"{stichprobe_pfad} vollständig ausfüllen, dann erneut auswerten.")
    statistik = berechne_statistik(zeilen)
    bericht = formatiere_ergebnis_md(statistik)
    Path(ergebnis_pfad).parent.mkdir(parents=True, exist_ok=True)
    Path(ergebnis_pfad).write_text(bericht, encoding="utf-8")
    return bericht


def _cli():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="befehl", required=True)

    p_ziehen = sub.add_parser("ziehen", help="50 Einträge ziehen, Scan-Ausschnitte rendern")
    p_ziehen.add_argument("--quelle", default=QUELLE_PFAD,
                           help="Verzeichnis mit den beiden Dickhoff-PDFs")

    sub.add_parser("auswerten", help="ausgefüllte stichprobe.csv auswerten")

    a = p.parse_args()
    if a.befehl == "ziehen":
        ziehen(quelle_dir=a.quelle)
    elif a.befehl == "auswerten":
        print(auswerten())


if __name__ == "__main__":
    sys.exit(_cli())
