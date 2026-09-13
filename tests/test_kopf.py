import pytest

from strassen.kopf import parse_kopf, _stadienkette, bereinige_rand, HINWEIS_RANDZEICHEN


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


from strassen.namen import parse_namenskette, unverarbeiteter_rest


def test_fallback_kappt_nicht_am_tagespunkt():
    """Kamerunstraße, Schl.-Nr. 01635, S. 188 — Goldstandard-Fehler: keine Kette.
    Die strenge Kettenerkennung scheitert, weil nach dem letzten Stadium ein Komma
    statt eines Punkts steht; der alte Fallback zerschnitt den Rest bei '26. '."""
    rumpf = ("01635, Stadtteil Gerschede, Str.-Kl.: Gemeindestraße, Str.-Gr.: Stadt und Ort, "
             "26. Mai 1939: Kamerunstraße, Kamerun, eine ehemalige deutsche Kolonie im Westen "
             "Zentralafrikas, nach 1918 französisches bzw. britisches Mandatsgebiet, seit 1961 "
             "unabhängige Republik. Siehe auch Askaristraße,")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Stadt und Ort"
    s = parse_namenskette(k.rest)
    assert [(x.gueltig_ab, x.name) for x in s] == [("1939-05-26", "Kamerunstraße")]


def test_feldgrenze_springt_nicht_auf_tagesziffer():
    """An der Blumenwiese, Schl.-Nr. 01552, S. 48: Namensgruppe endete bei '14'."""
    rumpf = ("01552, Stadtteil Kray, Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
             "14. Dezember 1999: An der Blumenwiese. Sie war eine von zwei Straßen.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Lagebezeichnung"
    assert parse_namenskette(k.rest)[0].gueltig_ab == "1999-12-14"


def test_komma_vor_datum_darf_fehlen():
    """Hirtsieferstraße, Schl.-Nr. 01316, S. 160: '… Stadtverordneter 01. Oktober 1920: …'"""
    rumpf = ("01316, Stadtteil Holsterhausen, Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, Mann, "
             "Deutscher, Politiker, Stadtverordneter 01. Oktober 1920: Mercatorstraße, "
             "29. August 1946: Hirtsieferstraße. Heinrich Hirtsiefer *1876.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Person, Mann, Deutscher, Politiker, Stadtverordneter"
    assert [x.gueltig_ab for x in parse_namenskette(k.rest)] == ["1920-10-01", "1946-08-29"]


def test_namensgruppe_endet_vor_verstuemmeltem_datum():
    """Overhammshof, Schl.-Nr. 02356, S. 254 (Seitenumbruch mit Rauschen): Namensgruppe
    war 'Hofname, 21'. Das Rauschen selbst entfernt Task 7; hier zählt nur die Grenze."""
    rumpf = ("02356, Stadtteil Fischlaken, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
             "21. Januar mm nm mm nn nn 1970: Overhammshof. Nach dem Hofe Overhamm.")
    assert parse_kopf(rumpf).namensgruppe == "Hofname"


def test_namensgruppe_endet_vor_stern_tagesziffer():
    """Eligiushöhe, Schl.-Nr. 00756, S. 106: '…, Heiliger, *03. Oktober 1932: Eligiushöhe'."""
    rumpf = ("00756, Stadtteil Kupferdreh, Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, Mann, "
             "Deutscher, Bischof, Heiliger, *03. Oktober 1932: Eligiushöhe. Eligius war.")
    assert parse_kopf(rumpf).namensgruppe == "Person, Mann, Deutscher, Bischof, Heiliger"


def test_kette_mit_st_abkuerzung_bleibt_vollstaendig():
    """St. Annental, Schl.-Nr. 02727, S. 309."""
    rumpf = ("02727, Stadtteile Bergerhausen und Rellinghausen, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.: Kirche und Kloster, 04. Februar 1904: Kapellenstraße, 16. September 1910: "
             "Walpurgisstraße (tiw.), 18. September 1926: St. Annental. Am 25. Juli 1516 wurde bei "
             "Gelegenheit einer Kirmes aus der Rellinghauser Kirche ein Gefäß gestohlen.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("St. Annental.")
    assert [x.name for x in parse_namenskette(k.rest)][-1] == "St. Annental"


def test_marker_varianten_strassenklasse():
    """Adolfstraße 00015 'Str.-KL:', Amselweg 00265 'Str.-K.:', An den Friedhöfen 00150
    'Str.-Kt.:', Dachsfeld 00590 'Str:-Kl.:', Cäcilienstraße 00540 'Str.-Kl.;',
    Brandstorstraße 00421 'Str.-Kl.;:'."""
    for marker in ["Str.-KL:", "Str.-K.:", "Str.-Kt.:", "Str:-Kl.:", "Str.-Kl.;", "Str.-Kl.;:"]:
        rumpf = (f"00015, Stadtteil Rüttenscheid, {marker} Gemeindestraße, Str.-Gr.: "
                 "Männlicher Vorname, 06. September 1897: Adolfstraße.")
        k = parse_kopf(rumpf)
        assert k.strassenklassen == ["Gemeindestraße"], marker
        assert k.namensgruppe == "Männlicher Vorname", marker


def test_kopf_hat_hinweise_tupel():
    rumpf = "00127, Stadtteil Byfang, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, 31. März 1955: Am Schroer."
    assert parse_kopf(rumpf).hinweise == ()


def test_stadium_ohne_doppelpunkt_in_kette_wird_abgegrenzt():
    """Berghausbusch, Schl.-Nr. 00471, S. 84."""
    rumpf = ("00471, Stadtteil Kupferdreh, Str.-Kl.: Gemeindestraße, Str.-Gr.: Familienname, "
             "11. Dezember 1974 Berghausbusch. Jan Hendrich Berghaus war Bauer.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Familienname"
    assert [x.name for x in parse_namenskette(k.rest)] == ["Berghausbusch"]


def test_prosa_datum_nach_kette_wird_nicht_angehaengt():
    """Kein Stadium aus 'Am 25. Juli 1516 Wurde' (Wort vor dem Datum)."""
    rumpf = ("02727, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Kirche, "
             "18. September 1926: St. Annental. Am 25. Juli 1516 Wurde bei Gelegenheit.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("St. Annental.")


def test_klassenwort_ohne_marker_wird_uebernommen_mit_hinweis():
    """Eibergweg, Schl.-Nr. 00733, S. 105: '…, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: …'
    (13 Fälle im Material; geschlossenes Vokabular)."""
    rumpf = ("00733, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: Stadt und Ort, "
             "20. November 1937: Eibergweg.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.stadtteile == ["Freisenbruch"]
    assert "Straßenklasse ohne Marker" in k.hinweise


def test_klassenwort_ohne_marker_mehrere():
    rumpf = ("00905, Stadtteile Freisenbruch und Steele, Landstraße, Gemeindestraße, Str.-Gr.: "
             "Stadt und Ort, 01. Januar 1900: Freisenbruchstraße.")
    assert parse_kopf(rumpf).strassenklassen == ["Landstraße", "Gemeindestraße"]


def test_klassenwort_ohne_marker_nur_zwischen_stadtteil_und_gruppe():
    """Ein Klassenwort erst in der Namenskette ('… 1901: Hauptstraße') zählt nicht."""
    rumpf = ("00127, Stadtteil Byfang, Str.-Gr.: Flurname, 31. März 1955: Hauptstraße.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == []
    assert k.hinweise == ()


def test_klassenwert_mit_ocr_fehler_wird_korrigiert():
    """Auf der Bredde, Schl.-Nr. 00210, S. 57: 'Str.-Kl.: Gemeindstraße' (5 Fälle)."""
    rumpf = ("00210, Stadtteil Frillendorf, Str.-Kl.: Gemeindstraße, Str.-Gr.: Flurname, "
             "01. August 1921: Auf der Bredde.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.hinweise == ("Straßenklasse OCR-korrigiert",)


def test_klassenwert_mit_zwei_fehlern_bleibt_wie_gelesen():
    rumpf = ("00210, Stadtteil Frillendorf, Str.-Kl.: Gemeidstrase, Str.-Gr.: Flurname, "
             "01. August 1921: Auf der Bredde.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeidstrase"]
    assert k.hinweise == ()


def test_klassenwort_ohne_marker_ohne_stadtteilangabe():
    """Synthetisch: die 13 Korpus-Fälle tragen alle eine Stadtteil-Angabe; dieser Test
    sichert den Fallback ab, wenn diese ganz fehlt."""
    rumpf = "00733, Gemeindestraße, Str.-Gr.: Stadt und Ort, 20. November 1937: Eibergweg."
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.stadtteile == []
    assert "Straßenklasse ohne Marker" in k.hinweise


def test_kein_klassenwort_ohne_stadtteilangabe_und_ohne_klassenwort():
    rumpf = "00733, Str.-Gr.: Stadt und Ort, 20. November 1937: Eibergweg."
    k = parse_kopf(rumpf)
    assert k.strassenklassen == []
    assert "Straßenklasse ohne Marker" not in k.hinweise


def test_feldende_am_stringende():
    """Ein Klassenwert am absoluten Textende behält sonst seinen Schlusspunkt."""
    rumpf = "04000, Stadtteil Musterhausen, Str.-Kl.: Gemeindestraße."
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.hinweise == ()


def test_stadium_endet_auch_am_komma_vor_dem_naechsten_stempel():
    """Kämmereihude, Schl.-Nr. 01638, S. 185 — Goldstandard-Fehler: 2 von 3 Stadien
    fehlten. Nach 'I. Levenhove,' folgt kein Satzende (SATZENDE), sondern ein Komma
    direkt vor dem nächsten Datumsstempel — die strenge Kettenerkennung muss auch
    dort ein Stadium abschließen können, sonst bricht die Kette an dieser Stelle ab
    und ALLE folgenden Stadien fallen aus kopf.rest heraus (_MAX_LUECKE)."""
    rumpf = ("01638, Stadtteil Katernberg, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.: Flurname, 13. Februar 1896: Ill. Ziegelstraße, "
             "09. Juli 1915: I. Levenhove, 25. Februar 1937: Kämmereihude. "
             "Erläuterung folgt hier.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [x.name for x in s] == ["Ill. Ziegelstraße", "I. Levenhove", "Kämmereihude"]


def test_stadium_am_komma_bricht_kamerunstraße_nicht_zusaetzlich_auf():
    """Die Kamerunstraße-Kette (ein einziges Stadium) darf durch die neue
    Komma-Abschlussregel nicht in mehrere Stadien zerfallen."""
    rumpf = ("01635, Stadtteil Gerschede, Str.-Kl.: Gemeindestraße, Str.-Gr.: Stadt und Ort, "
             "26. Mai 1939: Kamerunstraße, Kamerun, eine ehemalige deutsche Kolonie im Westen "
             "Zentralafrikas, nach 1918 französisches bzw. britisches Mandatsgebiet, seit 1961 "
             "unabhängige Republik. Siehe auch Askaristraße,")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [(x.gueltig_ab, x.name) for x in s] == [("1939-05-26", "Kamerunstraße")]


def test_kette_ueber_semikolon_hinweg_frau_bertha_krupp():
    """Frau-Bertha-Krupp-Straße, Schl.-Nr. 00896, S. 118 — Fix Task 12, Runde 1:
    kopf._STADIUM matchte auf dieser Kette nur den letzten Stempel (der einzige mit
    echtem Satzende) und `kopf.rest` reichte per Zufall bis dorthin. Die alte
    Komma-Abschlussregel (Runde 1) ließ das erste Stadium schon bei 'Berthastraße,'
    enden (kurz vor dem Semikolon-getrennten zweiten Stadium) — die dadurch verschobene
    Lücken-Messung (_MAX_LUECKE) brach die Kette vorzeitig ab, 4 von 5 Stadien fielen
    aus. Die neue, stempelbasierte Kette (Runde 2) muss alle 5 Stadien liefern,
    Semikolon zählt wie Komma als erlaubte Trennerposition."""
    rumpf = ("00896, Stadtteil Südviertel, Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, "
             "Frau, Deutsche, Familie Krupp, Essener Geschichte und Örtlichkeit, "
             "05. Juli 1889: Berthastraße, 26. Januar 1906: Frau-Berta-Krupp-Straße; "
             "23. September 1892: Alexstraße, 09. Juli 1915: Frau-Berta-Krupp-Straße "
             "(Verl), 12. Dezember 1957: Frau-Bertha-Krupp-Straße. Bertha Krupp "
             "(geb. Eichhoff) *13. Dezember 1831 in Köln.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [x.name for x in s] == [
        "Berthastraße", "Frau-Berta-Krupp-Straße", "Alexstraße",
        "Frau-Berta-Krupp-Straße (Verl.)", "Frau-Bertha-Krupp-Straße",
    ]


def test_kette_mit_unlesbarem_zwischenstempel_siebrechtweg():
    """Siebrechtweg, Schl.-Nr. 00718, S. 303 — Fix Task 12, Runde 1: derselbe
    Lücken-Bruch traf hier über einen per Positionsregel abgelehnten Zwischenstempel
    ('04. April 1986 aufgehoben:' — kein Doppelpunkt direkt nach dem Datum,
    kleingeschriebener Namensrest). Die neue Kette darf davon nicht abbrechen: beide
    echten Stadien (1974, 2006) bleiben erhalten, der unlesbare Zwischenstempel bleibt
    als Rauschen im Rest liegen und wird über 'Namenskette unvollständig gelesen'
    (Fix B, Runde 1) sichtbar statt zu verschwinden."""
    rumpf = ("00718, Stadtteil Altenessen-Nord, Str.-Kl.: Gemeindestraße, Str.-Gr.: "
             "Person, Mann, Deutscher, Gerichtsassessor, 11. Dezember 1974: "
             "Siebrechtweg, 04. April 1986 aufgehoben: Siebrechtweg, 31. Januar 2006: "
             "Siebrechtweg. Fritz (Friedrich) Siebrecht war ein Dr.-jur. h.c.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [(x.gueltig_ab, x.name) for x in s] == [
        ("1974-12-11", "Siebrechtweg"), ("2006-01-31", "Siebrechtweg"),
    ]
    residuum = unverarbeiteter_rest(k.rest)
    assert "1986" in residuum


def test_stempel_nach_semikolon_setzt_kette_fort():
    """Ein Stempel direkt nach Semikolon zählt wie einer nach Komma als
    Kettenfortsetzung (Fix Task 12, Runde 2)."""
    rumpf = ("00001, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, "
             "01. Januar 1900: Altname; 02. Februar 1950: Neuname.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [x.name for x in s] == ["Altname", "Neuname"]


def test_starker_stempel_nach_satzpunkt_setzt_kette_fort_natorpstrasse():
    """Natorpstraße, Schl.-Nr. 02287, S. 243 — Fix Task 12, Runde 2 (Regression):
    'Taubenstraße (Verl). 17. März 1971: Natorpstraße.' trennt die letzten beiden
    Stadien durch einen echten Satzpunkt statt durch Komma. Die Positionsregel darf
    einen STARKEN Stempel (regulärer Doppelpunkt) davon nicht ausschließen, sonst
    fällt das namensgebende letzte Stadium aus der Kette."""
    rumpf = ("02287, Stadtteil Ostviertel, Str.-Kl.: Gemeindestraße, Str.-Gr.: "
             "Person, Mann, Deutscher, Lehrer, 05. Juli 1889: Taubenstraße, "
             "19. September 1925: Taubenstraße (Verl). 17. März 1971: Natorpstraße. "
             "Gustav Natorp war Lehrer.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [x.name for x in s] == ["Taubenstraße", "Taubenstraße (Verl.)", "Natorpstraße"]


def test_starker_stempel_nach_prosa_setzt_kette_fort_frohnhauser_strasse():
    """Frohnhauser Straße, Schl.-Nr. 00930, S. 122 — Fix Task 12, Runde 2
    (Regression): der letzte, namensgebende Stempel steht nach den Wörtern
    'gemeinsame Bezeichnung am', nicht nach Komma/Semikolon. Als starker Stempel
    (regulärer Doppelpunkt) muss er die Kette trotzdem fortsetzen."""
    rumpf = ("00930, Stadtteile Stadtkern, Westviertel, Holsterhausen und "
             "Frohnhausen, Str.-Kl.: Kreisstraße, Landstraße, Str.-Gr.: "
             "Lagebezeichnung, um 1860: Frohnhauser Straße, vor 1885: "
             "Herrenbankstraße (Umb.), urspr.: Essen-Mülheimer-Straße (Umb.), "
             "gemeinsame Bezeichnung am 13. Dezember 1901: Frohnhauser Straße. "
             "Siehe Frohnhauser Platz.")
    k = parse_kopf(rumpf)
    s = parse_namenskette(k.rest)
    assert [x.name for x in s] == [
        "Frohnhauser Straße", "Herrenbankstraße (Umb.)",
        "Essen-Mülheimer-Straße (Umb.)", "Frohnhauser Straße",
    ]


def test_schwacher_stempel_nach_satzpunkt_stoppt_die_kette_weiterhin():
    """St. Annental, Schl.-Nr. 02727 — bestehender Prosafall: ein SCHWACHER Stempel
    ('Am 25. Juli 1516 wurde', kein Doppelpunkt) nach einem Satzpunkt bleibt Prosa
    und darf die Kette nicht fortsetzen — die Lockerung in Runde 3 gilt nur für
    starke Stempel."""
    rumpf = ("02727, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Kirche, "
             "18. September 1926: St. Annental. Am 25. Juli 1516 Wurde bei Gelegenheit.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("St. Annental.")


def test_starker_stempel_ausserhalb_der_namenslaenge_bleibt_prosa():
    """Ein starker Stempel weit hinter dem letzten Stadium (mehr als
    _MAX_NAMENSLAENGE Zeichen) gehört nicht mehr zur Kette, selbst wenn er
    regulär mit Doppelpunkt geschrieben ist — sonst würde jedes spät im
    Fließtext zitierte Datum die Kette künstlich verlängern."""
    # Füllzeichen bewusst synthetisch: nur die LÄNGE des Abstands wird geprüft.
    fuelltext = "Aus welchem Anlass die Straße diesen Namen erhielt ist unklar" + "!" * 45
    rumpf = ("00001, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, "
             "01. Januar 1900: X. " + fuelltext + " 01. Januar 1950: Y.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("X.")


def test_erster_stempel_weit_im_schwanz_oeffnet_keine_kette():
    """Abschlussreview: die Abstandsregel _MAX_NAMENSLAENGE gilt auch für den ERSTEN
    Stempel, gemessen ab Beginn des Schwanzes — sonst öffnet ein beliebig tief in der
    Erläuterung zitiertes Datum die Kette."""
    prosa = ("Der Name geht auf einen alten Hof zurueck der hier einst stand und lange "
             "bestand und niemand mehr kennt")
    assert len(prosa) > 100      # mehr als _MAX_NAMENSLAENGE vor dem Stempel
    assert _stadienkette(prosa + ". 01. Januar 1950: Y.") is None
    rumpf = ("00002, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname. "
             + prosa + ". 01. Januar 1950: Y.")
    k = parse_kopf(rumpf)
    # ohne Kette greift der Fallback (erstes Satzende); das zitierte Datum bleibt draußen
    assert "1950" not in k.rest


def test_erster_stempel_nach_urspr_klausel_oeffnet_die_kette():
    """Gegenprobe: eine legitime 'urspr.:'-Klausel vor dem ersten Stempel (im Material
    bis ~81 Zeichen) bleibt innerhalb der Abstandsregel."""
    vorlauf = "urspr.: Alter Name, gemeinsame Bezeichnung am"      # ~45 Zeichen
    assert _stadienkette(vorlauf + " 01. Januar 1950: Neustraße.") is not None
    rumpf = ("00003, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, "
             + vorlauf + " 01. Januar 1950: Neustraße.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("01. Januar 1950: Neustraße.")


@pytest.mark.parametrize("roh,soll", [
    (") Am Richtenberg", "Am Richtenberg"), ("” An der Braut", "An der Braut"),
    ("„ Gemeindestraße", "Gemeindestraße"), ("nn Hattenheimer Straße", "Hattenheimer Straße"),
    ("ia Auf dem Sutan", "Auf dem Sutan"),
])
def test_bereinige_rand_entfernt_rauschen_mit_hinweis(roh, soll):
    assert bereinige_rand(roh) == (soll, HINWEIS_RANDZEICHEN)


@pytest.mark.parametrize("wert", ["Am Handelshof", "Aachener Straße", "I. Buschlandweg", "Auf'm Uhlenbroich"])
def test_bereinige_rand_laesst_saubere_werte(wert):
    assert bereinige_rand(wert) == (wert, "")


def test_feldrest_semikolon_unterstrich_entfernt():
    k = parse_kopf("01008, Stadtteil Holsterhausen; _, Str.-Kl.: Gemeindestraße; _, Str.-Gr.: Flurname, 1900: Test.")
    assert k.stadtteile == ["Holsterhausen"] and k.strassenklassen == ["Gemeindestraße"]
