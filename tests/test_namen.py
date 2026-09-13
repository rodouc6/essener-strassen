import pytest

from strassen.namen import HINWEIS_ZUSATZ_ERGAENZT, normalisiere_zusatz, parse_namenskette


def test_dreistufige_kette_mit_tagesdatum():
    """Kütings Garten, S. 211 — der Beleg dafür, dass die Straße 1936
    'Klosterstraße' hieß."""
    rest = ("18. November 1904: Kirchstraße, 01. Juni 1926: Klosterstraße, "
            "20. November 1937: Kütings Garten.")
    s = parse_namenskette(rest)
    assert [x.name for x in s] == ["Kirchstraße", "Klosterstraße", "Kütings Garten"]
    assert [x.gueltig_ab for x in s] == ["1904-11-18", "1926-06-01", "1937-11-20"]
    assert all(x.datum_praezision == "tag" for x in s)
    assert [x.stadium for x in s] == [1, 2, 3]


def test_urspruenglicher_name_ohne_datum():
    rest = "urspr.: Pottgasse, 07. Februar 1908: Kronenstraße."
    s = parse_namenskette(rest)
    assert s[0].name == "Pottgasse"
    assert s[0].ist_urspruenglich is True
    assert s[0].gueltig_ab == ""
    assert s[0].datum_praezision == "unbekannt"
    assert s[1].name == "Kronenstraße"
    assert s[1].datum_praezision == "tag"


def test_jahresangabe_ohne_tag():
    rest = "1902: Barkhofstraße."
    s = parse_namenskette(rest)
    assert s[0].gueltig_ab == "1902"
    assert s[0].datum_praezision == "jahr"


def test_leere_kette_ergibt_leere_liste():
    assert parse_namenskette("Siehe Hohenzollernstraße.") == []


def test_mehrfaches_urspr_wird_vollstaendig_erfasst():
    """Altenessener Straße, Schl.-Nr. 00053 — zwei 'urspr.:'-Stadien in einer
    Kette; mit nur einem _URSPR.search()-Treffer ging das zweite
    ('Essen-Horster-Straße') ersatzlos verloren."""
    rest = ("urspr.: Viehofer Chausee, 07. August 1908: Altenessener Straße, "
            "urspr.: Essen-Horster-Straße, 09. Juli 1915: "
            "Altenessener Straße (Verl.).")
    s = parse_namenskette(rest)
    assert [x.name for x in s] == [
        "Viehofer Chausee", "Altenessener Straße",
        "Essen-Horster-Straße", "Altenessener Straße (Verl.)",
    ]
    assert [x.ist_urspruenglich for x in s] == [True, False, True, False]
    assert [x.stadium for x in s] == [1, 2, 3, 4]


def test_name_mit_abkuerzungspunkt_bleibt_erhalten():
    """'St.-Ingbert-Höhe' darf nicht am Punkt nach 'St' abgeschnitten werden."""
    rest = "18. November 1904: St.-Ingbert-Höhe, 01. Juni 1926: Folgename."
    s = parse_namenskette(rest)
    assert s[0].name == "St.-Ingbert-Höhe"


def test_name_mit_klammerzusatz_am_satzende():
    """'(Verl.)' ist Teil des Namens; nur der abschließende Satzpunkt nicht."""
    rest = "09. Juli 1915: Altenessener Straße (Verl.). Erläuterung beginnt"
    s = parse_namenskette(rest)
    assert s[0].name == "Altenessener Straße (Verl.)"


def test_naechstes_stadium_ohne_komma_wird_nicht_ins_namensende_gezogen():
    """Natorpstraße: ein Folgestadium kann statt mit Komma mit einem echten
    Satzpunkt eingeleitet sein. Das Satzende-Muster muss auch die Tagesziffer
    des nächsten vollen Datums als Grenze erkennen, nicht nur Großbuchstaben —
    sonst rutscht '17' aus '17. März 1971' ins vorige Namensende."""
    rest = ("05. Juli 1889: Taubenstraße, 19. September 1925: Taubenstraße "
            "(Verl). 17. März 1971: Natorpstraße.")
    s = parse_namenskette(rest)
    assert [x.name for x in s] == ["Taubenstraße", "Taubenstraße (Verl.)", "Natorpstraße"]
    assert [x.gueltig_ab for x in s] == ["1889-07-05", "1925-09-19", "1971-03-17"]
    assert [x.datum_praezision for x in s] == ["tag", "tag", "tag"]


