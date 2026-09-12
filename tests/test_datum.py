import re

from strassen.datum import (SATZENDE, DATUMSSTEMPEL, lese_datum, MONATE,
                            ist_schwach, position_erlaubt)


_SATZ = re.compile(SATZENDE)


def _treffer(text):
    m = DATUMSSTEMPEL.search(text)
    assert m, text
    return m


def _stempel(text):
    return lese_datum(_treffer(text))


# --- Satzende (Regel 4) ---

def test_satzende_nach_wort_vor_grossbuchstabe():
    assert _SATZ.search("Kronenstraße. Die Pottgasse")


def test_kein_satzende_nach_st_abkuerzung():
    """St. Annental, Schl.-Nr. 02727, S. 309: 'St. Annental' wurde zu 'St'."""
    assert not _SATZ.search("St. Annental")


def test_kein_satzende_nach_roemischer_zahl():
    """Gerswidastraße, Schl.-Nr. 01022, S. 127: 'II. Weberstraße' wurde zu 'II'."""
    for zahl in ["I", "II", "III", "IV"]:
        assert not _SATZ.search(f"{zahl}. Weberstraße"), zahl


def test_kein_satzende_nach_ziffer():
    """Die Tagesziffer eines Datums ('26. Mai') ist kein Satzende."""
    assert not _SATZ.search("26. Mai 1939")


def test_satzende_am_stringende():
    assert _SATZ.search("Am Schroer.")


# --- sichere Datumsformen (Regeln 7, 8 und Bestand) ---

def test_tagesdatum():
    d = _stempel("26. Mai 1939: Kamerunstraße")
    assert (d.gueltig_ab, d.praezision, d.hinweis, d.trenner) == ("1939-05-26", "tag", "", ":")


def test_numerisches_datum():
    """Schlenterstraße, Schl.-Nr. 02774, S. 291: '29.08.1927: Schlenterstraße'."""
    d = _stempel("29.08.1927: Schlenterstraße")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1927-08-29", "tag", "")


def test_jahrhundert():
    """Bungertstraße 00491 (S. 85) '16. Jahrhundert:', Oefte 03731 (S. 251) '9. Jahrh.:',
    Limbecker Straße 01971 (S. 223) 'im 16. Jahrhundert:'."""
    assert _stempel("16. Jahrhundert: Bungertstraße").gueltig_ab == "1501"
    assert _stempel("16. Jahrhundert: Bungertstraße").praezision == "jahrhundert"
    assert _stempel("9. Jahrh.: Oefte").gueltig_ab == "0801"
    assert _stempel("im 16. Jahrhundert: Lyndenbeker Straße").praezision == "jahrhundert"


def test_qualifier_vor_nach_jahr():
    assert _stempel("vor 1826: II. Weberstraße").praezision == "vor"
    assert _stempel("nach 1900: X").praezision == "nach"
    assert _stempel("etwa 1921: Nelkenstraße").praezision == "jahr"
    assert _stempel("um 1850: X").gueltig_ab == "1850"


def test_blosses_jahr():
    d = _stempel("1902: Barkhofstraße")
    assert (d.gueltig_ab, d.praezision) == ("1902", "jahr")


def test_stempel_setzt_nicht_mitten_in_ziffernfolge_an():
    """'19862:' (Spervogelweg 02949, S. 306) darf nicht als '9862:' oder '1986' gelesen werden."""
    assert DATUMSSTEMPEL.search("Minnesängerr 27. September 19862: Spervogelweg") is None


def test_monate_vollstaendig():
    assert len(MONATE) == 12 and MONATE["März"] == 3


# --- tolerante Formen (Regeln 6, 14, 15, 16, 18) ---

def test_komma_nach_tag_mit_hinweis():
    """Eskenshof, Schl.-Nr. 00817, S. 110: '13, Juni 1973: Eskenshof'."""
    d = _stempel("13, Juni 1973: Eskenshof")
    assert d.gueltig_ab == "1973-06-13"
    assert d.hinweis == "Datum: Komma nach Tag"


def test_ohne_doppelpunkt_mit_hinweis():
    """Berghausbusch, Schl.-Nr. 00471, S. 84: '11. Dezember 1974 Berghausbusch'."""
    d = _stempel("11. Dezember 1974 Berghausbusch")
    assert d.gueltig_ab == "1974-12-11"
    assert d.trenner == ""
    assert d.hinweis == "Datum ohne Doppelpunkt"


def test_semikolon_und_komma_statt_doppelpunkt():
    """Hobirkheide 01320 (S. 162) '05. Juni 1934; Hobirkheide';
    Havelring 01416 (S. 152) '07. September 1960, Havelring'."""
    assert _stempel("05. Juni 1934; Hobirkheide").trenner == ";"
    assert _stempel("05. Juni 1934; Hobirkheide").hinweis == "Datum ohne Doppelpunkt"
    assert _stempel("07. September 1960, Havelring").trenner == ","


