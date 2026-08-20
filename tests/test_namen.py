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
