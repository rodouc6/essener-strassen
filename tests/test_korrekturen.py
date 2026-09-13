"""Korrektur-Overlay: manuell gegen den Scan geprüfte Korrekturen (Spec 2026-09-12, 3.4)."""
import pytest

from strassen import korrekturen as ko


def _daten():
    strassen = [{"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausn", "strassenklasse": "Gemeindestraße",
                 "namensgruppe": "Stadt und Ort", "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
                {"schl_nr": "00002", "lemma": "Abteistraße", "stadtteile": "Werden", "strassenklasse": "Bundesstraße",
                 "namensgruppe": "Lagebezeichnung", "verweis_auf": "", "buchseite": 23, "status": "automatisch"}]
    namen = [{"schl_nr": "00001", "stadium": 1, "gueltig_ab": "1898", "datum_praezision": "vor", "name": "Victoriastraße (tlw.)", "ist_urspruenglich": "falsch"},
             {"schl_nr": "00001", "stadium": 2, "gueltig_ab": "1902-05-16", "datum_praezision": "tag", "name": "Aachener Straße", "ist_urspruenglich": "falsch"},
             {"schl_nr": "00002", "stadium": 1, "gueltig_ab": "1501", "datum_praezision": "jahrhundert", "name": "Abteistraße", "ist_urspruenglich": "wahr"}]
    return strassen, namen


def _k(schl, feld, alt, neu, **rest):
    return {"schl_nr": schl, "feld": feld, "wert_alt": alt, "wert_neu": neu, "beleg": rest.get("beleg", "x"),
            "quelle": rest.get("quelle", "goldstandard"), "datum": "2026-09-12"}


def test_kopffeld_korrigieren_setzt_status_geprueft():
    s, n = _daten()
    prot = ko.wende_an(s, n, [_k("00001", "stadtteile", "Frohnhausn", "Frohnhausen")])
    assert s[0]["stadtteile"] == "Frohnhausen" and s[0]["status"] == "geprueft"
    assert s[1]["status"] == "automatisch"
    assert prot == {"eintraege": 1, "korrekturen": 1}


def test_wert_alt_muss_zum_parser_passen():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00001.*stadtteile"):
        ko.wende_an(s, n, [_k("00001", "stadtteile", "Frohnhausen", "Holsterhausen")])


def test_unbekannte_schl_nr_bricht_ab():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00099"):
        ko.wende_an(s, n, [_k("00099", "lemma", "A", "B")])


def test_stadium_datum_und_name_aendern():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "16.05.1920"),
                       _k("00001", "stadium_2_name", "Aachener Straße", "Aachener Str.")])
    st = [z for z in n if z["schl_nr"] == "00001"]
    assert (st[1]["gueltig_ab"], st[1]["datum_praezision"], st[1]["name"]) == ("1920-05-16", "tag", "Aachener Str.")


def test_stadium_datum_wert_alt_in_stichprobenform():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler):
        ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "1898", "vor 1897")])   # ist 'vor 1898'
    ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "vor 1898", "vor 1897")])
    assert n[0]["gueltig_ab"] == "1897" and n[0]["datum_praezision"] == "vor"


def test_stadium_nachtragen_rueckt_folgende_auf():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "", "1900"), _k("00001", "stadium_2_name", "", "Zwischenname")])
    st = [(z["stadium"], z["gueltig_ab"], z["name"]) for z in n if z["schl_nr"] == "00001"]
    assert st == [(1, "1898", "Victoriastraße (tlw.)"), (2, "1900", "Zwischenname"), (3, "1902-05-16", "Aachener Straße")]


def test_stadium_nachtragen_braucht_datum_und_name():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="stadium_2"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_name", "", "Nur Name")])


def test_stadium_streichen_nummeriert_neu():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "vor 1898", ""), _k("00001", "stadium_1_name", "Victoriastraße (tlw.)", "")])
    st = [(z["stadium"], z["name"]) for z in n if z["schl_nr"] == "00001"]
    assert st == [(1, "Aachener Straße")]


