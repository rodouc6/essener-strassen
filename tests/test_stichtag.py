from strassen.stichtag import name_am_stichtag, baue_konkordanz, pruefe_konkordanz


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


# --- Fix-Runde 1 (Review Task 7) -------------------------------------------------

def test_baue_konkordanz_trennt_klammerzusatz_vom_namen():
    """Dickhoffs Klammerzusätze ('(tlw.)', '(Verl.)', OCR-Varianten wie '{tlw.)')
    gehören nicht in den Namen, den wir mit dem Adressbuch abgleichen — sie werden
    abgetrennt und landen in einer eigenen Spalte 'zusatz'."""
    strassen = [{"schl_nr": "00099", "lemma": "Hochstraße Neu", "stadtteile": "Rüttenscheid",
                 "buchseite": "1"}]
    namen = [{"schl_nr": "00099", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Hochstraße (tiw.)"},
             {"schl_nr": "00099", "stadium": "2", "gueltig_ab": "1950-01-01",
              "datum_praezision": "tag", "name": "Hochstraße Neu"}]
    k = baue_konkordanz(strassen, namen, "1936-06-30")
    assert k[0]["ehemalig"] == "Hochstraße"
    assert k[0]["zusatz"] == "(tiw.)"


def test_baue_konkordanz_laesst_nur_zusatz_unterschied_aus():
    """Unterscheidet sich das Stadium vom Lemma nur durch einen Klammerzusatz
    ('Aachener Straße (Verl.)' vs. Lemma 'Aachener Straße'), ist der Name nach
    Abtrennung des Zusatzes unverändert — das ist keine echte Umbenennung und
    braucht keinen Konkordanzeintrag."""
    strassen = [{"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausen",
                 "buchseite": "1"}]
    namen = [{"schl_nr": "00001", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Aachener Straße"},
             {"schl_nr": "00001", "stadium": "2", "gueltig_ab": "1909-03-05",
              "datum_praezision": "tag", "name": "Aachener Straße (Verl.)"}]
    assert baue_konkordanz(strassen, namen, "1936-06-30") == []


def test_baue_konkordanz_behaelt_informationstragenden_teil_zusatz():
    """Fix-Runde 2: '(tlw.)' ('teilweise') ist kein rein administrativer Zusatz wie
    '(Verl.)'/'(Umb.)', sondern sagt, dass nur ein Teil der Straße den historischen
    Namen trug — das ist Information, die beim bloßen 'unverändert'-Drop verloren
    ginge (Fund: schl_nr 00318 Beisenstraße, Katernberg, 1936 'Beisenstraße
    (tlw.)'). Die Zeile bleibt daher in der Konkordanz, mit ehemalig == heutig und
    gefülltem zusatz."""
    strassen = [{"schl_nr": "00318", "lemma": "Beisenstraße", "stadtteile": "Katernberg",
                 "buchseite": "1"}]
    namen = [{"schl_nr": "00318", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Beisenstraße"},
             {"schl_nr": "00318", "stadium": "2", "gueltig_ab": "1909-03-05",
              "datum_praezision": "tag", "name": "Beisenstraße (tlw.)"}]
    k = baue_konkordanz(strassen, namen, "1936-06-30")
    assert len(k) == 1
    assert k[0]["ehemalig"] == "Beisenstraße"
    assert k[0]["heutig"] == "Beisenstraße"
    assert k[0]["zusatz"] == "(tlw.)"


def test_baue_konkordanz_markiert_kollisionen_als_nicht_eindeutig():
    """Zwei Straßen im selben Stadtteil, die (nach Zusatz-Abtrennung) denselben
    historischen Namen tragen, sind für den Adressbuch-Abgleich nicht unterscheidbar
    — beide werden als 'eindeutig'='nein' markiert, ein dritter, kollisionsfreier
    Eintrag bleibt 'ja'."""
    strassen = [{"schl_nr": "00001", "lemma": "Straße Eins", "stadtteile": "Mitte", "buchseite": "1"},
                {"schl_nr": "00002", "lemma": "Straße Zwei", "stadtteile": "Mitte", "buchseite": "1"},
                {"schl_nr": "00003", "lemma": "Straße Drei", "stadtteile": "Mitte", "buchseite": "1"}]
    namen = [{"schl_nr": "00001", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Altname"},
             {"schl_nr": "00001", "stadium": "2", "gueltig_ab": "1950-01-01",
              "datum_praezision": "tag", "name": "Straße Eins"},
             {"schl_nr": "00002", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Altname"},
             {"schl_nr": "00002", "stadium": "2", "gueltig_ab": "1950-01-01",
              "datum_praezision": "tag", "name": "Straße Zwei"},
             {"schl_nr": "00003", "stadium": "1", "gueltig_ab": "1900-01-01",
              "datum_praezision": "tag", "name": "Einzigname"},
             {"schl_nr": "00003", "stadium": "2", "gueltig_ab": "1950-01-01",
              "datum_praezision": "tag", "name": "Straße Drei"}]
    k = baue_konkordanz(strassen, namen, "1936-06-30")
    kollisionen = [r for r in k if r["ehemalig"] == "Altname"]
    assert len(kollisionen) == 2
    assert all(r["eindeutig"] == "nein" for r in kollisionen)
    einzig = next(r for r in k if r["ehemalig"] == "Einzigname")
    assert einzig["eindeutig"] == "ja"


def test_baue_konkordanz_laesst_inkonsistente_namenskette_aus():
    """00286: einziges Stadium 'Marktplatz' (1900), Lemma aber 'Barbarossaplatz' —
    das mechanische Konsistenz-Netz (letztes Stadium ≠ Lemma) erkennt die
    unvollständige Kette und nimmt die Zeile NICHT in die Konkordanz auf."""
    strassen = [{"schl_nr": "00286", "lemma": "Barbarossaplatz", "stadtteile": "Stoppenberg",
                 "buchseite": "61"}]
    namen = [{"schl_nr": "00286", "stadium": "1", "gueltig_ab": "1900",
              "datum_praezision": "jahr", "name": "Marktplatz"}]
    assert baue_konkordanz(strassen, namen, "1936-06-30") == []


def test_pruefe_konkordanz_findet_inkonsistente_namenskette():
    """Derselbe 00286-Fall landet bei pruefe_konkordanz als Prüffall mit Begründung."""
    strassen = [{"schl_nr": "00286", "lemma": "Barbarossaplatz", "stadtteile": "Stoppenberg",
                 "buchseite": "61"}]
    namen = [{"schl_nr": "00286", "stadium": "1", "gueltig_ab": "1900",
              "datum_praezision": "jahr", "name": "Marktplatz"}]
    p = pruefe_konkordanz(strassen, namen, "1936-06-30")
    assert len(p) == 1
    assert p[0]["lemma"] == "Barbarossaplatz"
    assert p[0]["buchseite"] == "61"
    assert p[0]["grund"] == "Namenskette unvollständig (letztes Stadium ≠ Lemma)"
