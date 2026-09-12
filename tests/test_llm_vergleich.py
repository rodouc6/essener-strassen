import csv
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


def _parser():
    strassen = [
        {"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausen", "strassenklasse": "Gemeindestraße",
         "namensgruppe": "Stadt und Ort", "verweis_auf": "", "buchseite": 23, "status": "automatisch"},
        {"schl_nr": "00002", "lemma": "Abteistraße", "stadtteile": "Werden", "strassenklasse": "Bundesstraße",
         "namensgruppe": "Lagebezeichnung", "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
        {"schl_nr": "00004", "lemma": "Nur Parser", "stadtteile": "", "strassenklasse": "", "namensgruppe": "",
         "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
        {"schl_nr": "00099", "lemma": "Andere Seite", "stadtteile": "X", "strassenklasse": "Y", "namensgruppe": "Z",
         "verweis_auf": "", "buchseite": 40, "status": "automatisch"},
    ]
    namen = [
        {"schl_nr": "00001", "stadium": 1, "gueltig_ab": "1898", "datum_praezision": "vor", "name": "Victoriastraße (tlw.)", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00001", "stadium": 2, "gueltig_ab": "1902-05-16", "datum_praezision": "tag", "name": "Aachener Straße", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00002", "stadium": 1, "gueltig_ab": "1501", "datum_praezision": "jahrhundert", "name": "Abteistraße", "ist_urspruenglich": "wahr"},
    ]
    return strassen, namen


def _modell_antwort(**aenderungen):
    a = _antwort()
    for schl, felder in aenderungen.items():
        e = next(x for x in a["eintraege"] if lv._schl_nr(x["schl_nr"]) == schl)
        e.update(felder)
    return a


def test_feldwert_kopf_stadium_eintrag_und_fehlend():
    s, n = lv.als_struktur(*_parser())
    assert lv.feldwert(s, n, "00001", "lemma") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_1_datum") == "vor 1898"
    assert lv.feldwert(s, n, "00001", "stadium_2_name") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_2") == "1902-05-16 Aachener Straße"
    assert lv.feldwert(s, n, "00001", "eintrag") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_3_name") is None
    assert lv.feldwert(s, n, "00007", "lemma") is None


def test_pruefliste_beide_modelle_einig_gegen_parser_steht_oben():
    qwen = _modell_antwort(**{"00001": {"lemma": "Aachenerstraße"}})
    mistral = _modell_antwort(**{"00001": {"lemma": "Aachenerstraße"}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: mistral}}})
    erste = zeilen[0]
    assert (erste["schl_nr"], erste["feld"], erste["einig"]) == ("00001", "lemma", "beide")
    assert (erste["wert_parser"], erste["wert_qwen"], erste["wert_mistral"]) == ("Aachener Straße", "Aachenerstraße", "Aachenerstraße")
    assert erste["status_parser"] == "automatisch" and erste["korrektur"] == "" and erste["beleg"] == ""


def test_pruefliste_nur_ein_modell_weicht_ab_fuellt_anderes_mit_eigenem_wert():
    qwen = _modell_antwort(**{"00001": {"stadtteile": ["Frohnhausen", "Holsterhausen"]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    z = next(x for x in zeilen if x["feld"] == "stadtteile" and x["schl_nr"] == "00001")
    assert z["einig"] == "eines"
    assert z["wert_qwen"] == "Frohnhausen; Holsterhausen" and z["wert_mistral"] == "Frohnhausen"


def test_pruefliste_vollstaendigkeit_je_gelesener_seite():
    zeilen, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    felder = {(z["schl_nr"], z["feld"]): z for z in zeilen}
    fehlt = felder[("00004", "eintrag")]          # Parser hat, Modelle nicht
    assert fehlt["wert_parser"] == "Nur Parser" and fehlt["wert_qwen"] == "" and fehlt["einig"] == "beide"
    nur_modell = felder[("00003", "eintrag")]     # Modelle haben, Parser nicht
    assert nur_modell["wert_parser"] == "" and nur_modell["wert_qwen"] == "Achenbachstraße"
    assert ("00099", "eintrag") not in felder      # Seite 40 wurde nicht gelesen
    assert kz["qwen"]["eintraege_fehlend"] == 1 and kz["qwen"]["eintraege_nur_modell"] == 1


def test_pruefliste_datum_und_name_je_stadium():
    qwen = _modell_antwort(**{"00001": {"stadien": [
        {"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": False},
        {"datum": "16.05.1920", "name": "Aachener Straße", "urspruenglich": False}]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    z = next(x for x in zeilen if x["feld"] == "stadium_2_datum")
    assert (z["wert_parser"], z["wert_qwen"], z["wert_mistral"], z["einig"]) == ("1902-05-16", "1920-05-16", "1902-05-16", "eines")


def test_pruefliste_unlesbare_seite_eines_modells():
    zeilen, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _modell_antwort(**{"00001": {"lemma": "X"}})}},
                                                 "mistral": {"antworten": {23: {"buchseite": 23, "eintraege": None, "fehler": "unlesbar"}}}})
    z = next(x for x in zeilen if x["feld"] == "lemma" and x["schl_nr"] == "00001")
    assert z["einig"] == "unlesbar" and z["wert_mistral"] == ""
    assert kz["mistral"]["seiten_unlesbar"] == 1


def test_pruefliste_unvollstaendiger_eintrag_vergleicht_nur_kopf():
    # 00002 ist im Fixture unvollstaendig=true und hat dort nur 1 Stadium mit unlesbarem Datum
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    assert not [z for z in zeilen if z["schl_nr"] == "00002" and z["feld"].startswith("stadium")]


def test_kennzahlen_uebereinstimmung_je_feldtyp_und_status():
    _, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _modell_antwort(**{"00001": {"lemma": "X"}})}},
                                            "mistral": {"antworten": {23: _antwort()}}})
    q = kz["qwen"]
    assert q["seiten_gelesen"] == 1 and q["eintraege_modell"] == 3
    assert q["uebereinstimmung"]["automatisch"]["lemma"] == {"verglichen": 1, "gleich": 0}
    assert q["uebereinstimmung"]["unsicher"]["lemma"] == {"verglichen": 1, "gleich": 1}   # 00002; 00004 fehlt beim Modell
    assert q["datum_nicht_normalisierbar"] == 1
    md = lv.formatiere_kennzahlen_md(kz)
    assert "qwen" in md and "Status" in md and "verändern den Status nicht" in md


def test_schreibe_pruefliste_spalten(tmp_path):
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    pfad = tmp_path / "pruefung_llm.csv"
    lv.schreibe_pruefliste(zeilen, pfad)
    with open(pfad, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        assert r.fieldnames == lv.FELDER_PRUEFLISTE