def test_urspruenglich_aendern():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_1_urspruenglich", "falsch", "wahr")])
    assert n[0]["ist_urspruenglich"] == "wahr"


def test_bestaetigung_setzt_nur_status():
    s, n = _daten()
    prot = ko.wende_an(s, n, [_k("00001", "eintrag", "", "")])
    assert s[0]["status"] == "geprueft" and s[0]["stadtteile"] == "Frohnhausn"
    assert prot == {"eintraege": 1, "korrekturen": 1}


def test_bestaetigung_mit_werten_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler):
        ko.wende_an(s, n, [_k("00001", "eintrag", "", "x")])


def test_nicht_normalisierbares_datum_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="normalisierbar"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "Frühjahr 1902")])


def test_dublette_der_schl_nr_ist_mehrdeutig():
    s, n = _daten()
    s.append(dict(s[0]))
    with pytest.raises(ko.KorrekturFehler, match="mehrdeutig"):
        ko.wende_an(s, n, [_k("00001", "lemma", "Aachener Straße", "X")])


def test_lade_korrekturen_fehlende_datei_leer(tmp_path):
    assert ko.lade_korrekturen(tmp_path / "gibt_es_nicht.csv") == []


# --- Fix-Runde 1: precision-first-Lücken ---


def test_stadium_0_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler):
        ko.wende_an(s, n, [_k("00001", "stadium_0_name", "", "X")])


def test_nachtrag_ueber_erlaubte_position_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="stadium_9"):
        ko.wende_an(s, n, [_k("00001", "stadium_9_datum", "", "1600"),
                           _k("00001", "stadium_9_name", "", "X")])


def test_nachtrag_direkt_nach_ende_wird_angehaengt():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_3_datum", "", "1950"),
                       _k("00001", "stadium_3_name", "", "Neuname")])
    st = [(z["stadium"], z["name"]) for z in n if z["schl_nr"] == "00001"]
    assert st[-1] == (3, "Neuname")


def test_nachtrag_mit_leeren_werten_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="Nachtragen braucht Datum und Name mit Wert"):
        ko.wende_an(s, n, [_k("00001", "stadium_3_datum", "", ""),
                           _k("00001", "stadium_3_name", "", "")])


def test_lade_korrekturen_header_only_datei_leer(tmp_path):
    pfad = tmp_path / "korrekturen.csv"
    pfad.write_text(",".join(ko.FELDER_KORREKTUREN) + "\n", encoding="utf-8")
    assert ko.lade_korrekturen(pfad) == []


def test_lade_korrekturen_falsche_spalte_ist_fehler(tmp_path):
    pfad = tmp_path / "korrekturen.csv"
    spalten = list(ko.FELDER_KORREKTUREN)
    spalten[3] = "wert-neu"
    pfad.write_text(",".join(spalten) + "\n", encoding="utf-8")
    with pytest.raises(ko.KorrekturFehler):
        ko.lade_korrekturen(pfad)


def test_feldaenderung_und_nachtrag_am_gleichen_ziel():
    """Feldänderungen adressieren die Parser-Nummerierung (vor Streichen/Einfügen),
    Nachträge die gedruckte Zielposition (danach) — beide am selben Stadium 2:
    das umbenannte Parser-Stadium landet auf 3, das neu eingefügte auf 2."""
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_name", "Aachener Straße", "Aachener Str. (neu)"),
                       _k("00001", "stadium_2_datum", "", "1900"),
                       _k("00001", "stadium_2_name", "", "Zwischenname")])
    st = [(z["stadium"], z["name"], z["gueltig_ab"]) for z in n if z["schl_nr"] == "00001"]
    assert st == [(1, "Victoriastraße (tlw.)", "1898"),
                  (2, "Zwischenname", "1900"),
                  (3, "Aachener Str. (neu)", "1902-05-16")]


