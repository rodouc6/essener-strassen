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
