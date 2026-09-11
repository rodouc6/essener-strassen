"""Die 17 Korrekturen der Goldstandard-Stichprobe (Entwicklungs-Stichprobe, 2026-09-11)
gegen den aktuellen Parser: Jede Korrektur ist entweder umgesetzt ODER der Eintrag ist
status=unsicher (precision-first: korrigiert oder gekennzeichnet, nie still falsch).

Braucht die lokalen OCR-Seiten (gitignored); ohne sie wird übersprungen."""
import csv
from collections import defaultdict
from pathlib import Path

import pytest

from strassen.erschliessen import main

WURZEL = Path(__file__).resolve().parent.parent
OCR = WURZEL / "ocr" / "seiten"
STICHPROBE = WURZEL / "docs" / "goldstandard" / "stichprobe.csv"

pytestmark = pytest.mark.skipif(not OCR.is_dir(), reason="ocr/seiten/ nur lokal vorhanden")


@pytest.fixture(scope="module")
def datensatz(tmp_path_factory):
    aus = tmp_path_factory.mktemp("daten")
    main(ocr_dir=str(OCR), ausgabe_dir=str(aus))
    strassen = {z["schl_nr"]: z for z in csv.DictReader(open(aus / "strassen.csv", encoding="utf-8"))}
    namen = defaultdict(dict)
    for z in csv.DictReader(open(aus / "namen.csv", encoding="utf-8")):
        namen[z["schl_nr"]][int(z["stadium"])] = z
    return strassen, namen


def _fehlerzeilen():
    with open(STICHPROBE, encoding="utf-8", newline="") as f:
        return [z for z in csv.DictReader(f) if z["korrekt"].strip().lower() == "nein"]


def _ist_wert(strassen, namen, schl, feld):
    if feld.startswith("stadium_"):
        _, n, art = feld.split("_")
        st = namen.get(schl, {}).get(int(n))
        if st is None:
            return None
        return st["gueltig_ab"] if art == "datum" else st["name"]
    return strassen.get(schl, {}).get(feld)


@pytest.mark.parametrize("zeile", _fehlerzeilen(), ids=lambda z: f"{z['schl_nr']}-{z['feld']}")
def test_korrektur_umgesetzt_oder_gekennzeichnet(datensatz, zeile):
    strassen, namen = datensatz
    schl = zeile["schl_nr"]
    assert schl in strassen, "Eintrag verschwunden"
    ist = _ist_wert(strassen, namen, schl, zeile["feld"])
    korrigiert = ist == zeile["korrektur"]
    gekennzeichnet = strassen[schl]["status"] == "unsicher"
    assert korrigiert or gekennzeichnet, f"ist={ist!r}, soll={zeile['korrektur']!r}, status={strassen[schl]['status']}"


def test_mindestens_zwoelf_korrekturen_umgesetzt(datensatz):
    """Sollwert aus der Spec: Alle Fehler außer reinem OCR-Rauschen (Spervogelweg:
    'Minnesängerr', '19862') sind durch Regeln behebbar — mindestens 12 von 17."""
    strassen, namen = datensatz
    umgesetzt = sum(1 for z in _fehlerzeilen()
                    if _ist_wert(strassen, namen, z["schl_nr"], z["feld"]) == z["korrektur"])
    assert umgesetzt >= 12, umgesetzt
