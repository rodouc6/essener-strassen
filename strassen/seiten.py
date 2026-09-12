"""Buchseiten als Graustufen-PNG für die unabhängige LLM-Lesung rendern.

Spec 2026-09-12, Abschnitt 3.1. Eine Datei je Buchseite unter llm/seiten/sNNN.png
(gitignored — Seitenbilder sind urheberrechtlich geschützt). Idempotent: vorhandene
Dateien werden übersprungen.

  python3 -m strassen.seiten [--quelle DIR] [--seiten 23-30,45]
"""
import argparse
from pathlib import Path

from strassen.goldstandard import QUELLE_PFAD, buchseite_zu_scan, rendere_ausschnitt

WURZEL = Path(__file__).resolve().parent.parent
SEITEN_DIR = WURZEL / "llm" / "seiten"
ERSTE_SEITE, LETZTE_SEITE = 2, 388   # Scan-Umfang, s. README „Quelle"
DPI = 300                            # 150 dpi (Goldstandard-Ausschnitte) reichen
                                     # den Modellen für 'Str.-Kl.:' und Stempel nicht


def seiten_dateiname(buchseite) -> str:
    return f"s{int(buchseite):03d}.png"


def parse_seitenbereich(text) -> list:
    """'23-30' -> 23..30, '23,45' -> [23, 45], None/leer -> alle Buchseiten."""
    if not text:
        return list(range(ERSTE_SEITE, LETZTE_SEITE + 1))
    seiten = []
    for teil in text.split(","):
        teil = teil.strip()
        if "-" in teil:
            a, b = teil.split("-", 1)
            seiten.extend(range(int(a), int(b) + 1))
        else:
            seiten.append(int(teil))
    return seiten


def rendere_seiten(seiten, ziel_dir=SEITEN_DIR, quelle_dir=QUELLE_PFAD, dpi=DPI,
                   render=rendere_ausschnitt) -> list:
    """Rendert alle noch fehlenden Buchseiten; gibt die neu erzeugten Pfade zurück."""
    ziel_dir = Path(ziel_dir)
    ziel_dir.mkdir(parents=True, exist_ok=True)
    neu = []
    for buchseite in seiten:
        ziel = ziel_dir / seiten_dateiname(buchseite)
        if ziel.exists():
            continue
        band, pdf_seite, haelfte = buchseite_zu_scan(buchseite)
        render(band, pdf_seite, haelfte, quelle_dir, ziel, dpi=dpi)
        neu.append(ziel)
    return neu


def _cli():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quelle", default=QUELLE_PFAD, help="Verzeichnis mit den beiden Dickhoff-PDFs")
    p.add_argument("--seiten", help="Buchseiten, z. B. 23-30,45 (Standard: alle)")
    p.add_argument("--ziel", default=str(SEITEN_DIR))
    a = p.parse_args()
    neu = rendere_seiten(parse_seitenbereich(a.seiten), a.ziel, a.quelle)
    print(f"{len(neu)} Seiten neu gerendert nach {a.ziel}")


if __name__ == "__main__":
    _cli()
