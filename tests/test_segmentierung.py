import pytest

from strassen.segmentierung import segmentiere, ANKER, HINWEIS_ANKER_KORRIGIERT


def _eintraege(text, seite=1):
    return segmentiere([(seite, text)])


def test_verstuemmelter_anker_wird_erkannt():
    """'Sch!.-Nr.:' kam im echten OCR vor (Kütings Garten, S. 211).
    122 der 3340 Einträge tragen einen entstellten Anker. Jede Abweichung von
    der kanonischen Form 'Schl.-Nr.:' erzeugt zusätzlich den Hinweis
    HINWEIS_ANKER_KORRIGIERT (R6) — nur die kanonische Form selbst nicht."""
    for variante in ["Sch!.-Nr.:", "Scht.-Nr.:", "Schi.-Nr.:",
                     "Schl-Nr.:", "Schl.-Nr:", "Sch.-Nr.:", "Schtl.-Nr.:"]:
        assert ANKER.search(f"Beispielstraße: {variante} 01234"), variante
        e = _eintraege(f"Vorlauf. Beispielstraße: {variante} 01234, Stadtteil X")
        assert e[0].hinweise == (HINWEIS_ANKER_KORRIGIERT,), variante
    assert ANKER.search("Beispielstraße: Schl.-Nr.: 01234")
    e = _eintraege("Vorlauf. Beispielstraße: Schl.-Nr.: 01234, Stadtteil X")
    assert e[0].hinweise == ()


def test_komma_statt_punkt_nach_schl_wird_erkannt():
    """'Schl,-Nr.:' (Komma statt Punkt) kam im echten OCR 11-mal vor
    (u. a. Herkendell S. 156, Kalthofweg S. 188, Im Dreieck S. 175) und
    wurde vom Anker verpasst, wodurch der Eintrag komplett fehlte und sein
    Text in den rest des Vorgängers blutete. Als Abweichung von der
    kanonischen Form trägt der Eintrag zusätzlich HINWEIS_ANKER_KORRIGIERT."""
    assert ANKER.search("Herkendell: Schl,-Nr.: 03676, Stadtteil Kettwig")
    e = _eintraege("Vorlauf. Herkendell: Schl,-Nr.: 03676, Stadtteil Kettwig")
    assert e[0].hinweise == (HINWEIS_ANKER_KORRIGIERT,)


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


