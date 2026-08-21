from strassen.segmentierung import segmentiere, ANKER


def test_verstuemmelter_anker_wird_erkannt():
    """'Sch!.-Nr.:' kam im echten OCR vor (Kütings Garten, S. 211).
    122 der 3340 Einträge tragen einen entstellten Anker."""
    for variante in ["Schl.-Nr.:", "Sch!.-Nr.:", "Scht.-Nr.:", "Schi.-Nr.:",
                     "Schl-Nr.:", "Schl.-Nr:", "Sch.-Nr.:", "Schtl.-Nr.:"]:
        assert ANKER.search(f"Beispielstraße: {variante} 01234"), variante


def test_komma_statt_punkt_nach_schl_wird_erkannt():
    """'Schl,-Nr.:' (Komma statt Punkt) kam im echten OCR 11-mal vor
    (u. a. Herkendell S. 156, Kalthofweg S. 188, Im Dreieck S. 175) und
    wurde vom Anker verpasst, wodurch der Eintrag komplett fehlte und sein
    Text in den rest des Vorgängers blutete."""
    assert ANKER.search("Herkendell: Schl,-Nr.: 03676, Stadtteil Kettwig")


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


def test_anker_ohne_lemma_wird_optional_in_verworfene_erfasst():
    """Ein Anker ohne davorstehendes Lemma-Doppelpunkt-Muster wird nicht
    stillschweigend verworfen: mit übergebener verworfene-Liste landet er
    dort als (buchseite, kontext_ausschnitt) statt spurlos zu verschwinden
    (zuletzt 8 Fälle im echten Material)."""
    seiten = [(300, "Anlage ohne Eigenname Schl.-Nr.: 09999, Stadtteil Nirgendwo, "
                    "Str.-Kl.: Gemeindestraße. "
                    "Kütings Garten: Schl.-Nr.: 01838, Stadtteil Freisenbruch.")]
    verworfene = []
    eintraege = segmentiere(seiten, verworfene=verworfene)
    assert len(eintraege) == 1
    assert eintraege[0].lemma_roh == "Kütings Garten"
    assert len(verworfene) == 1
    buchseite, kontext = verworfene[0]
    assert buchseite == 300
    assert "Eigenname" in kontext


def test_lemma_mit_abkuerzungspunkt_bleibt_vollstaendig():
    """'St.-Ingbert-Höhe' wurde bislang am Punkt nach 'St' abgeschnitten
    ([^.,;:] schließt jeden Punkt aus) — das Lemma kam nur als
    '-Ingbert-Höhe' an (>=21 betroffene Zeilen im Material, u. a. S. 227/272).
    Ein Punkt, der direkt von einem Bindestrich oder Buchstaben gefolgt wird
    (Abkürzung), darf die Rückwärtssuche nicht abbrechen; ein echter
    Satzende-Punkt (gefolgt von Leerzeichen) weiterhin schon."""
    seiten = [(227, "Vorheriger Eintrag endet hier. "
                    "St.-Ingbert-Höhe: Schl.-Nr.: 02728, Stadtteil Byfang.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "St.-Ingbert-Höhe"


def test_segmentiere_ohne_verworfene_parameter_bleibt_kompatibel():
    """Bestehende Aufrufe segmentiere(seiten) ohne den neuen Parameter
    müssen unverändert funktionieren."""
    seiten = [(211, "Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    eintraege = segmentiere(seiten)
    assert len(eintraege) == 1
