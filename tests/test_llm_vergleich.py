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


def test_normalisiere_meldet_stadien_die_keine_liste_sind():
    antwort = {"buchseite": 23, "eintraege": [
        {"schl_nr": "1", "lemma": "X", "stadien": {"datum": "1900", "name": "X"}}]}
    strassen, namen, probleme = lv.normalisiere_antwort(antwort)
    assert namen == []
    assert probleme == [{"schl_nr": "00001", "buchseite": 23, "feld": "stadien",
                         "text": str({"datum": "1900", "name": "X"})[:200], "grund": lv.GRUND_STADIEN}]


def test_normalisiere_ueberspringt_stadium_das_kein_dict_ist():
    antwort = {"buchseite": 23, "eintraege": [
        {"schl_nr": "1", "lemma": "X", "stadien": ["nicht ein dict"]}]}
    strassen, namen, probleme = lv.normalisiere_antwort(antwort)
    assert namen == []
    assert probleme == [{"schl_nr": "00001", "buchseite": 23, "feld": "stadium_1",
                         "text": "nicht ein dict", "grund": lv.GRUND_STADIEN}]


def test_normalisiere_buchseite_null_wird_null():
    antwort = {"buchseite": None, "eintraege": [{"schl_nr": "1", "lemma": "X", "stadien": []}]}
    strassen, _, _ = lv.normalisiere_antwort(antwort)
    assert strassen[0]["buchseite"] == 0


def test_normalisiere_eintrag_ohne_schl_nr():
    antwort = {"buchseite": 23, "eintraege": [{"lemma": "X", "stadien": []}]}
    strassen, _, _ = lv.normalisiere_antwort(antwort)
    assert strassen[0]["schl_nr"] == ""


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
    # 00002 ist im Fixture unvollstaendig=true; regulärer Stadien-Abgleich entfällt daher,
    # aber die Problem-Zeile für das nicht normalisierbare Datum "16. Jh." erscheint trotzdem
    # (Spec 3.3: ein Datenproblem signalisiert einen Muster-/Prompt-Fehler, kein Kuratierungsfall).
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    stadium_zeilen = [z for z in zeilen if z["schl_nr"] == "00002" and z["feld"].startswith("stadium")]
    assert [z["feld"] for z in stadium_zeilen] == ["stadium_1_datum"]
    assert stadium_zeilen[0]["wert_qwen"] == "16. Jh. (nicht normalisierbar)"


def test_pruefliste_verlorenes_stadium_zaehlt_datum_und_name_als_abweichung():
    # Parser hat 2 Stadien zu 00001, das Modell nur das erste (identische Signatur) —
    # das verlorene 2. Stadium muss Datum UND Name als Abweichung zählen, nicht als 'gleich'.
    qwen = _modell_antwort(**{"00001": {"stadien": [
        {"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": False}]}})
    _, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    q = kz["qwen"]["uebereinstimmung"]["automatisch"]
    assert q["stadium_datum"] == {"verglichen": 2, "gleich": 1}
    assert q["stadium_name"] == {"verglichen": 2, "gleich": 1}


