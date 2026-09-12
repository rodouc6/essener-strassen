"""Smoke-Test für strassen.veroeffentlichen: Stufe 3+4 auf einer Mini-Fixture,
inklusive des STATUS_BELASTBAR-Filters (`status` in `automatisch`/`geprueft`) für
die Konkordanz-Ableitung (IMPORTANT 2) und der Reproduzierbarkeit (zweimaliger Lauf
liefert byte-identische Artefakte).
"""
import csv

from strassen.veroeffentlichen import main


def _schreibe_fixture(tmp_path):
    daten = tmp_path / "daten"
    docs = tmp_path / "docs"
    daten.mkdir()
    docs.mkdir()

    strassen = [
        {"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausen",
         "strassenklasse": "Gemeindestraße", "namensgruppe": "Person", "verweis_auf": "",
         "buchseite": "10", "status": "automatisch"},
        {"schl_nr": "00002", "lemma": "Unsichere Straße", "stadtteile": "Mitte",
         "strassenklasse": "Gemeindestraße", "namensgruppe": "Flurname", "verweis_auf": "",
         "buchseite": "11", "status": "unsicher"},
        {"schl_nr": "00003", "lemma": "Geprüfte Straße", "stadtteile": "Rüttenscheid",
         "strassenklasse": "Gemeindestraße", "namensgruppe": "Person", "verweis_auf": "",
         "buchseite": "12", "status": "geprueft"},
    ]
    namen = [
        {"schl_nr": "00001", "stadium": "1", "gueltig_ab": "1900-01-01",
         "datum_praezision": "tag", "name": "Kaiserstraße", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00001", "stadium": "2", "gueltig_ab": "1937-11-01",
         "datum_praezision": "tag", "name": "Aachener Straße", "ist_urspruenglich": "falsch"},
        # Nur unter status=automatisch relevant; ohne den Filter würde diese
        # Straße (status=unsicher) ebenfalls einen Konkordanzeintrag erzeugen.
        {"schl_nr": "00002", "stadium": "1", "gueltig_ab": "1920-01-01",
         "datum_praezision": "tag", "name": "Alte Gasse", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00002", "stadium": "2", "gueltig_ab": "1937-05-01",
         "datum_praezision": "tag", "name": "Unsichere Straße", "ist_urspruenglich": "falsch"},
        # status=geprueft ist genauso belastbar wie status=automatisch und muss
        # ebenfalls in die Konkordanz einfließen.
        {"schl_nr": "00003", "stadium": "1", "gueltig_ab": "1905-01-01",
         "datum_praezision": "tag", "name": "Alte Bahnhofstraße", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00003", "stadium": "2", "gueltig_ab": "1937-08-01",
         "datum_praezision": "tag", "name": "Geprüfte Straße", "ist_urspruenglich": "falsch"},
    ]
    with open(daten / "strassen.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["schl_nr", "lemma", "stadtteile",
                            "strassenklasse", "namensgruppe", "verweis_auf",
                            "buchseite", "status"])
        w.writeheader()
        w.writerows(strassen)
    with open(daten / "namen.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["schl_nr", "stadium", "gueltig_ab",
                            "datum_praezision", "name", "ist_urspruenglich"])
        w.writeheader()
        w.writerows(namen)

    amtlich = tmp_path / "amtlich.csv"
    amtlich.write_text("strasse\nAachener Straße\n", encoding="utf-8")

    adressbuch = tmp_path / "essen1936.csv"
    adressbuch.write_text(
        "Adresse\tsonstiges\nKaiserstraße 5\tx\nKaiserstraße 7\tx\nAlte Gasse 1\tx\n",
        encoding="utf-8")

    return daten, docs, amtlich, adressbuch


