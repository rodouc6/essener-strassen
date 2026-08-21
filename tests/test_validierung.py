from strassen.validierung import (pruefe_schluesselnummern, pruefe_alphabet,
                              pruefe_gegen_amtlich)


def test_luecken_und_dubletten_werden_gefunden():
    strassen = [{"schl_nr": "00001"}, {"schl_nr": "00002"}, {"schl_nr": "00004"},
                {"schl_nr": "00004"}]
    e = pruefe_schluesselnummern(strassen)
    assert 3 in e["luecken"]
    assert "00004" in e["dubletten"]


def test_lemma_ausserhalb_der_sortierung_faellt_auf():
    """Ein OCR-verstümmeltes Lemma bricht die alphabetische Ordnung des Lexikons."""
    strassen = [{"schl_nr": "1", "lemma": "Kronenstraße"},
                {"schl_nr": "2", "lemma": "Aaaafalsch"},
                {"schl_nr": "3", "lemma": "Kruppstraße"}]
    auffaellig = pruefe_alphabet(strassen)
    assert any(x["lemma"] == "Aaaafalsch" for x in auffaellig)


def test_abgleich_mit_amtlichem_verzeichnis():
    strassen = [{"lemma": "Kruppstraße"}, {"lemma": "Kriippstraße"}]
    e = pruefe_gegen_amtlich(strassen, {"kruppstraße"})
    assert e["bestaetigt"] == 1
    assert "Kriippstraße" in e["unbekannt"]


def test_umlaut_wird_woerterbuchueblich_einsortiert():
    """ü wird zu 'ue' expandiert (nicht nur Diakritika gestrichen) — sonst wird
    z. B. 'Am Luftschacht' fälschlich als Ausreißer zwischen 'Am Lünink' und
    'Am Markuskreuz' gemeldet (Task-6-Selbstdurchsicht-Fund, echte Buchreihenfolge:
    Lünink vor Luftschacht vor Markuskreuz — mit ü→ue korrekt sortiert)."""
    strassen = [{"schl_nr": "1", "lemma": "Am Lindenbruch"},
                {"schl_nr": "2", "lemma": "Am Lünink"},
                {"schl_nr": "3", "lemma": "Am Luftschacht"},
                {"schl_nr": "4", "lemma": "Am Markuskreuz"}]
    auffaellig = pruefe_alphabet(strassen)
    assert not any(x["lemma"] == "Am Luftschacht" for x in auffaellig)