def test_pruefliste_nur_ist_urspruenglich_geaendert_erzeugt_eigene_zeile():
    # Datum und Name von Stadium 1 bleiben gleich, nur 'urspruenglich' wechselt falsch -> wahr.
    qwen = _modell_antwort(**{"00001": {"stadien": [
        {"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": True},
        {"datum": "16.05.1902:", "name": "Aachener Straße", "urspruenglich": False}]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    stadium1_zeilen = [z for z in zeilen if z["schl_nr"] == "00001" and z["feld"].startswith("stadium_1")]
    assert [z["feld"] for z in stadium1_zeilen] == ["stadium_1_urspruenglich"]
    z = stadium1_zeilen[0]
    assert (z["wert_parser"], z["wert_qwen"]) == ("falsch", "wahr")


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


def _stichprobe():
    basis = {"lemma": "Aachener Straße", "status": "automatisch", "buchseite": "23"}
    return [
        {**basis, "schl_nr": "00001", "feld": "lemma", "wert": "Aachener Straße", "korrekt": "ja", "korrektur": ""},
        {**basis, "schl_nr": "00001", "feld": "stadium_2_datum", "wert": "1902-05-16", "korrekt": "ja", "korrektur": ""},
        {**basis, "schl_nr": "00001", "feld": "stadtteile", "wert": "Frohnhausn", "korrekt": "nein", "korrektur": "Frohnhausen"},
        {**basis, "schl_nr": "00001", "feld": "stadium_3_name", "wert": "", "korrekt": "nein", "korrektur": "Neuer Name"},   # nachgetragen
        {**basis, "schl_nr": "00001", "feld": "verweis_auf", "wert": "", "korrekt": "", "korrektur": ""},                   # ungeprüft
    ]


def test_messe_goldstandard_zaehlt_treffer_gegen_soll():
    s, n, _ = lv.normalisiere_antwort(_antwort())
    st = lv.messe_goldstandard(_stichprobe(), lv.als_struktur(s, n))
    assert st["gesamt"] == {"geprueft": 4, "korrekt": 3, "fehlerquote": 25.0}
    assert st["je_feldtyp"]["stadium_datum"]["korrekt"] == 1
    assert st["fehlend_gesamt"] == 1 and st["fehlend_gefunden"] == 0
    assert st["fehler"] == [{"schl_nr": "00001", "lemma": "Aachener Straße", "status": "automatisch",
                             "feld": "stadium_3_name", "soll": "Neuer Name", "ist": None}]


def test_formatiere_ergebnis_llm_md_je_modell():
    s, n, _ = lv.normalisiere_antwort(_antwort())
    st = lv.messe_goldstandard(_stichprobe(), lv.als_struktur(s, n))
    md = lv.formatiere_ergebnis_llm_md({"qwen": st})
    assert "## Modell `qwen`" in md and "25.0 %" in md


def test_uebernehmen_erzeugt_korrekturzeilen_und_ueberspringt_dubletten():
    pruefliste = [
        {"schl_nr": "00001", "feld": "lemma", "wert_parser": "Aachener Straße", "korrektur": "Aachenerstraße", "beleg": "Aachenerstraße"},
        {"schl_nr": "00001", "feld": "stadium_2_datum", "wert_parser": "1902-05-16", "korrektur": "", "beleg": ""},
        {"schl_nr": "00002", "feld": "stadium_2", "wert_parser": "", "korrektur": "1930 | Neuer Name", "beleg": "1930: Neuer Name"},
    ]
    vorhanden = [{"schl_nr": "00001", "feld": "lemma", "wert_alt": "Aachener Straße", "wert_neu": "Aachenerstraße",
                  "beleg": "", "quelle": "llm-lauf", "datum": "2026-09-01"}]
    neu = lv.uebernehmen(pruefliste, vorhanden, datum="2026-09-13")
    assert neu == [
        {"schl_nr": "00002", "feld": "stadium_2_datum", "wert_alt": "", "wert_neu": "1930", "beleg": "1930: Neuer Name", "quelle": "llm-lauf", "datum": "2026-09-13"},
        {"schl_nr": "00002", "feld": "stadium_2_name", "wert_alt": "", "wert_neu": "Neuer Name", "beleg": "1930: Neuer Name", "quelle": "llm-lauf", "datum": "2026-09-13"},
    ]


def test_uebernehmen_lehnt_korrektur_fuer_fehlenden_parser_eintrag_ab():
    with pytest.raises(ValueError):
        lv.uebernehmen([{"schl_nr": "00003", "feld": "eintrag", "wert_parser": "", "korrektur": "Achenbachstraße", "beleg": ""}], [], "2026-09-13")


def test_finde_modelle_ueberspringt_unbekannte_ordner(tmp_path, capsys):
    for name in ("inferenz-qwen3-8-27b", "inferenz-mistral-small-4-119b", "fremd"):
        (tmp_path / name).mkdir()
    modelle = lv.finde_modelle(tmp_path)
    assert modelle == {"qwen": "inferenz-qwen3-8-27b", "mistral": "inferenz-mistral-small-4-119b"}
    assert "fremd" in capsys.readouterr().out


def _antwort_seite(buchseite, schl_nr):
    return {"buchseite": buchseite, "modell": "m", "zeitstempel": "", "prompt_hash": "", "rohtext": "", "fehler": "",
            "eintraege": [{"schl_nr": schl_nr, "lemma": "X", "stadtteile": [], "strassenklasse": [],
                           "namensgruppe": "", "verweis_auf": "", "stadien": [], "unvollstaendig": False}]}


def test_daten_fuer_goldstandard_nur_seiten_der_stichprobe():
    antworten = {23: _antwort(), 40: _antwort_seite(40, "00099")}
    stichprobe = [{"buchseite": "23"}]
    strassen, namen = lv.daten_fuer_goldstandard(antworten, stichprobe)
    assert {s["schl_nr"] for s in strassen} == {"00001", "00002", "00003"}


def test_daten_fuer_goldstandard_meldet_schl_nr_dublette():
    antworten = {23: _antwort(), 40: _antwort_seite(40, "00001")}
    stichprobe = [{"buchseite": "23"}, {"buchseite": "40"}]
    with pytest.raises(ValueError):
        lv.daten_fuer_goldstandard(antworten, stichprobe)


def test_lade_antworten_meldet_abgeschnittene_datei(tmp_path):
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "s023.json").write_text('{"buchseite": 23, "eintrae', encoding="utf-8")
    with pytest.raises(ValueError, match="nicht lesbar"):
        lv.lade_antworten(tmp_path, "m")


def test_pruefliste_hat_offene_korrekturen(tmp_path):
    leer = tmp_path / "leer.csv"
    gefuellt = tmp_path / "voll.csv"
    kopf = ",".join(lv.FELDER_PRUEFLISTE)
    leer.write_text(f"{kopf}\n00001,23,lemma,A,B,B,unsicher,beide,,\n", encoding="utf-8")
    gefuellt.write_text(f"{kopf}\n00001,23,lemma,A,B,B,unsicher,beide,Berichtigt,Beleg\n", encoding="utf-8")
    assert lv.pruefliste_hat_offene_korrekturen(gefuellt) is True
    assert lv.pruefliste_hat_offene_korrekturen(leer) is False
    assert lv.pruefliste_hat_offene_korrekturen(tmp_path / "fehlt.csv") is False


def test_pruefe_prompt_hashes():
    assert lv.pruefe_prompt_hashes({23: {"prompt_hash": "a"}, 24: {"prompt_hash": "a"}}) == {"a"}
    assert lv.pruefe_prompt_hashes({23: {"prompt_hash": "a"}, 24: {"prompt_hash": "b"}}) == {"a", "b"}
    assert lv.pruefe_prompt_hashes({23: {"prompt_hash": ""}, 24: {}}) == set()


def test_uebernehmen_lehnt_nicht_zuordenbares_stadium_ab():
    with pytest.raises(ValueError, match="stadium_\\?"):
        lv.uebernehmen([{"schl_nr": "00001", "feld": "stadium_?", "wert_parser": "",
                         "korrektur": "1930 | Neuer Name", "beleg": ""}], [], "2026-09-13")


def test_normalisiere_meldet_eingeschraenkt_lesbares_datum_behaelt_aber_den_wert():
    antwort = {"buchseite": 23, "eintraege": [
        {"schl_nr": "1", "lemma": "X", "stadien": [{"datum": "32.08.1927", "name": "X"}]}]}
    _, namen, probleme = lv.normalisiere_antwort(antwort)
    assert (namen[0]["gueltig_ab"], namen[0]["datum_praezision"]) == ("1927", "jahr")
    assert probleme == [{"schl_nr": "00001", "buchseite": 23, "feld": "stadium_1_datum",
                         "text": "32.08.1927", "grund": lv.GRUND_DATUM_EINGESCHRAENKT}]


def test_pruefliste_zeigt_rohtext_eines_eingeschraenkt_lesbaren_datums():
    qwen = _modell_antwort(**{"00001": {"stadien": [
        {"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": False},
        {"datum": "32.08.1927", "name": "Aachener Straße", "urspruenglich": False}]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}},
                                                "mistral": {"antworten": {23: _antwort()}}})
    z = next(x for x in zeilen if x["schl_nr"] == "00001" and x["feld"] == "stadium_2_datum")
    assert z["wert_qwen"] == "32.08.1927 (eingeschränkt lesbar)"


def test_kennzahlen_enthalten_stadium_urspruenglich():
    _, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}},
                                            "mistral": {"antworten": {23: _antwort()}}})
    assert kz["qwen"]["uebereinstimmung"]["automatisch"]["stadium_urspruenglich"] == {"verglichen": 2, "gleich": 2}


