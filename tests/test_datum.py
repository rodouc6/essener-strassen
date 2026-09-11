import re

import pytest

from strassen.datum import SATZENDE, DATUMSSTEMPEL, lese_datum, MONATE


_SATZ = re.compile(SATZENDE)


def _stempel(text):
    m = DATUMSSTEMPEL.search(text)
    assert m, text
    return lese_datum(m)


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
    assert DATUMSSTEMPEL.search("Minnesängerr 27. September 19862: Spervogelweg") is None \
        or DATUMSSTEMPEL.search("Minnesängerr 27. September 19862: Spervogelweg").group("jahr_tag") is None


def test_monate_vollstaendig():
    assert len(MONATE) == 12 and MONATE["März"] == 3