def test_datum_mit_hinweis_wird_abgelehnt():
    # lese_text stuft '32.08.1927' auf das Jahr zurück (Hinweis 'Datum: Tag ungültig');
    # das Overlay darf so etwas nicht stillschweigend als geprueft übernehmen.
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="nicht sauber lesbar"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "32.08.1927")])


def test_datum_ohne_doppelpunkt_bleibt_zulaessig():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "29.08.1927:")])
    ko.wende_an(*_daten(), [_k("00001", "stadium_2_datum", "1902-05-16", "29.08.1927")])
    assert (n[1]["gueltig_ab"], n[1]["datum_praezision"]) == ("1927-08-29", "tag")


# --- Overlay-Erweiterung 2026-09-13: buchseite, schl_nr, Neuanlage, vorm.-Stadium ---

def test_buchseite_korrigieren():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "buchseite", "23", "24")])
    assert s[0]["buchseite"] == 24 and s[0]["status"] == "geprueft"


def test_buchseite_wert_alt_muss_passen():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00001 buchseite"):
        ko.wende_an(s, n, [_k("00001", "buchseite", "22", "24")])


def _daten_mit_dublette():
    s, n = _daten()
    s.append({"schl_nr": "00002", "lemma": "Rebenranke", "stadtteile": "Fischlaken", "strassenklasse": "Gemeindestraße",
              "namensgruppe": "Botanik", "verweis_auf": "", "buchseite": 270, "status": "unsicher"})
    n.append({"schl_nr": "00002", "stadium": 1, "gueltig_ab": "1936-08-05", "datum_praezision": "tag",
              "name": "Rebenranke", "ist_urspruenglich": "falsch"})
    return s, n


def test_schl_nr_umbenennen_adressiert_dublette_ueber_lemma():
    s, n = _daten_mit_dublette()
    prot = ko.wende_an(s, n, [_k("00002", "schl_nr", "Rebenranke", "00003"),
                              _k("00003", "stadtteile", "Fischlaken", "Fischlaken; Werden")])
    reben = [z for z in s if z["lemma"] == "Rebenranke"][0]
    assert reben["schl_nr"] == "00003" and reben["status"] == "geprueft"
    assert reben["stadtteile"] == "Fischlaken; Werden"
    # Bei einer Dublette ist nicht entscheidbar, welche Stadien zu welchem Eintrag gehören:
    # sie bleiben unter der alten Nummer und werden per Streichen/Nachtrag zugeordnet.
    assert [z["schl_nr"] for z in n if z["name"] == "Rebenranke"] == ["00002"]
    abtei = [z for z in s if z["lemma"] == "Abteistraße"][0]
    assert abtei["schl_nr"] == "00002" and abtei["status"] == "automatisch"
    assert prot["eintraege"] == 1


def test_schl_nr_wert_alt_muss_lemma_eines_eintrags_sein():
    s, n = _daten_mit_dublette()
    with pytest.raises(ko.KorrekturFehler, match="00002 schl_nr"):
        ko.wende_an(s, n, [_k("00002", "schl_nr", "Gibtsnicht", "00003")])


def test_schl_nr_neu_darf_nicht_vergeben_sein():
    s, n = _daten_mit_dublette()
    with pytest.raises(ko.KorrekturFehler, match="00001"):
        ko.wende_an(s, n, [_k("00002", "schl_nr", "Rebenranke", "00001")])


