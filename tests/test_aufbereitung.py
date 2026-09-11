from strassen.aufbereitung import verbinde_zeilen, bereinige


def test_zerrissener_marker_bleibt_erhalten():
    """Str.-\nKl.: darf nicht zu 'Str.Kl.:' entstellt werden — der Bindestrich
    gehört zum Marker, er ist kein Silbentrennstrich (661 Fälle im Material)."""
    roh = "Am Schroer: Schl.-Nr.: 00127, Stadtteil Byfang, Str.-\nKl.: Gemeindestraße"
    assert "Str.-Kl.:" in verbinde_zeilen(roh)


def test_echte_silbentrennung_wird_aufgeloest():
    roh = "Admiral-Scheer-Straße: Schl.-Nr.: 00012, Stadtteil Süd-\nviertel, Str.-Kl.:"
    assert "Südviertel" in verbinde_zeilen(roh)


def test_bindestrich_im_namen_bleibt():
    """Ein Trennstrich vor Großbuchstabe ist Namensbestandteil, keine Silbentrennung."""
    roh = "Franz-Arens-Straße: Schl.-Nr.: 00947"
    assert "Franz-Arens-Straße" in verbinde_zeilen(roh)


def test_kolumnentitel_und_seitenzahl_entfernt():
    roh = "Essener Straßen\n\nKruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken\n\n211\n"
    sauber = bereinige(roh)
    assert "Essener Straßen" not in sauber
    assert "\n211" not in sauber
    assert "Kruselbeek" in sauber


def test_ocr_fehler_stra_be_wird_zu_strasse():
    """OCR liest ß am Zeilenanfang als B: Stra-\nBe… → Straße…
    Nur dieser eindeutige Fall wird korrigiert (9 Vorkommen im Material)."""
    roh = "Kronenstra-\nBeek: Schl.-Nr.: 12345"
    assert "Kronenstraße" in verbinde_zeilen(roh)


def test_komposita_essen_bredeney_bleiben_erhalten():
    """Andere -\nB-Fälle sind legitime Komposita und bleiben unangetastet."""
    roh = "Fundstelle bei Essen-\nBredeney liegt hier"
    result = verbinde_zeilen(roh)
    assert "Essen- Bredeney" in result
    assert "Essenßredeney" not in result


def test_einzelbuchstaben_abschnittskopf_wird_entfernt():
    """Der alleinstehende Buchstabe-Kopf eines Alphabet-Abschnitts (z. B. 'A' vor
    dem ersten A-Eintrag) wird sonst fälschlich ins Folgelemma gezogen
    (Task-6-Fix-Runde-1-Finding, real 41 Fälle über 20 Buchstaben)."""
    roh = ("Lit.: Prof. Wilhelm Albermann. In: Werdener Beiträge, Heft 16.\n\n"
           "A\n\n"
           "Aachener Straße: Schl.-Nr.: 00001, Stadtteil Frohnhausen")
    result = verbinde_zeilen(bereinige(roh))
    assert "A Aachener Straße" not in result
    assert "Aachener Straße" in result


def test_doppelkopf_mit_komma_wird_entfernt():
    """Doppelköpfe wie 'Q,R' (S. 267, wenn ein Buchstabe keinen eigenen Abschnitt
    trägt) werden ebenso entfernt."""
    roh = ("Quartier an der Altendorfer Straße.\n\n"
           "Q,R\n\n"
           "Quellenbliek: Schl.-Nr.: 02500, Stadtteil Bredeney")
    result = verbinde_zeilen(bereinige(roh))
    assert "Q,R Quellenbliek" not in result
    assert "R Quellenbliek" not in result
    assert "Quellenbliek" in result


def test_normaler_eintragstext_bleibt_erhalten():
    """Gegentest: normaler, mehrwortiger Eintragstext bleibt unangetastet."""
    roh = "Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken, Str.-Kl.: Gemeindestraße"
    result = verbinde_zeilen(bereinige(roh))
    assert result == roh


