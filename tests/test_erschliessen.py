"""Gesamtlauf: prüft, dass die Zusatzaufträge des Controllers greifen —
Anker ohne Lemma, auffällige Lemmata und Köpfe ohne Namensstadium landen alle
sichtbar in pruefung.csv statt stillschweigend zu verschwinden oder zu fehlen.
"""
import csv
import subprocess
import sys

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
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname."
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
    # Fix-Runde 4: einzelnes Ziffern-Token (Spaltenrauschen aus dem Scan)
    assert _name_auffaellig("Obere Aue. ze 5 Oberer Schloßhang- Schloss Borbeck ll") is True
    assert _name_auffaellig("Am Berge 7 Hof") is True
    # echte Namen mit Ziffer behalten ihren Punkt und bleiben unauffällig
    assert _name_auffaellig("Brandstraße (tlw. 2. Hälfte)") is False
    assert _name_auffaellig("1. Schockenhecke") is False
    # Fix-Runde 4: echtes Satzende MITTEN im Namen
    assert _name_auffaellig("Obere Aue. Oberer Schloßhang") is True
    assert _name_auffaellig("St. Annental") is False
    assert _name_auffaellig("II. Weberstraße") is False
    assert _name_auffaellig("Ill. Ziegelstraße") is False
    assert _name_auffaellig("Graßmannstraße (Verl.)") is False
    assert _name_auffaellig("Altendorfer Straße") is False


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


# --- MINOR 2 (Whole-Branch-Review): 'Siehe' tief in der Erläuterung darf das
# 'kein Namensstadium erkannt'-Netz nicht unterdrücken --------------------

_SEITE4 = (
    "Testverweisstraße: Schl.-Nr.: 07001, Stadtteil Musterhausen, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, "
    "14. November A 0, EEE 1935: Testverweisstraße. Dies ist eine lange "
    "Erläuterung ohne inhaltlichen Bezug zum folgenden Verweis. "
    "Siehe Anderestraße. "
    "Kurzverweis: Schl.-Nr.: 07002, Stadtteil Musterhausen, "
    "Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, "
    "01. Januar 1900: Kurzverweis. Siehe Zielstraße."
)


def _lauf4(tmp_path):
    ocr_dir = tmp_path / "ocr4"
    ocr_dir.mkdir()
    (ocr_dir / "s600.txt").write_text(_SEITE4, encoding="utf-8")
    ausgabe_dir = tmp_path / "daten4"
    kennzahlen = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir)
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen = list(csv.DictReader(f))
    with open(ausgabe_dir / "pruefung.csv", encoding="utf-8") as f:
        pruefung = list(csv.DictReader(f))
    return kennzahlen, strassen, pruefung


def test_siehe_tief_in_erlaeuterung_unterdrueckt_pruefungsnetz_nicht(tmp_path):
    """OCR-verstümmeltes Datum (kein Stadium erkennbar) UND ein 'Siehe X' weit
    hinten in einer inhaltlich unabhängigen Erläuterung (Analogon zu den realen
    stillen Verlusten 00685, 00864, 02845): der Eintrag muss trotz des fernen
    'Siehe' als 'kein Namensstadium erkannt' markiert werden, statt
    stillschweigend als 'automatisch' durchzulaufen. verweis_auf bleibt dabei
    trotzdem gefüllt (der Verweis selbst ist ja real vorhanden, nur eben kein
    Ersatz für das fehlende Stadium)."""
    _, strassen, pruefung = _lauf4(tmp_path)
    treffer = [z for z in pruefung
               if z["grund"] == "kein Namensstadium erkannt"
               and z["lemma_roh"] == "Testverweisstraße"]
    assert len(treffer) == 1
    zeile = [z for z in strassen if z["lemma"] == "Testverweisstraße"][0]
    assert zeile["status"] == "unsicher"
    assert zeile["verweis_auf"] == "Anderestraße"


def test_siehe_direkt_im_kopfbereich_zaehlt_weiterhin_als_verweis_eintrag(tmp_path):
    """Ein echter, kurzer Verweis-Eintrag ohne eigene Namenskette (Datum
    OCR-verstümmelt, 'Siehe X' folgt aber direkt im Kopfbereich, Analogon zu
    den realen Fällen 01078, 02224) bleibt weiterhin unauffällig — das Netz
    greift nur bei einem FERNEN 'Siehe', nicht bei jedem."""
    _, strassen, pruefung = _lauf4(tmp_path)
    treffer = [z for z in pruefung
               if z["grund"] == "kein Namensstadium erkannt"
               and z["lemma_roh"] == "Kurzverweis"]
    assert treffer == []
    zeile = [z for z in strassen if z["lemma"] == "Kurzverweis"][0]
    assert zeile["status"] == "automatisch"
    assert zeile["verweis_auf"] == "Zielstraße"


# --- MINOR 7: sinnvoller Exitcode ------------------------------------------

