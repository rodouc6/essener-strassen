"""Gesamtlauf: prüft, dass die Zusatzaufträge des Controllers greifen —
Anker ohne Lemma, auffällige Lemmata und Köpfe ohne Namensstadium landen alle
sichtbar in pruefung.csv statt stillschweigend zu verschwinden oder zu fehlen.
"""
import csv

from strassen.erschliessen import main

_SEITE = (
    "Anlage ohne Eigenname Schl.-Nr.: 09999, Stadtteil Nirgendwo, "
    "Str.-Kl.: Gemeindestraße. "
    "Kütings Garten: Schl.-Nr.: 01838, Stadtteil Freisenbruch, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "18. November 1904: Kirchstraße, 01. Juni 1926: Klosterstraße, "
    "20. November 1937: Kütings Garten. "
    "Straße Am Alten Wasserwerk Nördlich Vom Deich: Schl.-Nr.: 02000, "
    "Stadtteil Fischlaken, Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "05. Mai 1900: Straße Am Alten Wasserwerk Nördlich Vom Deich. "
    "Sackgasse Ohne Angabe: Schl.-Nr.: 04000, Stadtteil Musterhausen, "
    "Str.-Kl.: Gemeindestraße."
)


def _lauf(tmp_path):
    ocr_dir = tmp_path / "ocr"
    ocr_dir.mkdir()
    (ocr_dir / "s300.txt").write_text(_SEITE, encoding="utf-8")
    ausgabe_dir = tmp_path / "daten"
    kennzahlen = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir)
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen = list(csv.DictReader(f))
    with open(ausgabe_dir / "namen.csv", encoding="utf-8") as f:
        namen = list(csv.DictReader(f))
    with open(ausgabe_dir / "pruefung.csv", encoding="utf-8") as f:
        pruefung = list(csv.DictReader(f))
    return kennzahlen, strassen, namen, pruefung


def test_anker_ohne_lemma_landet_sichtbar_in_pruefung(tmp_path):
    """Zusatzauftrag 1: ein Anker ohne auffindbares Lemma darf nicht
    stillschweigend verschwinden, sondern muss in pruefung.csv auftauchen."""
    _, _, _, pruefung = _lauf(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Anker ohne Lemma"]
    assert len(treffer) == 1
    assert treffer[0]["buchseite"] == "300"


def test_auffaelliges_lemma_wird_gekennzeichnet_aber_trotzdem_aufgenommen(tmp_path):
    """Zusatzauftrag 2: ein Lemma mit >4 Wörtern oder >40 Zeichen wird
    markiert (grund + status='unsicher'), aber nicht ausgeschlossen."""
    _, strassen, _, pruefung = _lauf(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Lemma auffällig (Länge)"]
    assert len(treffer) == 1
    assert treffer[0]["lemma_roh"] == "Straße Am Alten Wasserwerk Nördlich Vom Deich"

    zeile = [z for z in strassen
             if z["lemma"] == "Straße Am Alten Wasserwerk Nördlich Vom Deich"][0]
    assert zeile["status"] == "unsicher"


def test_normaler_eintrag_bleibt_automatisch(tmp_path):
    _, strassen, namen, _ = _lauf(tmp_path)
    zeile = [z for z in strassen if z["lemma"] == "Kütings Garten"][0]
    assert zeile["status"] == "automatisch"
    stadien = [z for z in namen if z["schl_nr"] == "01838"]
    assert len(stadien) == 3
    assert [s["name"] for s in stadien] == ["Kirchstraße", "Klosterstraße", "Kütings Garten"]


def test_kopf_ohne_namensstadium_und_ohne_verweis_landet_in_pruefung(tmp_path):
    """Zusatzauftrag 3: Kopf lesbar, aber rest leer und kein 'Siehe' → Ground
    'kein Namensstadium erkannt'; der Eintrag bleibt trotzdem in strassen.csv."""
    _, strassen, _, pruefung = _lauf(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "kein Namensstadium erkannt"]
    assert len(treffer) == 1
    assert treffer[0]["lemma_roh"] == "Sackgasse Ohne Angabe"
    assert any(z["lemma"] == "Sackgasse Ohne Angabe" for z in strassen)


def test_kennzahlen_gesamtlauf(tmp_path):
    kennzahlen, strassen, namen, pruefung = _lauf(tmp_path)
    assert kennzahlen["eintraege"] == 3
    assert kennzahlen["strassen"] == 3
    assert kennzahlen["namensstadien"] == 4
    assert kennzahlen["pruefung"] == 3
    assert len(strassen) == 3
    assert len(namen) == 4
    assert len(pruefung) == 3
