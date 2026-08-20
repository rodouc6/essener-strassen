from strassen.namen import parse_namenskette


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
    assert [x.name for x in s] == ["Taubenstraße", "Taubenstraße (Verl)", "Natorpstraße"]
    assert [x.gueltig_ab for x in s] == ["1889-07-05", "1925-09-19", "1971-03-17"]
    assert [x.datum_praezision for x in s] == ["tag", "tag", "tag"]