def test_cli_exit_code_1_bei_leerem_ocr_verzeichnis(tmp_path):
    """`python3 -m strassen.erschliessen` muss Exitcode 1 liefern, wenn kein
    einziger Straßeneintrag erzeugt wurde (leeres/falsches ocr_dir) — vorher
    war der Exitcode unabhängig vom Ergebnis immer 0."""
    ocr_dir = tmp_path / "ocr_leer"
    ocr_dir.mkdir()
    ausgabe_dir = tmp_path / "daten"
    code = (
        "import sys; from strassen.erschliessen import main; "
        f"kz = main(ocr_dir={str(ocr_dir)!r}, ausgabe_dir={str(ausgabe_dir)!r}); "
        "sys.exit(0 if kz['strassen'] else 1)"
    )
    ergebnis = subprocess.run([sys.executable, "-c", code], capture_output=True)
    assert ergebnis.returncode == 1


def test_cli_exit_code_0_bei_erfolgreichem_lauf(tmp_path):
    ocr_dir = tmp_path / "ocr"
    ocr_dir.mkdir()
    (ocr_dir / "s300.txt").write_text(_SEITE, encoding="utf-8")
    ausgabe_dir = tmp_path / "daten"
    code = (
        "import sys; from strassen.erschliessen import main; "
        f"kz = main(ocr_dir={str(ocr_dir)!r}, ausgabe_dir={str(ausgabe_dir)!r}); "
        "sys.exit(0 if kz['strassen'] else 1)"
    )
    ergebnis = subprocess.run([sys.executable, "-c", code], capture_output=True)
    assert ergebnis.returncode == 0


# --- Task 8: Hinweise aus Kopf/Stadien als Prüfgründe, leere Kopffelder ---

import csv as _csv


def _lauf5(tmp_path, seitentext, nummer=100):
    ocr = tmp_path / "ocr"
    ocr.mkdir()
    (ocr / f"s{nummer:03d}.txt").write_text(seitentext, encoding="utf-8")
    aus = tmp_path / "daten"
    main(ocr_dir=str(ocr), ausgabe_dir=str(aus))
    strassen = list(_csv.DictReader(open(aus / "strassen.csv", encoding="utf-8")))
    pruefung = list(_csv.DictReader(open(aus / "pruefung.csv", encoding="utf-8")))
    return strassen, pruefung


def test_datums_hinweis_wird_pruefgrund_und_unsicher(tmp_path):
    """Eskenshof, Schl.-Nr. 00817, S. 110: '13, Juni 1973: Eskenshof'."""
    strassen, pruefung = _lauf5(tmp_path,
        "Eskenshof: Schl.-Nr.: 00817, Stadtteil Überruhr-Holthausen, Str.-Kl.: Gemeindestraße, "
        "Str.-Gr.: Hofname, 13, Juni 1973: Eskenshof. Nach dem Behandigungsgut Esken.\n")
    assert strassen[0]["status"] == "unsicher"
    assert [z["grund"] for z in pruefung] == ["Datum: Komma nach Tag"]


def test_kopf_hinweis_wird_pruefgrund(tmp_path):
    strassen, pruefung = _lauf5(tmp_path,
        "Eibergweg: Schl.-Nr.: 00733, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: "
        "Stadt und Ort, 20. November 1937: Eibergweg. Erläuterung.\n")
    assert strassen[0]["strassenklasse"] == "Gemeindestraße"
    assert strassen[0]["status"] == "unsicher"
    assert "Straßenklasse ohne Marker" in [z["grund"] for z in pruefung]


def test_mehrere_hinweise_eines_stadiums_werden_einzelne_gruende(tmp_path):
    strassen, pruefung = _lauf5(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
        "13, Novemner 1900: Testweg. Erläuterung.\n")
    gruende = sorted(z["grund"] for z in pruefung)
    assert gruende == ["Datum: Komma nach Tag", "Monatsname OCR-korrigiert"]


def test_leerer_stadtteil_wird_pruefgrund(tmp_path):
    """Manderscheidtstraße 02191 (Goldstandard) war trotz leerem Stadtteil 'automatisch'."""
    strassen, pruefung = _lauf5(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
        "01. Januar 1900: Testweg. Erläuterung.\n")
    assert strassen[0]["status"] == "unsicher"
    assert "Stadtteil fehlt" in [z["grund"] for z in pruefung]


def test_leere_strassenklasse_wird_pruefgrund(tmp_path):
    strassen, pruefung = _lauf5(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Stadtteil X, Str.-Gr.: Hofname, "
        "01. Januar 1900: Testweg. Erläuterung.\n")
    assert "Straßenklasse fehlt" in [z["grund"] for z in pruefung]


def test_reiner_verweis_eintrag_ohne_klasse_bleibt_automatisch(tmp_path):
    """Grendgasse 01078 (S. 142): '…, Str.-Gr.: X. Siehe Grendplatz.' — kein Stadium,
    Verweis im Kopf; fehlende Felder sind hier kein Parserfehler."""
    strassen, pruefung = _lauf5(tmp_path,
        "Grendgasse: Schl.-Nr.: 01078, Stadtteil Stadtkern, Str.-Gr.: Essener Geschichte. "
        "Siehe Grendplatz.\n")
    assert strassen[0]["verweis_auf"] == "Grendplatz"
    assert "Straßenklasse fehlt" not in [z["grund"] for z in pruefung]
    assert strassen[0]["status"] == "automatisch"


