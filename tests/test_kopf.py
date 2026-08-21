from strassen.kopf import parse_kopf


def test_vollstaendiger_kopf():
    rumpf = ("01818, Stadtteil Stadtkern, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.: Essener Geschichte und Örtlichkeit, urspr.: Pottgasse, "
             "07. Februar 1908: Kronenstraße. Die Pottgasse wurde auf intensives "
             "Betreiben der Anlieger in Kronenstraße umbenannt.")
    k = parse_kopf(rumpf)
    assert k.schl_nr == "01818"
    assert k.stadtteile == ["Stadtkern"]
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.namensgruppe == "Essener Geschichte und Örtlichkeit"
    assert "urspr.: Pottgasse" in k.rest
    assert "Die Pottgasse wurde" not in k.rest      # Erläuterung abgeschnitten


def test_mehrere_stadtteile_und_klassen():
    """'Stadtteile X und Y' sowie mehrere Klassen kommen real vor (Kruppstraße)."""
    rumpf = ("01826, Stadtteile Holsterhausen und Südviertel, "
             "Str.-Kl.: Kreisstraße, Gemeindestraße, Str.-Gr.: Familienname, "
             "16. Mai 1902: Kruppstraße. Siehe Kruppallee.")
    k = parse_kopf(rumpf)
    assert k.stadtteile == ["Holsterhausen", "Südviertel"]
    assert k.strassenklassen == ["Kreisstraße", "Gemeindestraße"]


def test_fehlende_strassenklasse_ergibt_leere_liste():
    rumpf = "00127, Stadtteil Byfang, Str.-Gr.: Flurname, 31. März 1955: Am Schroer."
    k = parse_kopf(rumpf)
    assert k.strassenklassen == []
    assert k.namensgruppe == "Flurname"


def test_ohne_schluesselnummer_kein_kopf():
    assert parse_kopf("Stadtteil Byfang, Str.-Gr.: Flurname.") is None


def test_stadtteile_mit_komma_und_und():
    """Reale Aufzählung mit mehreren Kommas und 'und' (Altendorfer Straße,
    S. 30, 4 Stadtteile) — die reine Komma-Grenze der ersten Fassung kappte
    die Liste still auf das erste Element."""
    rumpf = ("00050, Stadtteile Altendorf, Bochold, Schönebeck und Westviertel, "
             "Str.-Kl.: Bundesstraße, Landstraße, Str.-Gr.: Lagebezeichnung, "
             "04. Dezember 1901: Altendorfer Straße.")
    k = parse_kopf(rumpf)
    assert k.stadtteile == ["Altendorf", "Bochold", "Schönebeck", "Westviertel"]


def test_erlaeuterung_mit_jahreszahl_wird_nicht_als_stadium_gelesen():
    """Realer Fall (Pottgießerstraße, S. 264): '... am 02. Mai 1739.
    Mutterrolle 1826: Besitzer ist ...' in der Erläuterung. Ohne Beschränkung
    auf echte Monatsnamen liest die Stadium-Regex '39.' (Endziffern von
    '1739') als Tag und 'Mutterrolle' als Monat und zieht die gesamte
    Erläuterung in rest."""
    rumpf = ("02453, Stadtteil Frohnhausen, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.: Hofname, 16. Oktober 1916: Pottgießerstraße. Der "
             "Pottgießerhof gehörte der Familie Pottgießer am 02. Mai 1739. "
             "Mutterrolle 1826: Besitzer ist Eberhard Pottgießer.")
    k = parse_kopf(rumpf)
    assert "Mutterrolle" not in k.rest
    assert k.rest == ", 16. Oktober 1916: Pottgießerstraße."


def test_klammerzusatz_am_stadiumsende_bleibt_geschlossen():
    """Realer Fall (Altenessener Straße, Schl.-Nr. 00053): der Punkt in
    '(Verl.)' darf das Stadium nicht schon innerhalb der Klammer beenden —
    nur der echte Satzpunkt danach tut das. Die alte 'stoppe am ersten
    Punkt'-Regel kappte hier auf '...(Verl.' statt '...(Verl.)'."""
    rumpf = ("00053, Str.-Gr.: Lagebezeichnung, "
             "09. Juli 1915: Altenessener Straße (Verl.). "
             "Die Erläuterung beginnt hier.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("Altenessener Straße (Verl.).")
    assert "Erläuterung" not in k.rest


def test_ziffernblock_mit_leerzeichen_wird_toleriert():
    """OCR trennt den Ziffernblock manchmal mit einem Leerzeichen ('01 544')
    — ohne Toleranz brach _NUMMER am ersten Fragment ab ('01'), wodurch
    mehrere verschiedene Straßen auf derselben (falschen, zu kurzen) Nummer
    kollidierten (u. a. 11 Straßen auf 00001; Hachestraße '011 52' wurde
    unauffällig zu 00011 statt 01152)."""
    rumpf = "01 544, Stadtteil Rüttenscheid, Str.-Kl.: Gemeindestraße."
    k = parse_kopf(rumpf)
    assert k.schl_nr == "01544"


def test_ziffernblock_zu_lang_ergibt_keinen_kopf():
    """Nach dem Entfernen der Leerzeichen dürfen es nicht mehr als 5 Ziffern
    sein — sonst lieber kein Kopf (None) als eine geratene Nummer."""
    assert parse_kopf("1 2 3 4 5 6, Stadtteil X.") is None


def test_marker_variante_ohne_r_wird_erkannt():
    """'St.-Gr.:' (fehlendes 'r' in 'Str') kam im OCR vor (4 Zeilen, u. a.
    Helenenstraße Schl.-Nr. 01261) — ohne Toleranz blieb namensgruppe leer."""
    rumpf = ("01261, Stadtteil Stadtkern, St.-Gr.: Person, "
             "01. Januar 1900: Helenenstraße.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Person"


def test_marker_mit_semikolon_statt_doppelpunkt_wird_erkannt():
    """'Str.-Gr.;' (Semikolon statt Doppelpunkt) kam im OCR vor
    (St.-Ingbert-Höhe, Schl.-Nr. 02728) — ohne Toleranz blieb namensgruppe
    leer und strassenklasse blutete in die nachfolgende Namenskette
    ('Gemeindestraße; Ort; etwa 1921: Nelkenstraße; 14')."""
    rumpf = ("02728, Stadtteil Leithe, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.; Stadt und Ort, etwa 1921: Nelkenstraße, "
             "14. November 1935: St.-Ingbert-Höhe.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Stadt und Ort"
    assert k.strassenklassen == ["Gemeindestraße"]


def test_marker_ohne_zweites_r_wird_erkannt():
    """'Str.-G.:' (fehlendes zweites 'r' in 'Gr') kam im OCR vor
    (Ilse-Menz-Weg, Schl.-Nr. 00700)."""
    rumpf = ("00700, Stadtteil Stadtkern, Str.-Kl.: Gemeindestraße, "
             "Str.-G.: Person, Frau, Deutsche, Kinobetreiberin, "
             "20. April 2004: Ilse-Menz-Weg.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Person, Frau, Deutsche, Kinobetreiberin"
    assert k.strassenklassen == ["Gemeindestraße"]