def test_st_abkuerzung_bleibt_im_namen():
    """St. Annental, Schl.-Nr. 02727, S. 309 — Goldstandard-Fehler: Stadium 3 hieß 'St'."""
    rest = ("04. Februar 1904: Kapellenstraße, 16. September 1910: Walpurgisstraße (tiw.), "
            "18. September 1926: St. Annental.")
    s = parse_namenskette(rest)
    assert [x.name for x in s] == ["Kapellenstraße", "Walpurgisstraße (tlw.)", "St. Annental"]


def test_roemische_zahl_bleibt_im_namen():
    """Gerswidastraße, Schl.-Nr. 01022, S. 127 — Goldstandard-Fehler: Stadium 1 hieß 'II'."""
    s = parse_namenskette("vor 1826: II. Weberstraße, 13. Juni 1966: Gerswidastraße.")
    assert s[0].name == "II. Weberstraße"
    assert s[0].datum_praezision == "vor"
    assert s[1].name == "Gerswidastraße"


def test_stadium_traegt_hinweis_aus_datum():
    s = parse_namenskette("13, Juni 1973: Eskenshof.")
    assert s[0].gueltig_ab == "1973-06-13"
    assert s[0].hinweis == "Datum: Komma nach Tag"


def test_regulaeres_stadium_hat_leeren_hinweis():
    s = parse_namenskette("16. Mai 1902: Kruppstraße.")
    assert s[0].hinweis == ""


def test_datum_ohne_doppelpunkt_am_kettenanfang():
    """Berghausbusch, Schl.-Nr. 00471, S. 84: '11. Dezember 1974 Berghausbusch. Jan Hendrich B…'"""
    s = parse_namenskette("11. Dezember 1974 Berghausbusch.")
    assert [x.name for x in s] == ["Berghausbusch"]
    assert s[0].hinweis == "Datum ohne Doppelpunkt"


def test_datum_ohne_doppelpunkt_nach_komma_in_der_kette():
    s = parse_namenskette("urspr.: Pottgasse, 07. Februar 1908 Kronenstraße.")
    assert [x.name for x in s] == ["Pottgasse", "Kronenstraße"]


def test_datum_ohne_doppelpunkt_tief_im_text_wird_ignoriert():
    """Ein Datum, dem ein Wort vorausgeht ('Am 25. Juli 1516 wurde …'), ist Prosa,
    kein Stadium — auch wenn kopf.rest es einmal enthalten sollte."""
    s = parse_namenskette("18. September 1926: St. Annental. Am 25. Juli 1516 Wurde")
    assert [x.name for x in s] == ["St. Annental"]


def test_datum_ohne_doppelpunkt_verlangt_grossgeschriebenen_namen():
    s = parse_namenskette("18. September 1926: St. Annental, 25. Juli 1516 wurde bei")
    assert [x.name for x in s] == ["St. Annental"]


def test_urspr_ohne_doppelpunkt():
    """Velberter Sträßchen 03203 (S. 330) 'urspr. Velberter Sträßchen.';
    Bocholder Straße 00379 (S. 72) 'urspr. Bocholder Landstraße, 30. April 1891: Hochstraße'."""
    s = parse_namenskette("urspr. Bocholder Landstraße, 30. April 1891: Hochstraße.")
    assert s[0].name == "Bocholder Landstraße"
    assert s[0].ist_urspruenglich is True
    assert s[0].hinweis == "urspr. ohne Doppelpunkt"
    assert s[1].name == "Hochstraße"


def test_jahrhundert_stadium():
    """Viehauser Berg, Schl.-Nr. 03213, S. 332."""
    s = parse_namenskette("16. Jahrh.: Viehauser Straße, 02. Juni 1922: Viehauser Berg.")
    assert (s[0].gueltig_ab, s[0].datum_praezision, s[0].name) == ("1501", "jahrhundert", "Viehauser Straße")


def test_numerisches_datum_stadium():
    s = parse_namenskette("29.08.1927: Schlenterstraße.")
    assert (s[0].gueltig_ab, s[0].name) == ("1927-08-29", "Schlenterstraße")


def test_bloss_jahr_hinter_rauschen_wird_nicht_als_stadium_gelesen():
    """Dudweilerstraße, Schl.-Nr. 00685, S. 104: Das Volldatum '14. November 1935'
    ist im OCR verstümmelt ('A 0, EEE' statt 'November'). Der Bloße-Jahr-Stempel
    '1935:', der aus dem Rauschen übrig bleibt, darf das verlorene Tag/Monat nicht
    stillschweigend zu einem gültigen Jahresdatum degradieren — precision-first:
    kein Stadium statt eines stillen Falsch-Datums."""
    s = parse_namenskette("14. November A 0, EEE 1935: Dudweilerstraße.")
    assert s == []