def test_zwei_grossbuchstaben_ohne_komma_bleiben_unangetastet():
    """Gegentest/Materialcheck: alleinstehende Zwei-Buchstaben-Zeilen OHNE Komma
    (z. B. 'ME', 'KL') sind im Material Bildrauschen, keine Abschnittsköpfe —
    die Regel bleibt bewusst auf Einzelbuchstaben (+ komma-getrennt) beschränkt,
    damit kein potenziell legitimer Zwei-Buchstaben-Fall verschluckt wird."""
    roh = "Vollendung des 80. Lebensjahres.\n\nME\n\nBertramstraße: Schl.-Nr.: 00347"
    result = verbinde_zeilen(bereinige(roh))
    assert "ME Bertramstraße" in result


def test_abschnittskopf_als_kleinbuchstabe_wird_entfernt():
    """S. 87: OCR las den Abschnittskopf 'C' als 'c' — Lemma wurde 'c Cäcilienstraße'
    (Goldstandard 00540). 29 Einzel-Kleinbuchstaben-Zeilen im Material, 28 davon Rauschen."""
    roh = "Gefangenschaft).\n\nc\n\nCäcilienstraße: Sch!.-Nr.: 00540, Stadtteil Rüttenscheid,"
    sauber = bereinige(roh)
    assert "\nc\n" not in sauber
    assert "Cäcilienstraße" in sauber


def test_randrauschen_letzte_zeile_wird_entfernt():
    """S. 254 endet mit 'mm nm mm nn nn' (Scanrand), mitten im Kopf von Overhammshof 02356."""
    roh = "Overhammshof: Schl.-Nr.: 02356, Stadtteil Fischlaken,\nStr.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, 21. Januar\n\nmm nm mm nn nn\n"
    sauber = bereinige(roh)
    assert "mm nm" not in sauber
    assert "21. Januar" in sauber


def test_randrauschen_erste_zeile_wird_entfernt():
    roh = "Vs u\n\nAachener Straße: Schl.-Nr.: 00001, Stadtteil Frohnhausen"
    assert "Vs u" not in bereinige(roh)


def test_randrauschen_greift_nicht_mitten_im_text():
    roh = "Aachener Straße: Schl.-Nr.: 00001,\nan der A\nStadtteil Frohnhausen, Str.-Kl.: Gemeindestraße."
    assert "an der A" in bereinige(roh)


def test_legitime_kurze_randzeile_bleibt():
    """Zeilen mit Ziffer oder Satzzeichen ('S. 33.', 'Hude.', '18.') sind kein Rauschen."""
    for zeile in ["1886, 5. 33.", "Hude.", "18."]:
        roh = f"Text davor.\n{zeile}\n"
        assert zeile in bereinige(roh), zeile


def test_stadtteil_marker_varianten_werden_normalisiert():
    """Am Stoppenberger Bach 01615 'Stadt-teil', Auf der Bucht 00211 'Stadttei!',
    Diestweg 02505 'Stadteil', Schönscheidts Hof 02812 'Stadttteil', In der Nähe der
    Armin… 02874 'Stadtteit', AmWasserturm 00268 'StadtteilBurgaltendorf',
    Manderscheidtstraße 02191 'Stadt-teile' (Goldstandard)."""
    faelle = {
        "01615, Stadt-teil Stoppenberg, Str.-Kl.:": "Stadtteil Stoppenberg",
        "00211, Stadttei! Heisingen, Str.-Kl.:": "Stadtteil Heisingen",
        "02505, Stadteil Bochold, Str.-Kl.:": "Stadtteil Bochold",
        "02812, Stadttteil Kray, Str.-Kl.:": "Stadtteil Kray",
        "02874, Stadtteit Nordviertel, Str.-Kl.:": "Stadtteil Nordviertel",
        "00268, StadtteilBurgaltendorf, Str.-Kl.:": "Stadtteil Burgaltendorf",
        "02191, Stadt-teile FrillendorfundStoppenberg, Str.-Kl.:": "Stadtteile Frillendorf und Stoppenberg",
    }
    for roh, erwartet in faelle.items():
        assert erwartet in verbinde_zeilen(roh), roh


def test_stadtteilen_in_prosa_bleibt_unangetastet():
    assert "Stadtteilen" in verbinde_zeilen("in den Stadtteilen Kray und Leithe")


def test_und_zwischen_klein_und_gross_wird_getrennt():
    assert verbinde_zeilen("FrillendorfundStoppenberg") == "Frillendorf und Stoppenberg"
    assert verbinde_zeilen("Hundstraße") == "Hundstraße"
