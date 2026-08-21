"""Gesamtlauf: prüft, dass die Zusatzaufträge des Controllers greifen —
Anker ohne Lemma, auffällige Lemmata und Köpfe ohne Namensstadium landen alle
sichtbar in pruefung.csv statt stillschweigend zu verschwinden oder zu fehlen.
"""
import csv

from strassen.erschliessen import (
    main, _lemma_form_auffaellig, _name_auffaellig, _feld_zu_lang,
    _namensgruppe_auffaellig,
)

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


# --- Fix-Runde 1 (Review Task 5): CRITICAL 1-3 + IMPORTANT ---------------

_SEITE2 = (
    "Doppelte Straße Eins: Schl.-Nr.: 05500, Stadtteil Rüttenscheid, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "01. Januar 1950: Doppelte Straße Eins. "
    "Doppelte Straße Zwei: Schl.-Nr.: 05500, Stadtteil Bergerhausen, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "02. Februar 1950: Doppelte Straße Zwei. "
    "3 Häuser am Sportplatz: Schl.-Nr.: 05600, Stadtteil Byfang, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "03. März 1950: Sportplatzweg. "
    "Rauschweg: Schl.-Nr.: 05700, Stadtteil Kray, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
    "04. April 1950: §§§ %%% ***. "
    "Langfeldweg: Schl.-Nr.: 05800, Stadtteil Steele, "
    "Str.-Kl.: AAAAAAAAAA BBBBBBBBBB CCCCCCCCCC DDDDDDDDDD EEEEEEEEEE "
    "FFFFFFFFFF, Str.-Gr.: Lagebezeichnung, 05. Mai 1950: Langfeldweg."
)


def _lauf2(tmp_path):
    ocr_dir = tmp_path / "ocr2"
    ocr_dir.mkdir()
    (ocr_dir / "s400.txt").write_text(_SEITE2, encoding="utf-8")
    ausgabe_dir = tmp_path / "daten2"
    kennzahlen = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir)
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen = list(csv.DictReader(f))
    with open(ausgabe_dir / "namen.csv", encoding="utf-8") as f:
        namen = list(csv.DictReader(f))
    with open(ausgabe_dir / "pruefung.csv", encoding="utf-8") as f:
        pruefung = list(csv.DictReader(f))
    return kennzahlen, strassen, namen, pruefung


