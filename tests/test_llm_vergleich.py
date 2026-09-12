import json
from pathlib import Path

import pytest

from strassen import llm_vergleich as lv

FIXTURE = Path(__file__).parent / "fixtures" / "llm_antwort_beispiel.json"


def _antwort():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_normalisiere_kopffelder_in_datensatzform():
    strassen, namen, probleme = lv.normalisiere_antwort(_antwort())
    assert [s["schl_nr"] for s in strassen] == ["00001", "00002", "00003"]   # '1' -> '00001'
    a = strassen[0]
    assert a["lemma"] == "Aachener Straße" and a["stadtteile"] == "Frohnhausen"
    assert a["strassenklasse"] == "Gemeindestraße" and a["buchseite"] == 23
    assert a["status"] == lv.STATUS_MODELL
    assert strassen[2]["verweis_auf"] == "Achenbachweg"


def test_normalisiere_stadien_ueber_datum_lese_text():
    _, namen, _ = lv.normalisiere_antwort(_antwort())
    st = [n for n in namen if n["schl_nr"] == "00001"]
    assert [(n["stadium"], n["gueltig_ab"], n["datum_praezision"], n["name"], n["ist_urspruenglich"]) for n in st] == [
        (1, "1898", "vor", "Victoriastraße (tlw.)", "falsch"),
        (2, "1902-05-16", "tag", "Aachener Straße", "falsch")]


def test_normalisiere_meldet_nicht_normalisierbares_datum():
    _, namen, probleme = lv.normalisiere_antwort(_antwort())
    abtei = [n for n in namen if n["schl_nr"] == "00002"][0]
    assert (abtei["gueltig_ab"], abtei["datum_praezision"], abtei["ist_urspruenglich"]) == ("", "unbekannt", "wahr")
    assert probleme == [{"schl_nr": "00002", "buchseite": 23, "feld": "stadium_1_datum",
                         "text": "16. Jh.", "grund": "Datum nicht normalisierbar"}]


def test_normalisiere_markiert_unvollstaendige_eintraege():
    strassen, _, _ = lv.normalisiere_antwort(_antwort())
    assert lv.ist_unvollstaendig(strassen[1]) and not lv.ist_unvollstaendig(strassen[0])


def test_normalisiere_unlesbare_antwort_liefert_nichts():
    assert lv.normalisiere_antwort({"buchseite": 5, "eintraege": None, "fehler": "unlesbar"}) == ([], [], [])


def test_lade_antworten_indexiert_nach_buchseite(tmp_path):
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "s023.json").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    antworten = lv.lade_antworten(tmp_path, "m")
    assert list(antworten) == [23] and antworten[23]["buchseite"] == 23


@pytest.mark.parametrize("modell,kurz", [("inferenz-qwen3-8-27b", "qwen"), ("inferenz-mistral-small-4-119b", "mistral")])
def test_kurzname(modell, kurz):
    assert lv.kurzname(modell) == kurz


def test_kurzname_unbekannt():
    with pytest.raises(ValueError):
        lv.kurzname("gpt-x")