def test_konkordanz_nutzt_automatisch_und_geprueft(tmp_path):
    """IMPORTANT 2: der STATUS_BELASTBAR-Filter (automatisch UND geprueft) steht
    im Code, nicht nur in einer Kommandozeile. Straße 00002 (status=unsicher)
    hätte am Stichtag ebenfalls einen Namenswandel (Alte Gasse -> Unsichere
    Straße), darf aber NICHT in der Konkordanz landen. Straße 00003
    (status=geprueft) ist genauso belastbar wie status=automatisch und MUSS
    in der Konkordanz erscheinen."""
    daten, docs, amtlich, adressbuch = _schreibe_fixture(tmp_path)
    kennzahlen = main(daten_dir=str(daten), docs_dir=str(docs), adressbuch=str(adressbuch),
                       amtliches_verzeichnis=str(amtlich), stichtag="1936-06-30")
    with open(daten / "konkordanz_1936.csv", encoding="utf-8") as f:
        konkordanz = list(csv.DictReader(f))
    assert len(konkordanz) == 2
    assert {k["schl_nr"] for k in konkordanz} == {"00001", "00003"}
    ehemalig_je_schl_nr = {k["schl_nr"]: k["ehemalig"] for k in konkordanz}
    assert ehemalig_je_schl_nr["00001"] == "Kaiserstraße"
    assert ehemalig_je_schl_nr["00003"] == "Alte Bahnhofstraße"
    assert all(k["schl_nr"] != "00002" for k in konkordanz)
    assert kennzahlen["strassen_belastbar"] == 2
    assert kennzahlen["strassen_geprueft"] == 1


def test_erzeugt_alle_vier_artefakte(tmp_path):
    daten, docs, amtlich, adressbuch = _schreibe_fixture(tmp_path)
    kennzahlen = main(daten_dir=str(daten), docs_dir=str(docs), adressbuch=str(adressbuch),
                       amtliches_verzeichnis=str(amtlich), stichtag="1936-06-30")
    assert (docs / "qualitaet.md").exists()
    assert (daten / "konkordanz_1936.csv").exists()
    assert (daten / "pruefung_konkordanz.csv").exists()
    assert (docs / "erhebungsstand.md").exists()
    assert kennzahlen["konkordanz"] == 2
    assert kennzahlen["strassen_belastbar"] == 2


def test_pruefung_validierung_enthaelt_nur_lemma_schl_nr_grund_keine_zitate(tmp_path):
    """IMPORTANT 5: 'Unsichere Straße' (schl_nr 00002) und 'Geprüfte Straße'
    (schl_nr 00003) sind nicht im amtlichen Verzeichnis bestätigt (nur
    'Aachener Straße' ist dort gelistet) und müssen mit
    grund='nicht im amtlichen Verzeichnis' auftauchen — ausschließlich Lemma,
    Schlüsselnummer und Grund, kein Rohtext/Zitat."""
    daten, docs, amtlich, adressbuch = _schreibe_fixture(tmp_path)
    main(daten_dir=str(daten), docs_dir=str(docs), adressbuch=str(adressbuch),
         amtliches_verzeichnis=str(amtlich), stichtag="1936-06-30")
    with open(daten / "pruefung_validierung.csv", encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert set(zeilen[0].keys()) == {"lemma", "schl_nr", "grund"}
    treffer = [z for z in zeilen if z["grund"] == "nicht im amtlichen Verzeichnis"]
    assert len(treffer) == 2
    assert {t["lemma"] for t in treffer} == {"Unsichere Straße", "Geprüfte Straße"}
    assert {t["schl_nr"] for t in treffer} == {"00002", "00003"}


def test_lauf_ist_byte_identisch_reproduzierbar(tmp_path):
    daten, docs, amtlich, adressbuch = _schreibe_fixture(tmp_path)
    main(daten_dir=str(daten), docs_dir=str(docs), adressbuch=str(adressbuch),
         amtliches_verzeichnis=str(amtlich), stichtag="1936-06-30")
    stand1 = {p.name: p.read_bytes() for p in list(daten.glob("*.csv")) + list(docs.glob("*.md"))}

    main(daten_dir=str(daten), docs_dir=str(docs), adressbuch=str(adressbuch),
         amtliches_verzeichnis=str(amtlich), stichtag="1936-06-30")
    stand2 = {p.name: p.read_bytes() for p in list(daten.glob("*.csv")) + list(docs.glob("*.md"))}

    assert stand1 == stand2


def test_lade_adressbuch_strassennamen_trennt_hausnummer_ab(tmp_path):
    from strassen.veroeffentlichen import lade_adressbuch_strassennamen

    pfad = tmp_path / "essen1936.csv"
    pfad.write_text("Adresse\tx\nKaiserstraße 5\tx\nGrenzstr. 25\tx\n", encoding="utf-8")
    namen = lade_adressbuch_strassennamen(pfad)
    assert "Kaiserstraße" in namen
    assert "Grenzstr." in namen
