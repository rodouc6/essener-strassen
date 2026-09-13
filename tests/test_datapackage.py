"""IMPORTANT 4: datapackage.json muss gültiges JSON bleiben und darf keine
primaryKey-Deklaration mehr tragen (3 echte schl_nr-Dubletten verletzen sie) —
stattdessen ein Hinweis in der schl_nr-Feldbeschreibung.
"""
import json
from pathlib import Path

PFAD = Path(__file__).resolve().parent.parent / "datapackage.json"


def _lade():
    return json.loads(PFAD.read_text(encoding="utf-8"))


def test_ist_gueltiges_json():
    _lade()


def test_keine_primary_key_deklaration_mehr():
    paket = _lade()
    for ressource in paket["resources"]:
        assert "primaryKey" not in ressource["schema"]


def test_schl_nr_feldbeschreibung_nennt_die_dubletten():
    paket = _lade()
    strassen = next(r for r in paket["resources"] if r["name"] == "strassen")
    schl_nr_feld = next(f for f in strassen["schema"]["fields"] if f["name"] == "schl_nr")
    beschreibung = schl_nr_feld["description"]
    assert "nicht strikt eindeutig" in beschreibung
    for nummer in ("02402", "02568", "03448"):
        assert nummer in beschreibung


def test_foreign_key_auf_strassen_bleibt_erhalten():
    paket = _lade()
    namen = next(r for r in paket["resources"] if r["name"] == "namen")
    assert namen["schema"]["foreignKeys"][0]["reference"]["resource"] == "strassen"


def test_datum_praezision_enum_enthaelt_jahrhundert():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    namen = next(r for r in paket["resources"] if r["name"] == "namen")
    feld = next(f for f in namen["schema"]["fields"] if f["name"] == "datum_praezision")
    assert "jahrhundert" in feld["constraints"]["enum"]


def test_datapackage_hat_korrekturen_ressource_mit_feldern():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    r = next(r for r in paket["resources"] if r["name"] == "korrekturen")
    assert r["path"] == "daten/korrekturen.csv"
    assert [f["name"] for f in r["schema"]["fields"]] == ["schl_nr", "feld", "wert_alt", "wert_neu", "beleg", "quelle", "datum"]


def test_status_beschreibung_nennt_alle_drei_werte():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    strassen = next(r for r in paket["resources"] if r["name"] == "strassen")
    feld = next(f for f in strassen["schema"]["fields"] if f["name"] == "status")
    assert feld["constraints"]["enum"] == ["automatisch", "geprueft", "unsicher"]
    assert "geprueft" in feld.get("description", "") and "Overlay" in feld["description"]


def test_korrekturen_csv_hat_kopfzeile():
    kopf = Path("daten/korrekturen.csv").read_text(encoding="utf-8").splitlines()[0]
    assert kopf == "schl_nr,feld,wert_alt,wert_neu,beleg,quelle,datum"


def test_vorgehensseite_nennt_alle_schritte():
    text = Path("docs/vorgehen.md").read_text(encoding="utf-8")
    for stichwort in ["2026-08-20", "Goldstandard", "Entwicklungs-Stichprobe", "Parser-Reparatur",
                      "LLM-Lesung", "Option A", "Korrektur-Overlay", "Parser-Runde 2"]:
        assert stichwort in text
