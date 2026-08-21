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
