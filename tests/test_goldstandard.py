import pytest

from strassen.goldstandard import (
    buchseite_zu_scan, formatiere_datum, ziehe_schichtung, baue_pruefzeilen,
    berechne_statistik, auswerten, scan_dateiname,
)


# --- Seitenumrechnung buchseite -> band/pdf_seite/haelfte ---

def test_buchseite_2_ist_erste_pdf_seite_band_1_links():
    assert buchseite_zu_scan(2) == (1, 1, "links")


def test_buchseite_3_ist_erste_pdf_seite_band_1_rechts():
    assert buchseite_zu_scan(3) == (1, 1, "rechts")


def test_buchseite_201_letzte_seite_band_1():
    # Band 1: Buchseiten 2..201 auf 100 Doppelseiten-Scans -> pdf_seite 1..100
    assert buchseite_zu_scan(201) == (1, 100, "rechts")


def test_buchseite_202_erste_seite_band_2():
    assert buchseite_zu_scan(202) == (2, 1, "links")


def test_buchseite_203_band_2_rechts():
    assert buchseite_zu_scan(203) == (2, 1, "rechts")


def test_buchseite_388_ist_letzte_pdf_seite_band_2():
    # Band 2: Buchseiten 202.. auf 94 Doppelseiten-Scans -> pdf_seite 1..94;
    # 388 ist gerade -> linke Buchseite der letzten Doppelseite.
    assert buchseite_zu_scan(388) == (2, 94, "links")


def test_buchseite_akzeptiert_string():
    assert buchseite_zu_scan("23") == buchseite_zu_scan(23)


# --- formatiere_datum ---

def test_formatiere_datum_tag():
    assert formatiere_datum("tag", "1904-11-18") == "1904-11-18"


def test_formatiere_datum_vor():
    assert formatiere_datum("vor", "1898") == "vor 1898"


def test_formatiere_datum_jahr():
    assert formatiere_datum("jahr", "1900") == "1900"


def test_formatiere_datum_unbekannt():
    assert formatiere_datum("unbekannt", "") == "(urspr., kein Datum)"


# --- Schichtung 40/10 ---

def _strassen(n_automatisch, n_unsicher):
    strassen = [{"schl_nr": f"{i:05d}", "lemma": f"Straße {i}", "buchseite": "10",
                 "status": "automatisch"} for i in range(n_automatisch)]
    strassen += [{"schl_nr": f"{1000+i:05d}", "lemma": f"Unsicher {i}",
                  "buchseite": "10", "status": "unsicher"}
                 for i in range(n_unsicher)]
    return strassen


def test_schichtung_liefert_40_automatisch_10_unsicher():
    strassen = _strassen(100, 50)
    gezogen = ziehe_schichtung(strassen)
    assert sum(1 for z in gezogen if z["status"] == "automatisch") == 40
    assert sum(1 for z in gezogen if z["status"] == "unsicher") == 10
    assert len(gezogen) == 50


def test_schichtung_ist_deterministisch():
    strassen = _strassen(100, 50)
    a = ziehe_schichtung(strassen)
    b = ziehe_schichtung(strassen)
    assert [z["schl_nr"] for z in a] == [z["schl_nr"] for z in b]


def test_schichtung_bricht_ab_wenn_zu_wenig_unsicher():
    strassen = _strassen(100, 5)
    with pytest.raises(ValueError):
        ziehe_schichtung(strassen)


def test_schichtung_bricht_ab_wenn_zu_wenig_automatisch():
    strassen = _strassen(10, 50)
    with pytest.raises(ValueError):
        ziehe_schichtung(strassen)


# --- baue_pruefzeilen ---

