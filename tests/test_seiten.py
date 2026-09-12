from pathlib import Path

from strassen import seiten


def test_seiten_dateiname_dreistellig():
    assert seiten.seiten_dateiname(23) == "s023.png"
    assert seiten.seiten_dateiname("7") == "s007.png"


def test_parse_seitenbereich_bereich_und_liste():
    assert seiten.parse_seitenbereich("23-25") == [23, 24, 25]
    assert seiten.parse_seitenbereich("23,45") == [23, 45]
    assert seiten.parse_seitenbereich("23-24,45") == [23, 24, 45]


def test_parse_seitenbereich_ohne_angabe_alle_buchseiten():
    alle = seiten.parse_seitenbereich(None)
    assert alle[0] == 2 and alle[-1] == 388 and len(alle) == 387


def test_rendere_seiten_ueberspringt_vorhandene_und_reicht_dpi_durch(tmp_path):
    aufrufe = []

    def render(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi):
        aufrufe.append((band, pdf_seite, haelfte, ziel_png.name, dpi))
        Path(ziel_png).write_bytes(b"png")

    (tmp_path / "s023.png").write_bytes(b"alt")
    neu = seiten.rendere_seiten([23, 24], tmp_path, "/quelle", dpi=300, render=render)
    assert [p.name for p in neu] == ["s024.png"]
    assert aufrufe == [(1, 12, "links", "s024.png", 300)]
