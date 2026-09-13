import csv

from strassen import pruefbilder as pb

_Z = [{"schl_nr": "00021", "buchseite": "23", "feld": "stadium_3_name", "einig": "beide"},
      {"schl_nr": "00021", "buchseite": "23", "feld": "stadium_5_name", "einig": "beide"},
      {"schl_nr": "00013", "buchseite": "23", "feld": "stadium_1_name", "einig": "beide"},
      {"schl_nr": "00500", "buchseite": "86", "feld": "lemma", "einig": "eines"}]


def test_eintraege_aus_pruefliste_dedupliziert_und_filtert():
    e = pb.eintraege_aus_pruefliste(_Z)
    assert [(x["schl_nr"], x["buchseite"], x["felder"]) for x in e] == [
        ("00013", 23, ["stadium_1_name"]), ("00021", 23, ["stadium_3_name", "stadium_5_name"])]


def test_eintraege_aus_pruefliste_mit_eines():
    assert len(pb.eintraege_aus_pruefliste(_Z, einig=("beide", "eines"))) == 3


def test_formatiere_index_tabelle():
    md = pb.formatiere_index(pb.eintraege_aus_pruefliste(_Z))
    assert "| 00021 | 23 | stadium_3_name, stadium_5_name | schlnr_00021_s023.png |" in md


def test_erzeuge_rendert_je_eintrag_einmal(tmp_path):
    pfad = tmp_path / "pruefung_llm.csv"
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["schl_nr", "buchseite", "feld", "einig"]); w.writeheader(); w.writerows(_Z)
    aufrufe = []
    def render(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi):
        aufrufe.append(ziel_png.name); ziel_png.write_bytes(b"png")
    n = pb.erzeuge(pfad, tmp_path / "bilder", "/quelle", ("beide",), render)
    assert n == 2 and sorted(aufrufe) == ["schlnr_00013_s023.png", "schlnr_00021_s023.png"]
    assert (tmp_path / "bilder" / "index.md").exists()
    assert pb.erzeuge(pfad, tmp_path / "bilder", "/quelle", ("beide",), render) == 0   # idempotent
