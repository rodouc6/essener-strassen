"""Gesamtlauf: OCR-Seiten → strassen.csv, namen.csv, pruefung.csv.

pruefung.csv ist das Sichtbarkeits-Netz (precision-first): lieber ein Eintrag
zu viel darin als einer, der stillschweigend verloren geht oder unmarkiert
veröffentlicht wird. Drei Gründe landen dort:
  - "Anker ohne Lemma": die Segmentierung fand eine Schlüsselnummer-Angabe,
    aber kein davorstehendes Lemma (segmentierung.segmentiere(verworfene=...)).
  - "Lemma auffällig (Länge)": das Lemma ist ungewöhnlich lang (>4 Wörter oder
    >40 Zeichen) — der Eintrag wird trotzdem veröffentlicht, nur als
    status="unsicher" statt "automatisch" markiert (Kennzeichnung, kein
    Ausschluss).
  - "kein Namensstadium erkannt": der Kopf ist lesbar, aber weder ein
    Namensstadium noch ein Verweis ("Siehe ...") ließ sich finden.
  - "keine Schlüsselnummer lesbar": parse_kopf() fand keinen Kopf im Rumpf.
"""
import re
import sys
from pathlib import Path

from strassen.aufbereitung import aufbereiten
from strassen.segmentierung import segmentiere
from strassen.kopf import parse_kopf
from strassen.namen import parse_namenskette
from strassen.ausgabe import schreibe_strassen, schreibe_namen, schreibe_pruefung

_VERWEIS = re.compile(r"Siehe\s+([A-ZÄÖÜ][^.,;]{2,60})")
# Auffälliges Lemma: die weit überwiegende Mehrheit echter Straßennamen ist
# kurz. Alles darüber wird nicht verworfen, sondern nur zur manuellen Prüfung
# markiert (Zusatzauftrag Controller) — precision-first heißt hier: sichtbar
# machen statt schweigend zu vertrauen.
_LEMMA_MAX_WOERTER = 4
_LEMMA_MAX_ZEICHEN = 40


def _lemma_auffaellig(lemma: str) -> bool:
    return len(lemma) > _LEMMA_MAX_ZEICHEN or len(lemma.split()) > _LEMMA_MAX_WOERTER


def main(ocr_dir="ocr/seiten", ausgabe_dir="daten"):
    ziel = Path(ausgabe_dir)
    ziel.mkdir(parents=True, exist_ok=True)

    verworfene = []
    eintraege = segmentiere(aufbereiten(ocr_dir), verworfene=verworfene)

    strassen, namen, pruefung = [], [], []

    for buchseite, kontext in verworfene:
        pruefung.append({"buchseite": buchseite, "lemma_roh": "",
                         "grund": "Anker ohne Lemma", "rohtext": kontext[:200]})

    for e in eintraege:
        k = parse_kopf(e.rumpf)
        if k is None:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "keine Schlüsselnummer lesbar",
                             "rohtext": e.rumpf[:200]})
            continue

        auffaellig = _lemma_auffaellig(e.lemma_roh)
        if auffaellig:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "Lemma auffällig (Länge)",
                             "rohtext": e.rumpf[:200]})

        mv = _VERWEIS.search(e.rumpf)
        stadien = parse_namenskette(k.rest)
        if not stadien and not mv:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "kein Namensstadium erkannt",
                             "rohtext": e.rumpf[:200]})

        strassen.append({
            "schl_nr": k.schl_nr, "lemma": e.lemma_roh,
            "stadtteile": "; ".join(k.stadtteile),
            "strassenklasse": "; ".join(k.strassenklassen),
            "namensgruppe": k.namensgruppe,
            "verweis_auf": mv.group(1).strip() if mv else "",
            "buchseite": e.buchseite,
            "status": "unsicher" if auffaellig else "automatisch"})
        for s in stadien:
            namen.append({"schl_nr": k.schl_nr, "stadium": s.stadium,
                          "gueltig_ab": s.gueltig_ab,
                          "datum_praezision": s.datum_praezision, "name": s.name,
                          "ist_urspruenglich": "wahr" if s.ist_urspruenglich else "falsch"})

    schreibe_strassen(strassen, ziel / "strassen.csv")
    schreibe_namen(namen, ziel / "namen.csv")
    schreibe_pruefung(pruefung, ziel / "pruefung.csv")
    kennzahlen = {"eintraege": len(eintraege), "strassen": len(strassen),
                  "namensstadien": len(namen), "pruefung": len(pruefung)}
    print(kennzahlen)
    return kennzahlen


if __name__ == "__main__":
    sys.exit(0 if main() else 0)