def test_monatsname_mit_einem_ocr_fehler_wird_korrigiert():
    """Deilbachufer 00608 (S. 95) 'Novemner'; Einbleckstraße 00745 'Nobember';
    Möllneys Nocken 02149 'Aprit'; Bonsiepen 02515 'Mat'."""
    assert _stempel("13. Novemner 1900: Uferstraße").gueltig_ab == "1900-11-13"
    assert _stempel("13. Novemner 1900: Uferstraße").hinweis == "Monatsname OCR-korrigiert"
    assert _stempel("28. Nobember 1895: Einbleckstraße").gueltig_ab == "1895-11-28"
    assert _stempel("13. Aprit 1908: Möllneys Nocken").gueltig_ab == "1908-04-13"
    assert _stempel("18. Mat 1989: Bonsiepen").gueltig_ab == "1989-05-18"


def test_unbekanntes_monatswort_reduziert_auf_jahr():
    """Abschlussreview: eigener Hinweis — der Tag ist hier nicht das Problem."""
    d = _stempel("13. Xyzabc 1900: Uferstraße")
    assert (d.gueltig_ab, d.praezision) == ("1900", "jahr")
    assert d.hinweis == "Datum: Monat unlesbar"


def test_ungueltiger_tag_reduziert_auf_jahr():
    """Graudenzstraße, Schl.-Nr. 01073, S. 146: '085. Februar 1929'."""
    d = _stempel("085. Februar 1929: Heinrich-Lersch-Straße")
    assert (d.gueltig_ab, d.praezision) == ("1929", "jahr")
    assert d.hinweis == "Datum: Tag ungültig"


def test_ungueltiger_numerischer_monat_reduziert_auf_jahr():
    d = _stempel("29.18.1927: X")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1927", "jahr", "Datum: Tag ungültig")


def test_doppeljahr_mit_hinweis():
    """Henglerplatz, Schl.-Nr. 01273, S. 155: 'etwa 1910/11: Henglerplatz'."""
    d = _stempel("etwa 1910/11: Henglerplatz")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1910", "jahr", "Datum: Doppeljahr")


def test_mehrere_hinweise_werden_verbunden():
    d = _stempel("13, Novemner 1900 Uferstraße")
    assert d.hinweis == "Datum ohne Doppelpunkt; Datum: Komma nach Tag; Monatsname OCR-korrigiert"


def test_unscharf_eindeutig_verlangt_eindeutigkeit():
    from strassen.datum import unscharf_eindeutig
    assert unscharf_eindeutig("Novemner", MONATE) == "November"
    assert unscharf_eindeutig("Jun", MONATE) == "Juni"
    assert unscharf_eindeutig("Xyz", MONATE) is None
    assert unscharf_eindeutig("Mai", MONATE) is None      # exakt gleich zählt nicht als Distanz 1


def test_datumsstempel_anonym_hat_keine_benannten_gruppen():
    """DATUMSSTEMPEL_ANONYM wird für Lookaheads gebraucht (kopf._STADIUM), wo
    dieselbe benannte Gruppe nicht zweimal im selben Muster vorkommen darf."""
    from strassen.datum import DATUMSSTEMPEL_ANONYM
    assert "(?P<" not in DATUMSSTEMPEL_ANONYM
    re.compile(DATUMSSTEMPEL_ANONYM + DATUMSSTEMPEL_ANONYM)


# --- gemeinsame Regeln für kopf und namen (Abschlussreview) ---

def test_ist_schwach_unterscheidet_starke_und_schwache_stempel():
    assert ist_schwach(_treffer("1902: Barkhofstraße")) is True        # bloßes Jahr
    assert ist_schwach(_treffer("13. Juni 1973 Eskenshof")) is True    # ohne Doppelpunkt
    assert ist_schwach(_treffer("vor 1826: II. Weberstraße")) is False  # Qualifier
    assert ist_schwach(_treffer("18. September 1926: St. Annental")) is False


def test_position_erlaubt_nur_am_kettenanfang_oder_nach_trenner():
    assert position_erlaubt("1902: X", 0) is True
    assert position_erlaubt("A. Straße, 1902: X", len("A. Straße, ")) is True
    assert position_erlaubt("A. Straße; 1902: X", len("A. Straße; ")) is True
    assert position_erlaubt("Am 25. Juli 1516 wurde", len("Am ")) is False


# --- lese_text ---

from strassen.datum import lese_text


def test_lese_text_tagesdatum_numerisch_und_wortform():
    assert lese_text("29.08.1927")[:2] == ("1927-08-29", "tag")
    assert lese_text("16. Mai 1902:")[:2] == ("1902-05-16", "tag")


def test_lese_text_qualifier_jahr_jahrhundert():
    assert lese_text("vor 1898")[:2] == ("1898", "vor")
    assert lese_text("um 1900")[:2] == ("1900", "jahr")
    assert lese_text("im 16. Jahrhundert")[:2] == ("1501", "jahrhundert")
    assert lese_text("1927")[:2] == ("1927", "jahr")


def test_lese_text_leer_und_unpassend():
    assert lese_text("")[:2] == ("", "unbekannt")
    assert lese_text("16. Jh.") is None
    assert lese_text("Frühjahr 1920") is None