def test_bloss_jahr_in_der_kette_nach_komma_bleibt_gueltig():
    """'urspr.: Viehofer Chausee, 1908: Parkstraße.' — ein bloßes Jahr direkt nach
    einem Komma in der Kette (Positionsregel erfüllt) bleibt ein gültiges Stadium."""
    s = parse_namenskette("urspr.: Viehofer Chausee, 1908: Parkstraße.")
    assert [(x.gueltig_ab, x.name) for x in s] == [("", "Viehofer Chausee"), ("1908", "Parkstraße")]


def test_bloss_jahr_am_kettenanfang_bleibt_gueltig():
    s = parse_namenskette("1902: Barkhofstraße.")
    assert [(x.gueltig_ab, x.name) for x in s] == [("1902", "Barkhofstraße")]


def test_unverarbeiteter_rest_findet_verstuemmeltes_datum():
    """Am Thyssenhaus, Schl.-Nr. 00217, S. 44: '04. Februar 19377: Am Thyssenhaus.'
    — die verstümmelte Jahreszahl (5 statt 4 Ziffern) lässt keinen Stempel matchen;
    der Text bleibt unverarbeitet liegen, ohne dass irgendein Prüfgrund das anzeigt."""
    from strassen.namen import unverarbeiteter_rest
    rest = "22. Februar 1961: Am Rheinstahlhaus, 04. Februar 19377: Am Thyssenhaus."
    residue = unverarbeiteter_rest(rest)
    assert "19377" in residue


def test_unverarbeiteter_rest_ist_leer_bei_vollstaendig_gelesener_kette():
    """Kütings Garten, Schl.-Nr. 01838, S. 213 — vollständig gelesene Kette:
    kein unverarbeiteter Rest bleibt übrig."""
    from strassen.namen import unverarbeiteter_rest
    rest = ("18. November 1904: Kirchstraße, 01. Juni 1926: Klosterstraße, "
            "20. November 1937: Kütings Garten.")
    assert unverarbeiteter_rest(rest) == ""


@pytest.mark.parametrize("roh,soll", [
    ("Moltkestraße (tiw.)", "Moltkestraße (tlw.)"),
    ("Frohnhauser Straße (tIw.)", "Frohnhauser Straße (tlw.)"),
    ("Damannstraße (t!w.)", "Damannstraße (tlw.)"),
    ("Ahnewinkelstraße (Verl)", "Ahnewinkelstraße (Verl.)"),
    ("Kapitän-Lehmann-Höhe (Umb))", "Kapitän-Lehmann-Höhe (Umb.)"),
    ("Sonnenstraße {tlw.)", "Sonnenstraße (tlw.)"),
    ("Körholzstraße [neue Führung)", "Körholzstraße (neue Führung)"),
    ("Blockstraße (verl.)", "Blockstraße (Verl.)"),
    ("Altendorfer Straße (tlw. Umb.)", "Altendorfer Straße (tlw. Umb.)"),
])
def test_normalisiere_zusatz_bekannte_varianten_ohne_hinweis(roh, soll):
    assert normalisiere_zusatz(roh) == (soll, "")


def test_normalisiere_zusatz_ortsklammer_bleibt():
    assert normalisiere_zusatz("Bahnstraße (Essen)") == ("Bahnstraße (Essen)", "")


def test_normalisiere_zusatz_abgeschnitten_wird_ergaenzt_und_gekennzeichnet():
    assert normalisiere_zusatz("Thomaestraße (tiw") == ("Thomaestraße (tlw.)", HINWEIS_ZUSATZ_ERGAENZT)
    assert normalisiere_zusatz("Im Westerbruch (Verl") == ("Im Westerbruch (Verl.)", HINWEIS_ZUSATZ_ERGAENZT)


def test_normalisiere_zusatz_ohne_klammer_unveraendert():
    assert normalisiere_zusatz("Aachener Straße") == ("Aachener Straße", "")


def test_parse_namenskette_normalisiert_zusaetze():
    # Ahnewinkelstraße 00021, S. 23 (Prüfliste)
    st = parse_namenskette("vor 1898: Ahnewinkelstraße (Verl), 16. Mai 1902: Ahnewinkelstraße (tiw.)")
    assert [s.name for s in st] == ["Ahnewinkelstraße (Verl.)", "Ahnewinkelstraße (tlw.)"]
    assert all(s.hinweis == "" for s in st)


def test_parse_namenskette_abgeschnittener_zusatz_am_kettenende():
    st = parse_namenskette("29. März 1892: Thomaestraße (tiw")
    assert st[-1].name == "Thomaestraße (tlw.)"
    assert HINWEIS_ZUSATZ_ERGAENZT in st[-1].hinweis