def test_lemma_mit_st_abkuerzung_und_leerzeichen():
    """St. Annental, Schl.-Nr. 02727, S. 309 — Goldstandard-Fehler: Lemma war 'Annental'.
    15 Lemmata im Material beginnen mit 'St. ' (Leerzeichen, nicht Bindestrich)."""
    seiten = [(309, "Lit.: Herbert Steinhardt. In: Das Münster am Hellweg 1975, S. 139 ff. "
                    "St. Annental: Schl.-Nr.: 02727, Stadtteile Bergerhausen und Rellinghausen, "
                    "Str.-Kl.: Gemeindestraße.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "St. Annental"


def test_lemma_mit_st_bindestrich_bleibt():
    seiten = [(309, "Text. St.-Ingbert-Höhe: Schl.-Nr.: 02728, Stadtteil Leithe.")]
    assert segmentiere(seiten)[0].lemma_roh == "St.-Ingbert-Höhe"


def test_lemma_endet_weiterhin_am_satzpunkt():
    seiten = [(211, "Erläuterung endet hier. Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    assert segmentiere(seiten)[0].lemma_roh == "Kruselbeek"


def test_roemischer_praefix_bleibt_im_lemma():
    # S. 86, 00502/00503 (Prüfliste: 24 Lemmata ohne I./II./III.)
    e = _eintraege("Akten: STAD Best. Reg. Düsseldorf Nr. 19164. I. Buschlandweg: Schl.-Nr.: 00502, Stadtteil Frillendorf, "
                   "Str.-Kl.: Gemeindestraße. II. Buschlandweg: Schl.-Nr.: 00503, Stadtteil Frillendorf")
    assert [x.lemma_roh for x in e] == ["I. Buschlandweg", "II. Buschlandweg"]


def test_satzpunkt_vor_lemma_bricht_weiterhin_ab():
    e = _eintraege("gehört zur Flur. Aachener Straße: Schl.-Nr.: 00001, Stadtteil Frohnhausen")
    assert e[0].lemma_roh == "Aachener Straße"


@pytest.mark.parametrize("text,lemma,hinweis", [
    ("Bd. 85/1970; 5. 5 ff. Brunhildenstraße; Schl.-Nr.: 00465, Stadtteil Kray", "Brunhildenstraße", ()),           # S. 82
    ("Rep. 113 Nr. 565. Waldblick; Schl.-Nr.: 03297, Stadtteil Stadtwald", "Waldblick", ()),                         # S. 338
    ("an Rutger von Bergerhausen. Am Schloss Schellenberg:; Schl.-Nr.: 00710, Stadtteil", "Am Schloss Schellenberg", ()),  # S. 42
    ("zur Kenntnis gegeben. Graitengraben: Sch}.-Nr.: 01067, Stadtteil", "Graitengraben", ("Anker OCR-korrigiert",)),  # S. 133
    ("eine Ballonfabrik. Riegelweg: Sch).-Nr.: 02599, Stadtteil", "Riegelweg", ("Anker OCR-korrigiert",)),           # S. 274
    ("Bedeutung gewonnen. Schraeplerstraße:  Schl.-N.: 02821, Stadtteil", "Schraeplerstraße", ("Anker OCR-korrigiert",)),  # S. 296
    ("auch Markesfeld. Marreweg: -Schl.-Nr.: 02086, Stadtteil", "Marreweg", ("Anker OCR-korrigiert",)),              # S. 231
    ("Siehe Mallinckrodtplatz. Malmedystraße: Schl.-Nr.; 02070, Stadtteil", "Malmedystraße", ("Anker OCR-korrigiert",)),  # S. 229
])
def test_anker_und_trenner_varianten(text, lemma, hinweis):
    e = _eintraege(text)
    assert len(e) == 1 and e[0].lemma_roh == lemma
    assert e[0].hinweise == hinweis


def test_ill_als_ocr_form_von_iii_bricht_rueckwaertssuche_nicht():
    """OCR liest 'III.' oft als 'Ill.' (S. 283 Ill. Ruschenfeld, S. 315 Ill.
    Stiege, S. 321 Ill. Terwestenweg) — der Punkt danach ist Ordnungspunkt,
    kein Satzende, und darf die Rückwärtssuche nicht abbrechen (Fix Runde 1,
    Ergänzung zu R4)."""
    e = _eintraege("Reg. Nr. 1. Ill. Ruschenfeld: Schl.-Nr.: 02700, Stadtteil")
    assert e[0].lemma_roh == "Ill. Ruschenfeld"


def test_versprengter_grossbuchstabe_vor_anker_wird_toleriert():
    """02834 Schulte-Hinsel-Straße, S. 298: OCR setzt zwischen Trenner und
    Anker ein verirrtes 'S' ('Schulte-Hinsel-Straße:\\n\\nS Schl.-Nr.:' — nach
    verbinde_zeilen sind die Zeilenumbrüche Leerzeichen). Bislang schlug hier
    die Lemma-Suche fehl und der Eintrag landete als 'Anker ohne Lemma'. Ein
    einzelner Großbuchstabe plus Leerraum vor dem Anker wird toleriert; die
    Abweichung von der kanonischen Form macht ihn zugleich zu 'Anker
    OCR-korrigiert'."""
    e = _eintraege("unter-gebracht. Schulte-Hinsel-Straße: S Schl.-Nr.: 02834, Stadtteil")
    assert len(e) == 1
    assert e[0].lemma_roh == "Schulte-Hinsel-Straße"
    assert not e[0].lemma_roh.endswith("S")
    assert e[0].hinweise == (HINWEIS_ANKER_KORRIGIERT,)
