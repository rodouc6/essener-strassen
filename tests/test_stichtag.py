from strassen.stichtag import name_am_stichtag, baue_konkordanz


def test_name_am_stichtag_waehlt_das_gueltige_stadium():
    """Kütings Garten hieß 1936 'Klosterstraße' — die Umbenennung kam 1937."""
    stadien = [{"gueltig_ab": "1904-11-18", "datum_praezision": "tag", "name": "Kirchstraße"},
               {"gueltig_ab": "1926-06-01", "datum_praezision": "tag", "name": "Klosterstraße"},
               {"gueltig_ab": "1937-11-20", "datum_praezision": "tag", "name": "Kütings Garten"}]
    assert name_am_stichtag(stadien, "1936-06-30")["name"] == "Klosterstraße"


def test_stichtag_vor_erstem_stadium_ergibt_nichts():
    stadien = [{"gueltig_ab": "1955-03-31", "datum_praezision": "tag", "name": "Am Schroer"}]
    assert name_am_stichtag(stadien, "1936-06-30") is None


def test_unsichere_datierung_wird_gekennzeichnet_nicht_geraten():
    stadien = [{"gueltig_ab": "", "datum_praezision": "unbekannt", "name": "Pottgasse"},
               {"gueltig_ab": "1908-02-07", "datum_praezision": "tag", "name": "Kronenstraße"}]
    treffer = name_am_stichtag(stadien, "1936-06-30")
    assert treffer["name"] == "Kronenstraße"


def test_konkordanz_verknuepft_historischen_mit_heutigem_namen():
    strassen = [{"schl_nr": "01838", "lemma": "Kütings Garten", "stadtteile": "Freisenbruch"}]
    namen = [{"schl_nr": "01838", "stadium": "2", "gueltig_ab": "1926-06-01",
              "datum_praezision": "tag", "name": "Klosterstraße"},
             {"schl_nr": "01838", "stadium": "3", "gueltig_ab": "1937-11-20",
              "datum_praezision": "tag", "name": "Kütings Garten"}]
    k = baue_konkordanz(strassen, namen, "1936-06-30")
    assert k[0]["ehemalig"] == "Klosterstraße"
    assert k[0]["heutig"] == "Kütings Garten"
    assert k[0]["stadtteil"] == "Freisenbruch"
