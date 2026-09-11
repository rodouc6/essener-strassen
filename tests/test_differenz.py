import csv
from pathlib import Path

from strassen.differenz import vergleiche, formatiere_bericht

_S = ["schl_nr", "lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf", "buchseite", "status"]
_N = ["schl_nr", "stadium", "gueltig_ab", "datum_praezision", "name", "ist_urspruenglich"]


def _schreibe(d: Path, strassen, namen):
    d.mkdir(parents=True, exist_ok=True)
    for name, felder, zeilen in [("strassen.csv", _S, strassen), ("namen.csv", _N, namen)]:
        with open(d / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=felder)
            w.writeheader()
            w.writerows(zeilen)


def _s(schl, lemma, status="automatisch", **k):
    z = {"schl_nr": schl, "lemma": lemma, "stadtteile": "X", "strassenklasse": "Gemeindestraße",
         "namensgruppe": "Hofname", "verweis_auf": "", "buchseite": "1", "status": status}
    z.update(k)
    return z


def _n(schl, stadium, datum, name, praez="tag"):
    return {"schl_nr": schl, "stadium": str(stadium), "gueltig_ab": datum,
            "datum_praezision": praez, "name": name, "ist_urspruenglich": "falsch"}


def test_stadium_gewonnen_und_verloren(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A"), _s("2", "B")],
              [_n("2", 1, "1900-01-01", "Alt")])
    _schreibe(tmp_path / "neu", [_s("1", "A"), _s("2", "B")],
              [_n("1", 1, "1939-05-26", "Kamerunstraße")])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["stadium_gewonnen"] == [{"schl_nr": "1", "lemma": "A", "neu": "1939-05-26 Kamerunstraße"}]
    assert d["stadium_verloren"] == [{"schl_nr": "2", "lemma": "B", "alt": "1900-01-01 Alt"}]


def test_datum_und_name_veraendert(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [_n("1", 1, "1920", "II", "jahr")])
    _schreibe(tmp_path / "neu", [_s("1", "A")], [_n("1", 1, "1920-10-01", "II. Weberstraße")])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["datum_veraendert"] == [{"schl_nr": "1", "lemma": "A", "stadium": "1",
                                      "alt": "1920 (jahr)", "neu": "1920-10-01 (tag)"}]
    assert d["name_veraendert"] == [{"schl_nr": "1", "lemma": "A", "stadium": "1",
                                     "alt": "II", "neu": "II. Weberstraße"}]


def test_kopffeld_und_status(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A", stadtteile=""), _s("2", "B", status="unsicher")], [])
    _schreibe(tmp_path / "neu", [_s("1", "A", stadtteile="Kray", status="unsicher"), _s("2", "B")], [])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["kopffeld_veraendert"] == [{"schl_nr": "1", "lemma": "A", "feld": "stadtteile",
                                         "alt": "", "neu": "Kray"}]
    assert d["status_zu_unsicher"] == [{"schl_nr": "1", "lemma": "A"}]
    assert d["status_zu_automatisch"] == [{"schl_nr": "2", "lemma": "B"}]


def test_eintrag_neu_und_entfallen(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [])
    _schreibe(tmp_path / "neu", [_s("2", "B")], [])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["eintrag_neu"] == [{"schl_nr": "2", "lemma": "B"}]
    assert d["eintrag_entfallen"] == [{"schl_nr": "1", "lemma": "A"}]


def test_verweis_auf_und_buchseite_werden_verglichen(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A", verweis_auf="", buchseite="1")], [])
    _schreibe(tmp_path / "neu", [_s("1", "A", verweis_auf="B", buchseite="1")], [])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["kopffeld_veraendert"] == [{"schl_nr": "1", "lemma": "A", "feld": "verweis_auf",
                                         "alt": "", "neu": "B"}]


def test_ist_urspruenglich_veraendert(tmp_path):
    alt_zeile = _n("1", 1, "1920", "II", "jahr")
    neu_zeile = dict(alt_zeile)
    neu_zeile["ist_urspruenglich"] = "wahr"
    _schreibe(tmp_path / "alt", [_s("1", "A")], [alt_zeile])
    _schreibe(tmp_path / "neu", [_s("1", "A")], [neu_zeile])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["datum_veraendert"] == [{"schl_nr": "1", "lemma": "A", "stadium": "1",
                                      "alt": "1920 (jahr)", "neu": "1920 (jahr, urspr.)"}]
    assert d["name_veraendert"] == []


def test_stadium_einfuegung_in_der_mitte_kein_falscher_wechsel(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")],
              [_n("1", 1, "1900-01-01", "Alt A"), _n("1", 2, "1950-01-01", "Alt B")])
    _schreibe(tmp_path / "neu", [_s("1", "A")],
              [_n("1", 1, "1900-01-01", "Alt A"), _n("1", 2, "1920-01-01", "Mittelname"),
               _n("1", 3, "1950-01-01", "Alt B")])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["stadium_gewonnen"] == [{"schl_nr": "1", "lemma": "A", "neu": "1920-01-01 Mittelname"}]
    assert d["stadium_verloren"] == []
    assert d["datum_veraendert"] == []
    assert d["name_veraendert"] == []


def test_bericht_enthaelt_zaehlung_und_zeilen(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [])
    _schreibe(tmp_path / "neu", [_s("1", "A")], [_n("1", 1, "1939-05-26", "Kamerunstraße")])
    md = formatiere_bericht(vergleiche(tmp_path / "alt", tmp_path / "neu"))
    assert "| Stadium gewonnen | 1 |" in md
    assert "Kamerunstraße" in md