def test_doppelte_schluesselnummer_wird_markiert(tmp_path):
    """CRITICAL 3: alle Einträge, deren schl_nr mehrfach vorkommt, landen in
    pruefung.csv (grund='Schlüsselnummer mehrfach') und werden status='unsicher'
    — auch wenn beide Rohtexte für sich genommen sauber sind (nicht raten,
    welcher der beiden echt ist)."""
    _, strassen, _, pruefung = _lauf2(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Schlüsselnummer mehrfach"]
    assert len(treffer) == 2
    dubletten = [z for z in strassen if z["schl_nr"] == "05500"]
    assert len(dubletten) == 2
    assert all(z["status"] == "unsicher" for z in dubletten)


def test_ziffernblock_dubletten_werden_durch_nummernfix_vermieden():
    """Regressionsschutz auf Modulebene: die Kollisionsursache aus CRITICAL 3
    (Ziffernblock mit Leerzeichen) ist in kopf.py behoben — s. test_kopf.py."""
    from strassen.kopf import parse_kopf
    assert parse_kopf("01 544, Stadtteil X.").schl_nr == "01544"


def test_lemma_form_auffaellig_direkt():
    """CRITICAL 2b: Plausibilitätsfilter direkt geprüft — Lemma ohne
    Großbuchstaben-/Umlaut-Beginn oder mit Nicht-Namenszeichen ist auffällig,
    ein sauberes Lemma (auch mit Abkürzungspunkt) nicht."""
    assert _lemma_form_auffaellig("3 Häuser am Sportplatz") is True
    assert _lemma_form_auffaellig(") Am Richtenberg") is True
    assert _lemma_form_auffaellig("St.-Ingbert-Höhe") is False
    assert _lemma_form_auffaellig("Kütings Garten") is False


def test_auffaelliges_lemma_form_landet_in_pruefung_und_bleibt_erhalten(tmp_path):
    """CRITICAL 2b im Gesamtlauf: '3 Häuser am Sportplatz' beginnt mit einer
    Ziffer statt Großbuchstabe/Umlaut und wird markiert, aber trotzdem
    veröffentlicht (Kennzeichnung, kein Ausschluss)."""
    _, strassen, _, pruefung = _lauf2(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Lemma auffällig (Form)"]
    assert len(treffer) == 1
    assert treffer[0]["lemma_roh"] == "3 Häuser am Sportplatz"
    zeile = [z for z in strassen if z["lemma"] == "3 Häuser am Sportplatz"][0]
    assert zeile["status"] == "unsicher"


def test_name_auffaellig_direkt():
    """CRITICAL 1: Plausibilitätsfilter für Namensstadien direkt geprüft."""
    assert _name_auffaellig("§§§ %%% ***") is True
    assert _name_auffaellig("ab") is True          # < 3 Zeichen
    assert _name_auffaellig("x" * 61) is True       # > 60 Zeichen
    assert _name_auffaellig("Nummer 12345 Straße") is True  # Ziffernfolge >4
    assert _name_auffaellig("Kirchstraße") is False
    assert _name_auffaellig("Altenessener Straße (Verl.)") is False


def test_namensstadium_rauschen_markiert_ganzen_eintrag(tmp_path):
    """CRITICAL 1: Bildrauschen als Stadiumsname (Schl.-Nr. 05700, Analogon
    zum realen Fall 01760) markiert den GANZEN Eintrag als unsicher, das
    Stadium bleibt aber unverändert in namen.csv (Kennzeichnung, kein
    Ausschluss)."""
    _, strassen, namen, pruefung = _lauf2(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Namensstadium auffällig"]
    assert len(treffer) == 1
    assert treffer[0]["lemma_roh"] == "Rauschweg"
    zeile = [z for z in strassen if z["lemma"] == "Rauschweg"][0]
    assert zeile["status"] == "unsicher"
    stadium = [z for z in namen if z["schl_nr"] == "05700"][0]
    assert stadium["name"] == "§§§ %%% ***"


def test_feld_zu_lang_direkt():
    assert _feld_zu_lang("x" * 61) is True
    assert _feld_zu_lang("Gemeindestraße") is False


def test_feld_auffaellig_laenge_landet_in_pruefung(tmp_path):
    """IMPORTANT: ein ungewöhnlich langes strassenklasse-Feld (>60 Zeichen,
    typisches Symptom eines nicht erkannten Markers) wird markiert. Die
    Schwelle für strassenklasse bleibt unverändert bei 60 (Fix-Runde 1,
    Teil 2: nur die namensgruppe-Heuristik wurde nachjustiert, s. u.)."""
    _, strassen, _, pruefung = _lauf2(tmp_path)
    treffer = [z for z in pruefung if z["grund"] == "Feld auffällig (Länge)"]
    assert len(treffer) == 1
    assert treffer[0]["lemma_roh"] == "Langfeldweg"
    zeile = [z for z in strassen if z["lemma"] == "Langfeldweg"][0]
    assert zeile["status"] == "unsicher"


def test_marker_variante_ohne_r_im_gesamtlauf():
    """IMPORTANT: 'St.-Gr.:' (fehlendes 'r') liefert eine gefüllte
    namensgruppe statt einer leeren — Regressionsschutz auf Modulebene,
    s. test_kopf.py für den eigentlichen Fix."""
    from strassen.kopf import parse_kopf
    k = parse_kopf("01261, Stadtteil Stadtkern, St.-Gr.: Person, "
                    "01. Januar 1900: Helenenstraße.")
    assert k.namensgruppe == "Person"


# --- Fix-Runde 1, Teil 2 (Ruling 3): namensgruppe-Heuristik nachjustiert ---

def test_namensgruppe_auffaellig_direkt():
    """Ruling 3: strassenklasse-Schwelle (60) bleibt unverändert
    (test_feld_zu_lang_direkt); namensgruppe wird eigenständig geprüft —
    >150 Zeichen ODER Rauschzeichen ODER Ziffern-Cluster ≥3. Lange, aber
    saubere mehrteilige Klassifikationen (echte Buchtaxonomie, z. B.
    Leibnizstraße, 122 Zeichen) bleiben unauffällig."""
    lang_aber_sauber = ("Person, Mann, Deutscher, Philosoph, Wissenschaftler, "
                        "Mathematiker, Diplomat, Physiker, Historiker, "
                        "Politiker, Bibliothekar")
    assert len(lang_aber_sauber) < 150
    assert _namensgruppe_auffaellig(lang_aber_sauber) is False
    assert _namensgruppe_auffaellig("Essener Geschichte und Örtlichkeit") is False
    assert _namensgruppe_auffaellig("x" * 151) is True
    # Rauschzeichen (Unterstrich, wie im realen Fall 'Franz-Fischer-Weg_'):
    assert _namensgruppe_auffaellig("Industrie und Wirtschaft, Franz-Fischer-Weg_") is True
    # Ziffern-Cluster ab 3 Stellen (Jahreszahl in namensgruppe ist ein
    # Fehlerindiz, vgl. den echten Altendorfer-Bleed-Fall):
    assert _namensgruppe_auffaellig("etwa 1921: Nelkenstraße") is True
    assert _namensgruppe_auffaellig("Haus Nr. 12") is False


_SEITE3 = (
    "Langname Sauber: Schl.-Nr.: 05900, Stadtteil Rüttenscheid, "
    "Str.-Kl.: Gemeindestraße, "
    "Str.-Gr.: Person, Mann, Deutscher, Philosoph, Wissenschaftler, "
    "Mathematiker, Diplomat, Physiker, Historiker, Politiker, Bibliothekar, "
    "01. Januar 1950: Langname Sauber. "
    "Rauschgruppe: Schl.-Nr.: 06000, Stadtteil Byfang, "
    "Str.-Kl.: Gemeindestraße, "
    "Str.-Gr.: Industrie und Wirtschaft, Franz-Fischer-Weg_, "
    "02. Februar 1950: Rauschgruppe."
)


def _lauf3(tmp_path):
    ocr_dir = tmp_path / "ocr3"
    ocr_dir.mkdir()
    (ocr_dir / "s500.txt").write_text(_SEITE3, encoding="utf-8")
    ausgabe_dir = tmp_path / "daten3"
    kennzahlen = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir)
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen = list(csv.DictReader(f))
    with open(ausgabe_dir / "pruefung.csv", encoding="utf-8") as f:
        pruefung = list(csv.DictReader(f))
    return kennzahlen, strassen, pruefung


def test_lange_aber_saubere_namensgruppe_wird_nicht_mehr_geflaggt(tmp_path):
    """Ruling 3, Kernziel: eine lange, aber inhaltlich saubere
    Kategorien-Liste (>60, aber <150 Zeichen, keine Rauschzeichen) löst
    'Feld auffällig (Länge)' nicht mehr aus — vorher (Teil 1 dieser
    Fix-Runde) wäre sie fälschlich markiert worden."""
    _, strassen, pruefung = _lauf3(tmp_path)
    treffer = [z for z in pruefung
               if z["grund"] == "Feld auffällig (Länge)" and z["lemma_roh"] == "Langname Sauber"]
    assert treffer == []
    zeile = [z for z in strassen if z["lemma"] == "Langname Sauber"][0]
    assert zeile["status"] == "automatisch"


def test_namensgruppe_mit_rauschzeichen_wird_weiterhin_geflaggt(tmp_path):
    _, strassen, pruefung = _lauf3(tmp_path)
    treffer = [z for z in pruefung
               if z["grund"] == "Feld auffällig (Länge)" and z["lemma_roh"] == "Rauschgruppe"]
    assert len(treffer) == 1
    zeile = [z for z in strassen if z["lemma"] == "Rauschgruppe"][0]
    assert zeile["status"] == "unsicher"