def test_pruefzeilen_enthalten_kopf_und_stadien_felder():
    eintrag = {"schl_nr": "00001", "lemma": "Aachener Straße", "buchseite": "23",
               "stadtteile": "Frohnhausen", "strassenklasse": "Gemeindestraße",
               "namensgruppe": "Stadt und Ort", "verweis_auf": "", "status": "automatisch"}
    stadien = [{"stadium": "1", "gueltig_ab": "1898", "datum_praezision": "vor",
                "name": "Victoriastraße", "ist_urspruenglich": "falsch"},
               {"stadium": "2", "gueltig_ab": "1902-05-16", "datum_praezision": "tag",
                "name": "Aachener Straße", "ist_urspruenglich": "falsch"}]
    zeilen = baue_pruefzeilen(eintrag, stadien)
    felder = [z["feld"] for z in zeilen]
    assert felder[:6] == ["schl_nr", "lemma", "stadtteile", "strassenklasse",
                          "namensgruppe", "verweis_auf"]
    assert "stadium_1_datum" in felder and "stadium_1_name" in felder
    assert "stadium_2_datum" in felder and "stadium_2_name" in felder
    wert_stadium_1_datum = next(z["wert"] for z in zeilen if z["feld"] == "stadium_1_datum")
    assert wert_stadium_1_datum == "vor 1898"
    # korrekt/korrektur leer, band/pdf_seite/haelfte aus buchseite abgeleitet
    for z in zeilen:
        assert z["korrekt"] == "" and z["korrektur"] == ""
        assert (z["band"], z["pdf_seite"], z["haelfte"]) == buchseite_zu_scan("23")


def test_scan_dateiname():
    assert scan_dateiname("00001", "23") == "schlnr_00001_s023.png"


# --- auswerten-Rechnung auf Mini-Fixture ---

def _zeile(feld, korrekt):
    return {"schl_nr": "1", "lemma": "X", "buchseite": "10", "band": "1",
            "pdf_seite": "1", "haelfte": "links", "feld": feld, "wert": "x",
            "korrekt": korrekt, "korrektur": ""}


def test_berechne_statistik_zaehlt_richtig():
    zeilen = [
        _zeile("lemma", "ja"), _zeile("lemma", "ja"), _zeile("lemma", "nein"),
        _zeile("stadium_1_datum", "ja"), _zeile("stadium_2_datum", "nein"),
        _zeile("schl_nr", ""),  # noch nicht geprüft -> ignoriert
    ]
    stat = berechne_statistik(zeilen)
    assert stat["zeilen_gesamt"] == 6
    assert stat["zeilen_ausgefuellt"] == 5
    assert stat["je_feldtyp"]["lemma"] == {"geprueft": 3, "korrekt": 2,
                                            "fehlerquote": pytest.approx(100 / 3)}
    # stadium_1_datum und stadium_2_datum werden als Feldtyp 'stadium_datum' zusammengefasst
    assert stat["je_feldtyp"]["stadium_datum"] == {"geprueft": 2, "korrekt": 1,
                                                     "fehlerquote": 50.0}
    assert stat["gesamt"]["geprueft"] == 5
    assert stat["gesamt"]["korrekt"] == 3
    assert stat["gesamt"]["fehlerquote"] == pytest.approx(40.0)


def test_auswerten_bricht_ab_wenn_zu_viel_offen(tmp_path):
    import csv
    pfad = tmp_path / "stichprobe.csv"
    felder = ["schl_nr", "lemma", "buchseite", "band", "pdf_seite", "haelfte",
              "feld", "wert", "korrekt", "korrektur"]
    zeilen = [_zeile("lemma", "ja")] + [_zeile("lemma", "") for _ in range(9)]
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder)
        w.writeheader()
        w.writerows(zeilen)
    with pytest.raises(SystemExit):
        auswerten(stichprobe_pfad=pfad, ergebnis_pfad=tmp_path / "ergebnis.md")


def test_auswerten_schreibt_ergebnis_md(tmp_path):
    import csv
    pfad = tmp_path / "stichprobe.csv"
    felder = ["schl_nr", "lemma", "buchseite", "band", "pdf_seite", "haelfte",
              "feld", "wert", "korrekt", "korrektur"]
    zeilen = [_zeile("lemma", "ja"), _zeile("lemma", "ja"), _zeile("lemma", "nein")]
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder)
        w.writeheader()
        w.writerows(zeilen)
    ziel = tmp_path / "ergebnis.md"
    bericht = auswerten(stichprobe_pfad=pfad, ergebnis_pfad=ziel)
    assert ziel.exists()
    assert "lemma" in bericht
    assert ziel.read_text(encoding="utf-8") == bericht
