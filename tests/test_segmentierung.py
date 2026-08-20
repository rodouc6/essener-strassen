from strassen.segmentierung import segmentiere, ANKER


def test_verstuemmelter_anker_wird_erkannt():
    """'Sch!.-Nr.:' kam im echten OCR vor (Kütings Garten, S. 211).
    122 der 3340 Einträge tragen einen entstellten Anker."""
    for variante in ["Schl.-Nr.:", "Sch!.-Nr.:", "Scht.-Nr.:", "Schi.-Nr.:",
                     "Schl-Nr.:", "Schl.-Nr:", "Sch.-Nr.:", "Schtl.-Nr.:"]:
        assert ANKER.search(f"Beispielstraße: {variante} 01234"), variante


def test_eintrag_traegt_lemma_und_buchseite():
    seiten = [(211, "Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken, "
                    "Str.-Kl.: Gemeindestraße. Erläuterung. "
                    "Kuckucksrain: Schl.-Nr.: 01828, Stadtteile Rellinghausen und Stadtwald.")]
    eintraege = segmentiere(seiten)
    assert len(eintraege) == 2
    assert eintraege[0].lemma_roh == "Kruselbeek"
    assert eintraege[0].buchseite == 211
    assert eintraege[1].lemma_roh == "Kuckucksrain"


def test_eintrag_ueber_seitengrenze_behaelt_startseite():
    """Ein Eintrag am Seitenende läuft auf der Folgeseite weiter; belegt wird
    die Seite, auf der er beginnt."""
    seiten = [(210, "Kruppstraße: Schl.-Nr.: 01826, Stadtteile Holsterhausen und Südviertel, "
                    "Str.-Kl.: Kreisstraße, Gemeindestraße, Str.-Gr.: Familienname, "
                    "16. Mai 1902: Kruppstraße. Siehe"),
              (211, "Kruppallee. Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "Kruppstraße"
    assert eintraege[0].buchseite == 210
    assert "Kruppallee" in eintraege[0].rumpf
    assert eintraege[1].buchseite == 211


def test_komma_am_seitenende_wird_nicht_ins_lemma_gezogen():
    """Echter Fall S. 210/211: Die Seite endet mit einem Komma ('...Siehe
    Kruppallee,'), nicht mit einem Punkt. Ohne Komma-Ausschluss in der
    Lemma-Regex sucht die Rückwärtssuche über das Komma hinweg weiter und
    zieht 'Siehe Kruppallee,' ins Lemma des Folgeeintrags ('Siehe Kruppallee,
    Kruselbeek' statt 'Kruselbeek'), wodurch auch die Buchseite falsch auf
    210 statt 211 fällt."""
    seiten = [(210, "Kruppstraße: Schl.-Nr.: 01826, Stadtteile Holsterhausen und Südviertel, "
                    "Str.-Kl.: Kreisstraße, Gemeindestraße, Str.-Gr.: Familienname, "
                    "16. Mai 1902: Kruppstraße. Siehe Kruppallee,"),
              (211, "Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "Kruppstraße"
    assert "Siehe Kruppallee" in eintraege[0].rumpf
    assert eintraege[1].lemma_roh == "Kruselbeek"
    assert eintraege[1].buchseite == 211