def test_normalisiere_entfernt_weichtrennstriche_aus_werten():
    # Beobachtete Antwortform (Kalibrierung Task 11, Seite 100/mistral): das Modell gibt
    # ein am Zeilenende getrenntes Wort mit einem Weichtrennstrich U+00AD zurück
    # ('Kriegs\xaderinnerung'). Das ist Drucksatz, kein gelesenes Zeichen — es darf den
    # Wert nicht von dem des Parsers unterscheiden.
    antwort = {"buchseite": 100, "eintraege": [{
        "schl_nr": "00678", "lemma": "Düppel\xadstraße", "stadtteile": ["Hutt\xadrop"],
        "strassenklasse": ["Gemeinde\xadstraße"], "namensgruppe": "Stadt und Ort, Kriegs\xaderinnerung",
        "verweis_auf": "", "unvollstaendig": False,
        "stadien": [{"datum": "21. April 1911", "name": "Düppel\xadstraße", "urspruenglich": False}]}]}
    strassen, namen, probleme = lv.normalisiere_antwort(antwort)
    assert strassen[0]["namensgruppe"] == "Stadt und Ort, Kriegserinnerung"
    assert strassen[0]["lemma"] == "Düppelstraße"
    assert strassen[0]["stadtteile"] == "Huttrop" and strassen[0]["strassenklasse"] == "Gemeindestraße"
    assert namen[0]["name"] == "Düppelstraße" and probleme == []


