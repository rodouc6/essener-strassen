"""Dickhoff, Essener Straßen (2015): Doppelseiten-Scans → Buchseiten-Text via OCR.

Je PDF-Seite: 300 dpi rendern, Bundsteg (weißer Mittelstreifen) suchen, dort in
linke/rechte Buchseite teilen, beide Hälften einzeln mit tesseract (deu) lesen.
Die Buchseitenzahl wird aus der laufenden Nummer abgeleitet; die im Scan gedruckte
Zahl dient nur der Kontrolle (sie fehlt im OCR gelegentlich).
"""
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

HIER = Path(__file__).resolve().parent
QUELLE = HIER.parent
SEITEN = HIER / "seiten"
LOG = HIER / "log"

# (PDF, erste Buchseite auf PDF-Seite 1, Seitenzahl)
BAENDE = [
    ("Dickhoff_Essener Straßen_2015_1.pdf", 2, 100),
    ("Dickhoff_Essener Straßen_2015_2.pdf", 202, 94),
]
MIN_TAL_REL = 0.012          # Bundsteg muss mind. 1,2 % der Bildbreite breit sein


def finde_bundsteg(a):
    """x-Position des Bundstegs; (x, talbreite_px, erkannt)."""
    h, w = a.shape
    band = a[int(h * 0.10):int(h * 0.92), :]
    dunkel = (band < 128).mean(axis=0)
    lo, hi = int(w * 0.38), int(w * 0.62)
    weiss = dunkel[lo:hi] < 0.002
    best_len, best, start = 0, None, None
    for i, v in enumerate(weiss):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start > best_len:
                best_len, best = i - start, (start + lo, i + lo)
            start = None
    if start is not None and len(weiss) - start > best_len:
        best_len, best = len(weiss) - start, (start + lo, len(weiss) + lo)
    if best is None or best_len < w * MIN_TAL_REL:
        return w // 2, best_len, False
    return (best[0] + best[1]) // 2, best_len, True


def ocr(png_pfad, ziel_ohne_endung):
    subprocess.run(
        ["tesseract", str(png_pfad), str(ziel_ohne_endung), "-l", "deu", "--psm", "3"],
        check=True, capture_output=True,
        env={"PATH": "/usr/bin:/bin", "OMP_THREAD_LIMIT": "1"})


def verarbeite(auftrag):
    pdf, pdf_seite, buchseite_links = auftrag
    tmp = LOG / f"tmp_{pdf_seite}_{buchseite_links}"
    subprocess.run(["pdftoppm", "-f", str(pdf_seite), "-l", str(pdf_seite),
                    "-r", "300", "-gray", "-png", str(QUELLE / pdf), str(tmp)],
                   check=True, capture_output=True)
    treffer = sorted(LOG.glob(f"tmp_{pdf_seite}_{buchseite_links}-*.png"))
    if not treffer:
        return {"pdf_seite": pdf_seite, "fehler": "kein Rendering"}
    png = treffer[0]
    bild = Image.open(png).convert("L")
    x, talbreite, erkannt = finde_bundsteg(np.asarray(bild))
    w, h = bild.size
    ergebnis = {"pdf": pdf, "pdf_seite": pdf_seite, "schnitt_x": x,
                "talbreite": talbreite, "bundsteg_erkannt": erkannt, "breite": w}
    for versatz, (links, rechts) in enumerate([(0, x), (x, w)]):
        buchseite = buchseite_links + versatz
        haelfte = LOG / f"h_{buchseite}.png"
        bild.crop((links, 0, rechts, h)).save(haelfte)
        ocr(haelfte, SEITEN / f"s{buchseite:03d}")
        haelfte.unlink()
    png.unlink()
    return ergebnis


def main():
    auftraege = []
    for pdf, erste, n in BAENDE:
        for i in range(1, n + 1):
            auftraege.append((pdf, i, erste + (i - 1) * 2))
    SEITEN.mkdir(parents=True, exist_ok=True)
    LOG.mkdir(parents=True, exist_ok=True)
    fertig = 0
    with ProcessPoolExecutor(max_workers=10) as pool, \
            open(LOG / "bundsteg.tsv", "w", encoding="utf-8") as prot:
        prot.write("pdf\tpdf_seite\tschnitt_x\tbreite\ttalbreite\terkannt\n")
        for r in pool.map(verarbeite, auftraege):
            fertig += 1
            if "fehler" in r:
                print(f"FEHLER PDF-Seite {r['pdf_seite']}: {r['fehler']}", flush=True)
                continue
            prot.write(f"{r['pdf']}\t{r['pdf_seite']}\t{r['schnitt_x']}\t{r['breite']}"
                       f"\t{r['talbreite']}\t{'ja' if r['bundsteg_erkannt'] else 'NEIN'}\n")
            prot.flush()
            if fertig % 10 == 0:
                print(f"{fertig}/{len(auftraege)} Doppelseiten fertig", flush=True)
    print(f"Fertig: {fertig} Doppelseiten → {len(list(SEITEN.glob('*.txt')))} Buchseiten")


if __name__ == "__main__":
    sys.exit(main())