def test_eintrag_neu_anlegen():
    s, n = _daten()
    prot = ko.wende_an(s, n, [
        _k("00099", "eintrag", "", "Neue Straße"),
        _k("00099", "buchseite", "", "57"),
        _k("00099", "stadtteile", "", "Werden"),
        _k("00099", "strassenklasse", "", "Gemeindestraße"),
        _k("00099", "namensgruppe", "", "Flurname"),
        _k("00099", "stadium_1_datum", "", "07.04.1978"),
        _k("00099", "stadium_1_name", "", "Neue Straße"),
    ])
    neu = [z for z in s if z["schl_nr"] == "00099"]
    assert len(neu) == 1 and neu[0] == {
        "schl_nr": "00099", "lemma": "Neue Straße", "stadtteile": "Werden", "strassenklasse": "Gemeindestraße",
        "namensgruppe": "Flurname", "verweis_auf": "", "buchseite": 57, "status": "geprueft"}
    st = [z for z in n if z["schl_nr"] == "00099"]
    assert [(z["stadium"], z["gueltig_ab"], z["name"]) for z in st] == [(1, "1978-04-07", "Neue Straße")]
    assert prot["eintraege"] == 1


def test_eintrag_neu_braucht_buchseite():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00099.*buchseite"):
        ko.wende_an(s, n, [_k("00099", "eintrag", "", "Neue Straße"),
                           _k("00099", "stadium_1_datum", "", "07.04.1978"),
                           _k("00099", "stadium_1_name", "", "Neue Straße")])


def test_eintrag_neu_bei_vorhandener_schl_nr_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00001.*eintrag"):
        ko.wende_an(s, n, [_k("00001", "eintrag", "", "Aachener Straße")])


def test_unbekannte_schl_nr_ohne_neuanlage_bricht_weiter_ab():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00099"):
        ko.wende_an(s, n, [_k("00099", "buchseite", "", "57")])


def test_vorm_stadium_ohne_datum_nachtragen():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "", "vorm."),
                       _k("00001", "stadium_1_name", "", "Bolsterbaum (tlw.)")])
    st = [z for z in n if z["schl_nr"] == "00001"]
    assert (st[0]["stadium"], st[0]["gueltig_ab"], st[0]["datum_praezision"], st[0]["name"],
            st[0]["ist_urspruenglich"]) == (1, "", "unbekannt", "Bolsterbaum (tlw.)", "falsch")
    assert [z["stadium"] for z in st] == [1, 2, 3] and st[1]["name"] == "Victoriastraße (tlw.)"


def test_vorm_nur_als_nachtrag_erlaubt():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00001 stadium_2_datum"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "vorm.")])


def test_schl_nr_umbenennen_eindeutig_nimmt_stadien_mit():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "schl_nr", "Aachener Straße", "00009")])
    assert s[0]["schl_nr"] == "00009" and s[0]["status"] == "geprueft"
    assert [z["schl_nr"] for z in n if z["name"] == "Aachener Straße"] == ["00009"]
    assert not [z for z in n if z["schl_nr"] == "00001"]


def test_dublette_nach_umbenennung_wird_korrigierbar():
    s, n = _daten_mit_dublette()
    ko.wende_an(s, n, [_k("00002", "schl_nr", "Rebenranke", "00003"),
                       _k("00002", "stadium_2_datum", "1936-08-05", ""),
                       _k("00002", "stadium_2_name", "Rebenranke", ""),
                       _k("00003", "stadium_1_datum", "", "05.08.1936"),
                       _k("00003", "stadium_1_name", "", "Rebenranke")])
    assert [(z["schl_nr"], z["stadium"], z["name"]) for z in n if z["schl_nr"] in ("00002", "00003")] == [
        ("00002", 1, "Abteistraße"), ("00003", 1, "Rebenranke")]


def test_urspr_stadium_ohne_datum_nachtragen():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00002", "stadium_1_datum", "", "urspr."),
                       _k("00002", "stadium_1_name", "", "Velberter Sträßchen")])
    st = [z for z in n if z["schl_nr"] == "00002"]
    assert (st[0]["gueltig_ab"], st[0]["datum_praezision"], st[0]["name"], st[0]["ist_urspruenglich"]) == (
        "", "unbekannt", "Velberter Sträßchen", "wahr")
    assert st[1]["name"] == "Abteistraße" and st[1]["stadium"] == 2