@pytest.mark.parametrize("datum", ["urspr.", "urspr.:", "ursprünglich", " urspr. "])
def test_normalisiere_liest_urspr_marker_im_datumsfeld_als_kein_datum(datum):
    # Beobachtete Antwortform (Kalibrierung Task 11, Seiten 300/260/220, mistral): das
    # Modell schreibt den Marker 'urspr.' ins Datumsfeld statt allein in 'urspruenglich'.
    # Der Marker sagt genau, dass es kein Datum gibt — das ist eine Formfrage, kein
    # unlesbares Datum, und darf keine Prüfzeile 'Datum nicht normalisierbar' erzeugen.
    antwort = {"buchseite": 300, "eintraege": [{
        "schl_nr": "02851", "lemma": "Schwelmhöfe", "stadtteile": ["Kray"],
        "strassenklasse": ["Gemeindestraße"], "namensgruppe": "Familienname",
        "verweis_auf": "", "unvollstaendig": False,
        "stadien": [{"datum": datum, "name": "Hofstraße", "urspruenglich": True}]}]}
    _, namen, probleme = lv.normalisiere_antwort(antwort)
    assert probleme == []
    assert namen[0]["gueltig_ab"] == "" and namen[0]["datum_praezision"] == "unbekannt"
    assert namen[0]["ist_urspruenglich"] == "wahr"


def test_normalisiere_meldet_urspr_mit_unlesbarem_zusatz_weiterhin():
    # Nur der nackte Marker gilt als 'kein Datum'; bleibt daneben Text stehen, ist das
    # ein echtes Formproblem und muss sichtbar bleiben (precision-first).
    antwort = {"buchseite": 300, "eintraege": [{
        "schl_nr": "02851", "lemma": "Schwelmhöfe", "stadtteile": [], "strassenklasse": [],
        "namensgruppe": "", "verweis_auf": "", "unvollstaendig": False,
        "stadien": [{"datum": "urspr.: Hofstraße", "name": "Hofstraße", "urspruenglich": True}]}]}
    _, _, probleme = lv.normalisiere_antwort(antwort)
    assert [p["grund"] for p in probleme] == [lv.GRUND_DATUM]
