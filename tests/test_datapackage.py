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
