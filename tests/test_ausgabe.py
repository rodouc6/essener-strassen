import csv
from strassen.ausgabe import schreibe_strassen, schreibe_namen, schreibe_pruefung, FELDER_STRASSEN, FELDER_PRUEFUNG


def test_strassen_csv_hat_festgelegte_spalten(tmp_path):
    p = tmp_path / "strassen.csv"
    schreibe_strassen([{"schl_nr": "01838", "lemma": "Kütings Garten",
                        "stadtteile": "Freisenbruch", "strassenklasse": "Gemeindestraße",
                        "namensgruppe": "Lagebezeichnung", "verweis_auf": "",
                        "buchseite": 211, "status": "automatisch"}], p)
    with open(p, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert list(zeilen[0].keys()) == FELDER_STRASSEN
    assert zeilen[0]["lemma"] == "Kütings Garten"


def test_keine_erlaeuterungstexte_in_der_ausgabe(tmp_path):
    """Rechtliche Zusage der Spec: nur Fakten werden veröffentlicht."""
    p = tmp_path / "strassen.csv"
    schreibe_strassen([{"schl_nr": "01818", "lemma": "Kronenstraße",
                        "stadtteile": "Stadtkern", "strassenklasse": "Gemeindestraße",
                        "namensgruppe": "Essener Geschichte", "verweis_auf": "",
                        "buchseite": 210, "status": "automatisch"}], p)
    inhalt = p.read_text(encoding="utf-8")
    assert "Gasthaus" not in inhalt and "Chronik" not in inhalt
    assert len(inhalt.splitlines()) == 2


def test_namen_csv_verknuepft_ueber_schluesselnummer(tmp_path):
    p = tmp_path / "namen.csv"
    schreibe_namen([{"schl_nr": "01838", "stadium": 2, "gueltig_ab": "1926-06-01",
                     "datum_praezision": "tag", "name": "Klosterstraße",
                     "ist_urspruenglich": "falsch"}], p)
    with open(p, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert zeilen[0]["schl_nr"] == "01838"
    assert zeilen[0]["name"] == "Klosterstraße"


def test_pruefung_csv_hat_festgelegte_spalten(tmp_path):
    p = tmp_path / "pruefung.csv"
    schreibe_pruefung([{"buchseite": 300, "lemma_roh": "",
                        "grund": "Anker ohne Lemma",
                        "rohtext": "Anlage ohne Eigenname Schl.-Nr.:"}], p)
    with open(p, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert list(zeilen[0].keys()) == FELDER_PRUEFUNG
    assert zeilen[0]["grund"] == "Anker ohne Lemma"