def test_unverarbeiteter_rest_wird_pruefgrund(tmp_path):
    """Am Thyssenhaus, Schl.-Nr. 00217, S. 44: '04. Februar 19377: Am Thyssenhaus.'
    — die verstümmelte Jahreszahl lässt keinen Stempel matchen; ohne eigenen
    Prüfgrund verschwindet das fehlende Stadium unsichtbar (Fix Task 12)."""
    strassen, pruefung = _lauf5(tmp_path,
        "Am Thyssenhaus: Schl.-Nr.: 00217, Stadtteil Frohnhausen, Str.-Kl.: Gemeindestraße, "
        "Str.-Gr.: Hofname, 22. Februar 1961: Am Rheinstahlhaus, "
        "04. Februar 19377: Am Thyssenhaus. Erläuterung folgt.\n")
    assert strassen[0]["status"] == "unsicher"
    gruende = [z["grund"] for z in pruefung]
    assert "Namenskette unvollständig gelesen" in gruende
    treffer = [z for z in pruefung if z["grund"] == "Namenskette unvollständig gelesen"]
    assert "19377" in treffer[0]["rohtext"]


def test_vollstaendig_gelesene_kette_hat_keinen_pruefgrund_dafuer(tmp_path):
    """Kütings Garten, Schl.-Nr. 01838, S. 213 — vollständige Kette ohne Rest."""
    strassen, pruefung = _lauf5(tmp_path,
        "Kütings Garten: Schl.-Nr.: 01838, Stadtteil Freisenbruch, "
        "Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
        "18. November 1904: Kirchstraße, 01. Juni 1926: Klosterstraße, "
        "20. November 1937: Kütings Garten. Erläuterung.\n")
    assert "Namenskette unvollständig gelesen" not in [z["grund"] for z in pruefung]


def test_bloße_abkuerzung_als_name_ist_auffaellig():
    """Abschlussreview: 00334, S. 67 — gedruckt '18. November 1890: III. Rottstraße',
    die OCR setzte ein Komma hinter 'Ill'; der Name schrumpfte auf die bloße
    römische Zahl und blieb bisher 'automatisch'."""
    assert _name_auffaellig("Ill") is True
    assert _name_auffaellig("III.") is True
    assert _name_auffaellig("St") is True
    assert _name_auffaellig("II") is True
    assert _name_auffaellig("IV.") is True
    assert _name_auffaellig("12.") is True
    # vollständige Namen mit solchem Präfix bleiben unauffällig
    assert _name_auffaellig("II. Weberstraße") is False
    assert _name_auffaellig("St. Annental") is False


# --- Task 8: Korrektur-Overlay im Gesamtlauf ---


def test_main_wendet_korrekturen_an_und_zaehlt(tmp_path):
    """Eine Bestätigungszeile (feld=eintrag) im Korrektur-Overlay setzt status=geprueft
    und zählt in kennzahlen['korrigiert']; ohne korrekturen_pfad bleibt der Lauf unverändert."""
    from strassen.korrekturen import FELDER_KORREKTUREN

    _, strassen, _, _ = _lauf(tmp_path)
    schl_nr = strassen[0]["schl_nr"]
    lemma = strassen[0]["lemma"]
    assert strassen[0]["status"] != "geprueft"

    korr_pfad = tmp_path / "korrekturen.csv"
    with open(korr_pfad, "w", encoding="utf-8", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=FELDER_KORREKTUREN)
        w.writeheader()
        w.writerow({"schl_nr": schl_nr, "feld": "eintrag", "wert_alt": "", "wert_neu": "",
                    "beleg": "Scan geprüft", "quelle": "goldstandard", "datum": "2026-09-12"})

    ausgabe_dir = tmp_path / "daten"
    ocr_dir = tmp_path / "ocr"
    kennzahlen = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir, korrekturen_pfad=str(korr_pfad))
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen_korrigiert = list(_csv.DictReader(f))
    treffer = [z for z in strassen_korrigiert if z["schl_nr"] == schl_nr][0]
    assert treffer["status"] == "geprueft"
    assert treffer["lemma"] == lemma
    assert kennzahlen["korrigiert"] == 1

    kennzahlen_ohne = main(ocr_dir=ocr_dir, ausgabe_dir=ausgabe_dir, korrekturen_pfad="")
    with open(ausgabe_dir / "strassen.csv", encoding="utf-8") as f:
        strassen_unveraendert = list(_csv.DictReader(f))
    treffer2 = [z for z in strassen_unveraendert if z["schl_nr"] == schl_nr][0]
    assert treffer2["status"] != "geprueft"
    assert kennzahlen_ohne["korrigiert"] == 0
