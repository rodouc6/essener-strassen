# Essener Straßenverzeichnis — Parser und Validierung: Implementierungsplan

> **Für agentische Bearbeiter:** ERFORDERLICHE SUB-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, um diesen Plan Aufgabe für Aufgabe umzusetzen. Die Schritte nutzen Checkbox-Syntax (`- [ ]`) zur Nachverfolgung.

**Ziel:** Aus 388 OCR-Buchseiten von Dickhoff, *Essener Straßen* (2015) einen validierten, publizierbaren Datensatz aller Essener Straßen mit datierter Namensgeschichte erzeugen.

**Architektur:** Eine Kette kleiner, einzeln testbarer Module: Textaufbereitung → Segmentierung → Kopf-Parser → Namenskette → CSV-Ausgabe → Validierung → Ableitung. Jede Stufe schreibt ihr Ergebnis als Datei, damit Zwischenstände prüfbar bleiben. Was nicht sicher erkannt wird, geht nach `pruefung.csv` statt geraten zu werden.

**Tech Stack:** Python 3.12, ausschließlich Standardbibliothek (`re`, `csv`, `pathlib`, `unicodedata`), pytest für Tests. Bewusst ohne externe Abhängigkeiten — der Code ist Teil der Veröffentlichung und soll ohne Installationshürde nachvollziehbar sein.

**Spec:** `docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md`

## Globale Randbedingungen

- **Precision-first:** Nichts wird geraten. Unsichere Angaben gehen nach `pruefung.csv` oder werden im Feld `datum_praezision` gekennzeichnet.
- **Keine Erläuterungstexte in den Ausgabedateien.** `strassen.csv`, `namen.csv` und `konkordanz_1936.csv` enthalten ausschließlich Fakten. Der Fließtext bleibt in `ocr/` (gitignored).
- **Deutschsprachige Bezeichner** in Code und Daten, passend zur Quelle und zu den übrigen Projekten des Nutzers.
- **Keine externen Abhängigkeiten** außer pytest (nur für Tests).
- **Alle Ausgabedateien UTF-8, Komma-getrennt, mit Kopfzeile.**
- **Quelle der Wahrheit für Testdaten:** echte OCR-Ausschnitte aus `ocr/seiten/`, keine erfundenen Beispiele.

## Bekannte Kennzahlen des Ausgangsmaterials

Diese Zahlen stammen aus der Analyse des fertigen OCR-Laufs und dienen als Sollwerte:

| Größe | Wert |
|---|--:|
| Buchseiten (Dateien `ocr/seiten/sNNN.txt`) | 388 |
| Einträge mit sauberem Anker `Schl.-Nr.:` | 3.218 |
| Einträge mit verstümmeltem Anker (`Scht.-`, `Sch!.-`, `Schi.-`, `Schl-`, `Schtl.-`, `Sch.-`) | 122 |
| **Einträge gesamt (erwartet)** | **3.340** |
| Schlüsselnummern-Bereich | 1–3771 |
| Zerrissene Marker `Str.-` / `Kl.:` | 661 |
| Zerrissene Marker `Str.-` / `Gr.:` | 55 |
| Zerrissene Marker `Stadt-` / `teil` | 9 |
| Kolumnentitel „Essener Straßen" zu entfernen | 349 |

---

### Task 1: Projektgerüst und Textaufbereitung

Die Rohseiten enthalten Kolumnentitel, Seitenzahlen, Silbentrennung und über Zeilenumbrüche zerrissene Feldmarker. Diese Stufe stellt daraus fortlaufenden Text her — **ohne** die Feldmarker zu zerstören.

**Files:**
- Create: `strassen/aufbereitung.py`
- Create: `tests/test_aufbereitung.py`
- Create: `pyproject.toml`

**Interfaces:**
- Produces: `lade_seiten(verzeichnis) -> list[tuple[int, str]]` — (Buchseite, Rohtext), nach Seitenzahl sortiert
- Produces: `bereinige(text: str) -> str` — Kolumnentitel und Seitenzahlen entfernt
- Produces: `verbinde_zeilen(text: str) -> str` — Marker gerettet, Silbentrennung aufgelöst, eine Zeile
- Produces: `aufbereiten(verzeichnis) -> list[tuple[int, str]]` — (Buchseite, aufbereiteter Text)

- [ ] **Schritt 1: Test schreiben, der die Rettung der Feldmarker erzwingt**

```python
# tests/test_aufbereitung.py
from strassen.aufbereitung import verbinde_zeilen, bereinige


def test_zerrissener_marker_bleibt_erhalten():
    """Str.-\\nKl.: darf nicht zu 'Str.Kl.:' entstellt werden — der Bindestrich
    gehört zum Marker, er ist kein Silbentrennstrich (661 Fälle im Material)."""
    roh = "Am Schroer: Schl.-Nr.: 00127, Stadtteil Byfang, Str.-\nKl.: Gemeindestraße"
    assert "Str.-Kl.:" in verbinde_zeilen(roh)


def test_echte_silbentrennung_wird_aufgeloest():
    roh = "Admiral-Scheer-Straße: Schl.-Nr.: 00012, Stadtteil Süd-\nviertel, Str.-Kl.:"
    assert "Südviertel" in verbinde_zeilen(roh)


def test_bindestrich_im_namen_bleibt():
    """Ein Trennstrich vor Großbuchstabe ist Namensbestandteil, keine Silbentrennung."""
    roh = "Franz-Arens-Straße: Schl.-Nr.: 00947"
    assert "Franz-Arens-Straße" in verbinde_zeilen(roh)


def test_kolumnentitel_und_seitenzahl_entfernt():
    roh = "Essener Straßen\n\nKruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken\n\n211\n"
    sauber = bereinige(roh)
    assert "Essener Straßen" not in sauber
    assert "\n211" not in sauber
    assert "Kruselbeek" in sauber
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_aufbereitung.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.aufbereitung'`

- [ ] **Schritt 3: Minimale Implementierung**

```python
# strassen/aufbereitung.py
"""Rohe OCR-Seiten zu fortlaufendem, parsebarem Text aufbereiten.

Reihenfolge ist wesentlich: Erst die über Zeilenumbrüche zerrissenen Feldmarker
zusammenziehen, dann die echte Silbentrennung auflösen. Umgekehrt zerstörte die
Silbentrennungsregel die Marker ('Str.-\\nKl.:' würde zu 'Str.Kl.:').
"""
import re
from pathlib import Path

# Feldmarker, die im Satz über die Zeile brechen (661 + 55 + 9 Fälle im Material)
_MARKER = [
    (re.compile(r"(Str)\.-\s*\n\s*(Kl)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Str)\.-\s*\n\s*(Gr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Schl)\.-\s*\n\s*(Nr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"Stadt-\s*\n\s*teil"), "Stadtteil"),
]
_KOLUMNENTITEL = re.compile(r"^\s*Essener Straßen\s*$", re.MULTILINE)
_SEITENZAHL = re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE)
# Silbentrennung: Trennstrich am Zeilenende vor Kleinbuchstabe.
# Vor Großbuchstabe ist der Strich Namensbestandteil (Franz-Arens-Straße).
_TRENNUNG = re.compile(r"-\n(?=[a-zäöüß])")


def bereinige(text: str) -> str:
    text = _KOLUMNENTITEL.sub("", text)
    return _SEITENZAHL.sub("", text)


def verbinde_zeilen(text: str) -> str:
    for muster, ersatz in _MARKER:
        text = muster.sub(ersatz, text)
    text = _TRENNUNG.sub("", text)
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def lade_seiten(verzeichnis) -> list:
    seiten = []
    for pfad in sorted(Path(verzeichnis).glob("s*.txt")):
        nummer = int(pfad.stem.lstrip("s"))
        seiten.append((nummer, pfad.read_text(encoding="utf-8", errors="replace")))
    return seiten


def aufbereiten(verzeichnis) -> list:
    return [(nr, verbinde_zeilen(bereinige(roh))) for nr, roh in lade_seiten(verzeichnis)]
```

```toml
# pyproject.toml
[project]
name = "essener-strassen"
version = "0.1.0"
description = "Straßenverzeichnis Essen aus Dickhoff 2015 als Forschungsdatensatz"
requires-python = ">=3.12"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Schritt 4: Tests laufen lassen, Erfolg bestätigen**

Run: `python3 -m pytest tests/test_aufbereitung.py -v`
Erwartet: 4 passed

- [ ] **Schritt 5: Gegen das echte Material prüfen**

Run:
```bash
python3 -c "
from strassen.aufbereitung import aufbereiten
s = aufbereiten('ocr/seiten')
print('Seiten:', len(s))
t = ' '.join(x[1] for x in s)
print('Str.-Kl.:', t.count('Str.-Kl.:'))
print('Kolumnentitel-Reste:', t.count('Essener Straßen'))
"
```
Erwartet: `Seiten: 388`, `Str.-Kl.: 3142` (±20), `Kolumnentitel-Reste: 0`

- [ ] **Schritt 6: Committen**

```bash
git add strassen/aufbereitung.py tests/test_aufbereitung.py pyproject.toml
git commit -m "Textaufbereitung: Marker retten, Silbentrennung auflösen, Kolumnentitel entfernen"
```

---

### Task 2: Einträge segmentieren

Aus dem fortlaufenden Text die einzelnen Straßeneinträge schneiden — mit tolerantem Anker, damit die 122 OCR-verstümmelten Fälle nicht verlorengehen, und mit Buchseiten-Beleg.

**Files:**
- Create: `strassen/segmentierung.py`
- Create: `tests/test_segmentierung.py`

**Interfaces:**
- Consumes: `aufbereitung.aufbereiten(verzeichnis) -> list[tuple[int, str]]`
- Produces: `ANKER: re.Pattern` — tolerantes Muster für „Schl.-Nr.:"
- Produces: `Eintrag` — NamedTuple mit Feldern `lemma_roh: str`, `rumpf: str`, `buchseite: int`
- Produces: `segmentiere(seiten: list[tuple[int, str]]) -> list[Eintrag]`

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_segmentierung.py
from strassen.segmentierung import segmentiere, ANKER


def test_verstuemmelter_anker_wird_erkannt():
    """'Sch!.-Nr.:' kam im echten OCR vor (Kütings Garten, S. 211).
    122 der 3340 Einträge tragen einen entstellten Anker."""
    for variante in ["Schl.-Nr.:", "Sch!.-Nr.:", "Scht.-Nr.:", "Schi.-Nr.:",
                     "Schl-Nr.:", "Schl.-Nr:", "Sch.-Nr.:", "Schtl.-Nr.:"]:
        assert ANKER.search(f"Beispielstraße: {variante} 01234"), variante


def test_eintrag_traegt_lemma_und_buchseite():
    seiten = [(211, "Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken, "
                    "Str.-Kl.: Gemeindestraße. Erläuterung. "
                    "Kuckucksrain: Schl.-Nr.: 01828, Stadtteile Rellinghausen und Stadtwald.")]
    eintraege = segmentiere(seiten)
    assert len(eintraege) == 2
    assert eintraege[0].lemma_roh == "Kruselbeek"
    assert eintraege[0].buchseite == 211
    assert eintraege[1].lemma_roh == "Kuckucksrain"


def test_eintrag_ueber_seitengrenze_behaelt_startseite():
    """Ein Eintrag am Seitenende läuft auf der Folgeseite weiter; belegt wird
    die Seite, auf der er beginnt."""
    seiten = [(210, "Kruppstraße: Schl.-Nr.: 01826, Stadtteile Holsterhausen und Südviertel, "
                    "Str.-Kl.: Kreisstraße, Gemeindestraße, Str.-Gr.: Familienname, "
                    "16. Mai 1902: Kruppstraße. Siehe"),
              (211, "Kruppallee. Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "Kruppstraße"
    assert eintraege[0].buchseite == 210
    assert "Kruppallee" in eintraege[0].rumpf
    assert eintraege[1].buchseite == 211
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_segmentierung.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.segmentierung'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/segmentierung.py
"""Fortlaufenden Text in einzelne Straßeneinträge schneiden.

Der Anker ist die Schlüsselnummer-Angabe. Sie wird tolerant erkannt, weil das OCR
sie in 122 von 3340 Fällen entstellt ('Sch!.-Nr.:', 'Scht.-Nr.:', 'Schi.-Nr.:').
Das Lemma steht unmittelbar davor, abgetrennt durch einen Doppelpunkt.
"""
import re
from typing import NamedTuple

# Sch + bis zu drei fehlgelesene Zeichen + optionaler Punkt/Bindestrich + Nr + Doppelpunkt
ANKER = re.compile(r"Sch[a-zA-Z!|]{0,3}\.?\s*-?\s*Nr\.?\s*:")
# Lemma: das Stichwort vor dem Anker, bis zum trennenden Doppelpunkt.
_LEMMA = re.compile(r"([^.;:]{2,60}?)\s*:\s*$")


class Eintrag(NamedTuple):
    lemma_roh: str
    rumpf: str
    buchseite: int


def segmentiere(seiten) -> list:
    # Seiten aneinanderhängen und merken, wo jede beginnt, um den Beleg zu bestimmen.
    text_teile, grenzen, position = [], [], 0
    for nummer, text in seiten:
        grenzen.append((position, nummer))
        text_teile.append(text)
        position += len(text) + 1
    volltext = " ".join(text_teile)

    def buchseite_von(offset: int) -> int:
        seite = grenzen[0][1]
        for start, nummer in grenzen:
            if start <= offset:
                seite = nummer
            else:
                break
        return seite

    treffer = list(ANKER.finditer(volltext))
    eintraege = []
    for i, m in enumerate(treffer):
        vorlauf = volltext[max(0, m.start() - 70):m.start()]
        lemma_treffer = _LEMMA.search(vorlauf)
        if not lemma_treffer:
            continue
        lemma = lemma_treffer.group(1).strip()
        start_lemma = m.start() - (len(vorlauf) - lemma_treffer.start(1))
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(volltext)
        # Rumpf endet vor dem Lemma des nächsten Eintrags.
        rumpf = volltext[m.end():ende]
        naechstes_lemma = _LEMMA.search(volltext[max(0, ende - 70):ende])
        if naechstes_lemma:
            rumpf = rumpf[:len(rumpf) - (70 - naechstes_lemma.start(1)) if ende >= 70 else len(rumpf)]
        eintraege.append(Eintrag(lemma_roh=lemma, rumpf=rumpf.strip(),
                                 buchseite=buchseite_von(start_lemma)))
    return eintraege
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_segmentierung.py -v`
Erwartet: 3 passed

- [ ] **Schritt 5: Gegen das echte Material prüfen**

Run:
```bash
python3 -c "
from strassen.aufbereitung import aufbereiten
from strassen.segmentierung import segmentiere
e = segmentiere(aufbereiten('ocr/seiten'))
print('Einträge:', len(e))
print('Seiten belegt von', min(x.buchseite for x in e), 'bis', max(x.buchseite for x in e))
"
```
Erwartet: `Einträge: 3340` (±30 — Abweichungen sind Kandidaten für `pruefung.csv`, kein Fehler), Seiten etwa 20–385.

- [ ] **Schritt 6: Committen**

```bash
git add strassen/segmentierung.py tests/test_segmentierung.py
git commit -m "Segmentierung: Einträge mit tolerantem Anker schneiden, Buchseite belegen"
```

---

### Task 3: Eintragskopf parsen

Aus dem Rumpf die Strukturfelder lesen: Schlüsselnummer, Stadtteile, Straßenklasse, Namensgruppe. Der Kopf endet, wo der Erläuterungstext beginnt — diese Grenze ist die eigentliche Schwierigkeit.

**Files:**
- Create: `strassen/kopf.py`
- Create: `tests/test_kopf.py`

**Interfaces:**
- Consumes: `segmentierung.Eintrag`
- Produces: `Kopf` — NamedTuple mit `schl_nr: str`, `stadtteile: list[str]`, `strassenklassen: list[str]`, `namensgruppe: str`, `rest: str`
- Produces: `parse_kopf(rumpf: str) -> Kopf | None` — `None`, wenn keine Schlüsselnummer lesbar ist

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_kopf.py
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_kopf.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.kopf'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/kopf.py
"""Strukturfelder aus dem Eintragskopf lesen.

Der Kopf ist eine Kette kommagetrennter Felder; der Erläuterungstext beginnt nach
dem letzten Datum-Name-Paar. Die Abgrenzung erfolgt über die Feldmuster selbst:
Was keinem Muster mehr entspricht, ist Fließtext.
"""
import re
from typing import NamedTuple

_NUMMER = re.compile(r"^\s*(\d{1,5})\b")
_STADTTEIL = re.compile(r"Stadtteile?\s+([^,;]+?)(?=,|\s+Str\.-|$)")
_KLASSE = re.compile(r"Str\.-Kl\.:\s*(.+?)(?=,?\s*Str\.-Gr\.:|$)")
_GRUPPE = re.compile(r"Str\.-Gr\.:\s*(.+?)(?=,\s*(?:urspr\.:|\d{1,2}\.\s*\w+\s+\d{4}:)|\.\s|$)")
# Kopfende: der Punkt nach dem letzten „Datum: Name"-Paar bzw. nach der Namensgruppe.
_LETZTES_STADIUM = re.compile(r"\d{1,2}\.\s*\w+\s+\d{4}\s*:\s*[^.]{1,80}?\.")


class Kopf(NamedTuple):
    schl_nr: str
    stadtteile: list
    strassenklassen: list
    namensgruppe: str
    rest: str


def _teile(wert: str) -> list:
    wert = re.sub(r"\s+und\s+", ", ", wert)
    return [t.strip() for t in wert.split(",") if t.strip()]


def parse_kopf(rumpf: str):
    m = _NUMMER.match(rumpf)
    if not m:
        return None
    schl_nr = m.group(1).zfill(5)

    stadtteile = []
    ms = _STADTTEIL.search(rumpf)
    if ms:
        stadtteile = _teile(ms.group(1))

    klassen = []
    mk = _KLASSE.search(rumpf)
    if mk:
        klassen = _teile(mk.group(1))

    gruppe = ""
    mg = _GRUPPE.search(rumpf)
    if mg:
        gruppe = mg.group(1).strip().rstrip(",")

    # Rest = ab der Namensgruppe bis zum Ende des letzten Namensstadiums.
    start = mg.end() if mg else (mk.end() if mk else m.end())
    schwanz = rumpf[start:]
    stadien = list(_LETZTES_STADIUM.finditer(schwanz))
    rest = schwanz[:stadien[-1].end()] if stadien else schwanz.split(". ")[0]
    return Kopf(schl_nr=schl_nr, stadtteile=stadtteile, strassenklassen=klassen,
                namensgruppe=gruppe, rest=rest.strip())
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_kopf.py -v`
Erwartet: 4 passed

- [ ] **Schritt 5: Trefferquote am echten Material messen**

Run:
```bash
python3 -c "
from strassen.aufbereitung import aufbereiten
from strassen.segmentierung import segmentiere
from strassen.kopf import parse_kopf
e = segmentiere(aufbereiten('ocr/seiten'))
k = [parse_kopf(x.rumpf) for x in e]
ok = [x for x in k if x]
print('Einträge:', len(e), '| Kopf gelesen:', len(ok))
print('mit Stadtteil:', sum(1 for x in ok if x.stadtteile))
print('mit Klasse:  ', sum(1 for x in ok if x.strassenklassen))
print('mit Gruppe:  ', sum(1 for x in ok if x.namensgruppe))
"
```
Erwartet: Kopf gelesen ≥ 3.250; mit Stadtteil ≥ 3.300; mit Klasse ≈ 3.100; mit Gruppe ≈ 3.200. Wer darunter liegt, geht später nach `pruefung.csv`.

- [ ] **Schritt 6: Committen**

```bash
git add strassen/kopf.py tests/test_kopf.py
git commit -m "Kopf-Parser: Schlüsselnummer, Stadtteile, Straßenklassen, Namensgruppe"
```

---

### Task 4: Namenskette mit Datierung

Das Herzstück: die Folge der Namensstadien mit Datum und ausgewiesener Genauigkeit.

**Files:**
- Create: `strassen/namen.py`
- Create: `tests/test_namen.py`

**Interfaces:**
- Consumes: `kopf.Kopf.rest`
- Produces: `Stadium` — NamedTuple mit `stadium: int`, `gueltig_ab: str`, `datum_praezision: str`, `name: str`, `ist_urspruenglich: bool`
- Produces: `parse_namenskette(rest: str) -> list[Stadium]`
- Produces: `MONATE: dict[str, int]`

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_namen.py
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_namen.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.namen'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/namen.py
"""Namensstadien mit Datum aus dem Kopfrest lesen.

Jedes Stadium ist ein Datum-Name-Paar. Fehlt das Datum ('urspr.:'), wird das
im Feld datum_praezision ausgewiesen — nicht geschätzt.
"""
import re
from typing import NamedTuple

MONATE = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
          "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11,
          "Dezember": 12}

_TAG = re.compile(r"(\d{1,2})\.\s*(" + "|".join(MONATE) + r")\s+(\d{4})\s*:\s*([^,.;]{1,80})")
_JAHR = re.compile(r"(?<![\d.])(\d{4})\s*:\s*([^,.;]{1,80})")
_URSPR = re.compile(r"urspr\.:\s*([^,.;]{1,80})")


class Stadium(NamedTuple):
    stadium: int
    gueltig_ab: str
    datum_praezision: str
    name: str
    ist_urspruenglich: bool


def parse_namenskette(rest: str) -> list:
    roh = []
    mu = _URSPR.search(rest)
    if mu:
        roh.append((-1, "", "unbekannt", mu.group(1).strip(), True))
    belegt = []
    for m in _TAG.finditer(rest):
        tag, monat, jahr = int(m.group(1)), MONATE[m.group(2)], int(m.group(3))
        roh.append((m.start(), f"{jahr:04d}-{monat:02d}-{tag:02d}", "tag",
                    m.group(4).strip(), False))
        belegt.append((m.start(), m.end()))
    for m in _JAHR.finditer(rest):
        if any(a <= m.start() < b for a, b in belegt):
            continue
        roh.append((m.start(), m.group(1), "jahr", m.group(2).strip(), False))
    roh.sort(key=lambda x: x[0])
    return [Stadium(stadium=i, gueltig_ab=g, datum_praezision=p, name=n,
                    ist_urspruenglich=u)
            for i, (_, g, p, n, u) in enumerate(roh, 1)]
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_namen.py -v`
Erwartet: 4 passed

- [ ] **Schritt 5: Committen**

```bash
git add strassen/namen.py tests/test_namen.py
git commit -m "Namenskette: datierte Stadien mit ausgewiesener Datumsgenauigkeit"
```

---

### Task 5: CSV-Ausgabe

Die drei Ausgabedateien schreiben — ohne jeden Erläuterungstext.

**Files:**
- Create: `strassen/ausgabe.py`
- Create: `strassen/erschliessen.py`
- Create: `tests/test_ausgabe.py`

**Interfaces:**
- Consumes: `segmentierung.Eintrag`, `kopf.parse_kopf`, `namen.parse_namenskette`
- Produces: `schreibe_strassen(zeilen: list[dict], pfad)`
- Produces: `schreibe_namen(zeilen: list[dict], pfad)`
- Produces: `schreibe_pruefung(zeilen: list[dict], pfad)`
- Produces: `erschliessen.main(ocr_dir, ausgabe_dir) -> dict` — Kennzahlen des Laufs

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_ausgabe.py
import csv
from strassen.ausgabe import schreibe_strassen, schreibe_namen, FELDER_STRASSEN


def test_strassen_csv_hat_festgelegte_spalten(tmp_path):
    p = tmp_path / "strassen.csv"
    schreibe_strassen([{"schl_nr": "01838", "lemma": "Kütings Garten",
                        "stadtteile": "Freisenbruch", "strassenklasse": "Gemeindestraße",
                        "namensgruppe": "Lagebezeichnung", "verweis_auf": "",
                        "buchseite": 211, "status": "automatisch"}], p)
    with open(p, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert list(zeilen[0].keys()) == FELDER_STRASSEN
    assert zeilen[0]["lemma"] == "Kütings Garten"


def test_keine_erlaeuterungstexte_in_der_ausgabe(tmp_path):
    """Rechtliche Zusage der Spec: nur Fakten werden veröffentlicht."""
    p = tmp_path / "strassen.csv"
    schreibe_strassen([{"schl_nr": "01818", "lemma": "Kronenstraße",
                        "stadtteile": "Stadtkern", "strassenklasse": "Gemeindestraße",
                        "namensgruppe": "Essener Geschichte", "verweis_auf": "",
                        "buchseite": 210, "status": "automatisch"}], p)
    inhalt = p.read_text(encoding="utf-8")
    assert "Gasthaus" not in inhalt and "Chronik" not in inhalt
    assert len(inhalt.splitlines()) == 2


def test_namen_csv_verknuepft_ueber_schluesselnummer(tmp_path):
    p = tmp_path / "namen.csv"
    schreibe_namen([{"schl_nr": "01838", "stadium": 2, "gueltig_ab": "1926-06-01",
                     "datum_praezision": "tag", "name": "Klosterstraße",
                     "ist_urspruenglich": "falsch"}], p)
    with open(p, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f))
    assert zeilen[0]["schl_nr"] == "01838"
    assert zeilen[0]["name"] == "Klosterstraße"
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_ausgabe.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.ausgabe'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/ausgabe.py
"""CSV-Ausgaben des Datensatzes. Enthält ausschließlich Fakten, keine Fließtexte."""
import csv
from pathlib import Path

FELDER_STRASSEN = ["schl_nr", "lemma", "stadtteile", "strassenklasse",
                   "namensgruppe", "verweis_auf", "buchseite", "status"]
FELDER_NAMEN = ["schl_nr", "stadium", "gueltig_ab", "datum_praezision",
                "name", "ist_urspruenglich"]
FELDER_PRUEFUNG = ["buchseite", "lemma_roh", "grund", "rohtext"]


def _schreibe(zeilen, pfad, felder):
    with open(Path(pfad), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def schreibe_strassen(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_STRASSEN)


def schreibe_namen(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_NAMEN)


def schreibe_pruefung(zeilen, pfad):
    _schreibe(zeilen, pfad, FELDER_PRUEFUNG)
```

```python
# strassen/erschliessen.py
"""Gesamtlauf: OCR-Seiten → strassen.csv, namen.csv, pruefung.csv."""
import re
import sys
from pathlib import Path

from strassen.aufbereitung import aufbereiten
from strassen.segmentierung import segmentiere
from strassen.kopf import parse_kopf
from strassen.namen import parse_namenskette
from strassen.ausgabe import schreibe_strassen, schreibe_namen, schreibe_pruefung

_VERWEIS = re.compile(r"Siehe\s+([A-ZÄÖÜ][^.,;]{2,60})")


def main(ocr_dir="ocr/seiten", ausgabe_dir="daten"):
    ziel = Path(ausgabe_dir)
    ziel.mkdir(parents=True, exist_ok=True)
    eintraege = segmentiere(aufbereiten(ocr_dir))

    strassen, namen, pruefung = [], [], []
    for e in eintraege:
        k = parse_kopf(e.rumpf)
        if k is None:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "keine Schlüsselnummer lesbar",
                             "rohtext": e.rumpf[:200]})
            continue
        mv = _VERWEIS.search(e.rumpf)
        stadien = parse_namenskette(k.rest)
        if not stadien and not mv:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "kein Namensstadium erkannt",
                             "rohtext": e.rumpf[:200]})
        strassen.append({
            "schl_nr": k.schl_nr, "lemma": e.lemma_roh,
            "stadtteile": "; ".join(k.stadtteile),
            "strassenklasse": "; ".join(k.strassenklassen),
            "namensgruppe": k.namensgruppe,
            "verweis_auf": mv.group(1).strip() if mv else "",
            "buchseite": e.buchseite,
            "status": "automatisch"})
        for s in stadien:
            namen.append({"schl_nr": k.schl_nr, "stadium": s.stadium,
                          "gueltig_ab": s.gueltig_ab,
                          "datum_praezision": s.datum_praezision, "name": s.name,
                          "ist_urspruenglich": "wahr" if s.ist_urspruenglich else "falsch"})

    schreibe_strassen(strassen, ziel / "strassen.csv")
    schreibe_namen(namen, ziel / "namen.csv")
    schreibe_pruefung(pruefung, ziel / "pruefung.csv")
    kennzahlen = {"eintraege": len(eintraege), "strassen": len(strassen),
                  "namensstadien": len(namen), "pruefung": len(pruefung)}
    print(kennzahlen)
    return kennzahlen


if __name__ == "__main__":
    sys.exit(0 if main() else 0)
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_ausgabe.py -v`
Erwartet: 3 passed

- [ ] **Schritt 5: Gesamtlauf auf dem echten Material**

Run: `python3 -m strassen.erschliessen`
Erwartet: etwa `{'eintraege': 3340, 'strassen': 3300, 'namensstadien': 5000, 'pruefung': 40}` — die Prüfliste soll klein, aber nicht leer sein.

- [ ] **Schritt 6: Committen**

```bash
git add strassen/ausgabe.py strassen/erschliessen.py tests/test_ausgabe.py daten/
git commit -m "CSV-Ausgabe und Gesamtlauf: strassen, namen, pruefung"
```

---

### Task 6: Validierung — die drei Selbstprüfungen

Der Datensatz prüft sich gegen sich selbst. Ergebnis ist ein Qualitätsbericht mit bezifferten Fehlerquoten, der später ins README wandert.

**Files:**
- Create: `strassen/validierung.py`
- Create: `tests/test_validierung.py`

**Interfaces:**
- Produces: `pruefe_schluesselnummern(strassen: list[dict]) -> dict` mit Schlüsseln `luecken`, `dubletten`, `bereich`
- Produces: `pruefe_alphabet(strassen: list[dict]) -> list[dict]` — Lemmata, die aus der Sortierung fallen
- Produces: `pruefe_gegen_amtlich(strassen: list[dict], amtliche: set) -> dict` mit `bestaetigt`, `unbekannt`
- Produces: `schreibe_bericht(ergebnisse: dict, pfad)`

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_validierung.py
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_validierung.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.validierung'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/validierung.py
"""Drei unabhängige Selbstprüfungen des Datensatzes.

Die Schlüsselnummern sind amtlich und weitgehend fortlaufend, das Lexikon ist
alphabetisch geordnet, und die heutigen Straßennamen stehen im amtlichen
Verzeichnis. Jede Abweichung ist ein Kandidat für einen Parse- oder OCR-Fehler.
"""
import csv
import unicodedata
from collections import Counter
from pathlib import Path


def _sortierschluessel(lemma: str) -> str:
    s = unicodedata.normalize("NFKD", lemma.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("ß", "ss")


def pruefe_schluesselnummern(strassen) -> dict:
    nummern = [int(z["schl_nr"]) for z in strassen if str(z["schl_nr"]).isdigit()]
    zaehler = Counter(z["schl_nr"] for z in strassen)
    vorhanden = set(nummern)
    luecken = [n for n in range(min(nummern), max(nummern) + 1) if n not in vorhanden]
    return {"bereich": (min(nummern), max(nummern)),
            "anzahl": len(nummern),
            "luecken": luecken,
            "dubletten": [k for k, v in zaehler.items() if v > 1]}


def pruefe_alphabet(strassen) -> list:
    auffaellig = []
    schluessel = [(_sortierschluessel(z["lemma"]), z) for z in strassen]
    for i in range(1, len(schluessel) - 1):
        vor, akt, nach = schluessel[i - 1][0], schluessel[i][0], schluessel[i + 1][0]
        if akt < vor and akt < nach and vor <= nach:
            auffaellig.append(schluessel[i][1])
    return auffaellig


def pruefe_gegen_amtlich(strassen, amtliche) -> dict:
    bestaetigt, unbekannt = 0, []
    for z in strassen:
        if _sortierschluessel(z["lemma"]) in {_sortierschluessel(a) for a in amtliche}:
            bestaetigt += 1
        else:
            unbekannt.append(z["lemma"])
    return {"bestaetigt": bestaetigt, "unbekannt": unbekannt}


def lade_amtliche(pfad) -> set:
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        return {r["strasse"].strip() for r in csv.DictReader(f) if r.get("strasse")}


def schreibe_bericht(ergebnisse: dict, pfad):
    z = ["# Qualitätsbericht\n",
         "Drei unabhängige Selbstprüfungen des erschlossenen Datensatzes.\n",
         "## 1. Schlüsselnummern\n",
         f"- Bereich: {ergebnisse['nummern']['bereich'][0]}–"
         f"{ergebnisse['nummern']['bereich'][1]}",
         f"- erfasst: {ergebnisse['nummern']['anzahl']}",
         f"- Lücken: {len(ergebnisse['nummern']['luecken'])}",
         f"- Dubletten: {len(ergebnisse['nummern']['dubletten'])}\n",
         "## 2. Alphabetische Ordnung\n",
         f"- aus der Sortierung fallende Lemmata: {len(ergebnisse['alphabet'])}\n",
         "## 3. Abgleich mit dem amtlichen Straßenverzeichnis\n",
         f"- bestätigt: {ergebnisse['amtlich']['bestaetigt']}",
         f"- nicht im Verzeichnis: {len(ergebnisse['amtlich']['unbekannt'])}",
         "  (erwartbar bei aufgehobenen Straßen — nicht automatisch ein Fehler)\n"]
    Path(pfad).write_text("\n".join(z) + "\n", encoding="utf-8")
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_validierung.py -v`
Erwartet: 3 passed

- [ ] **Schritt 5: Bericht auf dem echten Datensatz erzeugen**

Run:
```bash
python3 -c "
import csv
from strassen.validierung import *
strassen = list(csv.DictReader(open('daten/strassen.csv', encoding='utf-8')))
amtlich = lade_amtliche('/home/christos/Projekte/AdressbuchEssen-v2/shared/strassen_aktuell.csv')
erg = {'nummern': pruefe_schluesselnummern(strassen),
       'alphabet': pruefe_alphabet(strassen),
       'amtlich': pruefe_gegen_amtlich(strassen, amtlich)}
schreibe_bericht(erg, 'docs/qualitaet.md')
print(open('docs/qualitaet.md').read())
"
```
Erwartet: ein Bericht mit bezifferten Werten. Lücken und auffällige Lemmata werden anschließend gesichtet; was ein Fehler ist, wandert nach `pruefung.csv`.

- [ ] **Schritt 6: Committen**

```bash
git add strassen/validierung.py tests/test_validierung.py docs/qualitaet.md
git commit -m "Validierung: Schlüsselnummern, Alphabet, Abgleich mit amtlichem Verzeichnis"
```

---

### Task 7: Stichtag messen und Konkordanz ableiten

Der Erhebungsstand des Adressbuchs wird aus den Daten bestimmt, nicht gesetzt; daraus entsteht die Konkordanz für das Kartenprojekt.

**Files:**
- Create: `strassen/stichtag.py`
- Create: `tests/test_stichtag.py`

**Interfaces:**
- Consumes: `daten/namen.csv`, `daten/strassen.csv`, `data/essen1936.csv` des Kartenprojekts
- Produces: `name_am_stichtag(stadien: list[dict], stichtag: str) -> dict | None`
- Produces: `messe_erhebungsstand(stadien_je_strasse: dict, adressbuch_namen: set) -> dict`
- Produces: `baue_konkordanz(strassen, namen, stichtag) -> list[dict]`

- [ ] **Schritt 1: Test schreiben**

```python
# tests/test_stichtag.py
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
```

- [ ] **Schritt 2: Test laufen lassen, Fehlschlag bestätigen**

Run: `python3 -m pytest tests/test_stichtag.py -v`
Erwartet: FAIL mit `ModuleNotFoundError: No module named 'strassen.stichtag'`

- [ ] **Schritt 3: Implementierung**

```python
# strassen/stichtag.py
"""Namensstand zu einem Stichtag bestimmen und die Konkordanz ableiten.

Stadien ohne verwertbares Datum werden übersprungen, nicht geschätzt; wo dadurch
kein Stadium bestimmbar ist, entsteht kein Konkordanzeintrag.
"""
from collections import defaultdict


def _vergleichbar(stadium) -> str:
    """Datum in vergleichbarer Form; leer, wenn nicht verwertbar."""
    wert = (stadium.get("gueltig_ab") or "").strip()
    if not wert:
        return ""
    if len(wert) == 4:            # nur Jahr: konservativ auf Jahresende legen
        return f"{wert}-12-31"
    return wert


def name_am_stichtag(stadien, stichtag: str):
    gueltig = None
    for s in sorted(stadien, key=lambda x: _vergleichbar(x) or "9999"):
        d = _vergleichbar(s)
        if not d:
            continue
        if d <= stichtag:
            gueltig = s
    return gueltig


def messe_erhebungsstand(stadien_je_strasse, adressbuch_namen) -> dict:
    """Zählt je Jahr, ob das Adressbuch die alte oder die neue Namensform nutzt."""
    befund = defaultdict(lambda: {"alt": 0, "neu": 0})
    for stadien in stadien_je_strasse.values():
        geordnet = sorted(stadien, key=lambda x: _vergleichbar(x) or "9999")
        for i in range(1, len(geordnet)):
            d = _vergleichbar(geordnet[i])
            if not d:
                continue
            jahr = int(d[:4])
            alt = geordnet[i - 1]["name"].strip().lower()
            neu = geordnet[i]["name"].strip().lower()
            if alt in adressbuch_namen and neu not in adressbuch_namen:
                befund[jahr]["alt"] += 1
            elif neu in adressbuch_namen and alt not in adressbuch_namen:
                befund[jahr]["neu"] += 1
    return dict(sorted(befund.items()))


def baue_konkordanz(strassen, namen, stichtag: str) -> list:
    je_nr = defaultdict(list)
    for z in namen:
        je_nr[z["schl_nr"]].append(z)
    aus = []
    for s in strassen:
        stadien = je_nr.get(s["schl_nr"], [])
        treffer = name_am_stichtag(stadien, stichtag)
        if not treffer:
            continue
        if treffer["name"].strip() == s["lemma"].strip():
            continue                      # Name unverändert — kein Konkordanzeintrag
        aus.append({"stadtteil": s.get("stadtteile", "").split(";")[0].strip(),
                    "ehemalig": treffer["name"].strip(),
                    "heutig": s["lemma"].strip(),
                    "schl_nr": s["schl_nr"],
                    "datum_praezision": treffer.get("datum_praezision", ""),
                    "quelle": "Dickhoff 2015"})
    return aus
```

- [ ] **Schritt 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_stichtag.py -v`
Erwartet: 4 passed

- [ ] **Schritt 5: Erhebungsstand messen und Konkordanz erzeugen**

Run:
```bash
python3 -c "
import csv, re
from collections import defaultdict
from strassen.stichtag import messe_erhebungsstand, baue_konkordanz
namen = list(csv.DictReader(open('daten/namen.csv', encoding='utf-8')))
strassen = list(csv.DictReader(open('daten/strassen.csv', encoding='utf-8')))
je = defaultdict(list)
for z in namen: je[z['schl_nr']].append(z)
ab = set()
with open('/home/christos/Projekte/AdressbuchEssen-v2/data/essen1936.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        a = (r.get('Adresse') or '').strip()
        s = re.split(r'\s+\d', a)[0].strip()
        if s: ab.add(s.lower())
print('Erhebungsstand-Messung:')
for jahr, w in messe_erhebungsstand(je, ab).items():
    if 1930 <= jahr <= 1940: print(f'   {jahr}: alt={w[\"alt\"]:4d}  neu={w[\"neu\"]:4d}')
k = baue_konkordanz(strassen, namen, '1936-06-30')
print('Konkordanzeinträge:', len(k))
import csv as c
with open('daten/konkordanz_1936.csv','w',encoding='utf-8',newline='') as g:
    w = c.DictWriter(g, fieldnames=['stadtteil','ehemalig','heutig','schl_nr','datum_praezision','quelle'])
    w.writeheader(); w.writerows(k)
"
```
Erwartet: Der Umschlag zwischen „neu" und „alt" liegt bei 1936/1937 (vgl. Vorabmessung: 1937 = 196 alt zu 15 neu). Konkordanzeinträge deutlich über den bisherigen 442.

- [ ] **Schritt 6: Committen**

```bash
git add strassen/stichtag.py tests/test_stichtag.py daten/konkordanz_1936.csv
git commit -m "Stichtagsmessung und Konkordanz-Ableitung aus den Namensstadien"
```

---

### Task 8: Veröffentlichungsformalia

Alles, was den Datensatz von einer Datei zu einer zitierfähigen Publikation macht.

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `CITATION.cff`
- Create: `datapackage.json`
- Modify: `strassen/ocr_lauf.py` (aus dem Datensammlungs-Ordner übernehmen)

**Interfaces:**
- Consumes: `docs/qualitaet.md` (Zahlen für den Qualitätsabschnitt des README)

- [ ] **Schritt 1: OCR-Skript ins Repo übernehmen**

Der OCR-Code gehört zur Methode und ist selbst publizierbar — er enthält keine geschützten Inhalte. Dritte mit eigenem Buchexemplar können den Datensatz damit nachbauen.

```bash
cp "/home/christos/Projekte/00_Datensammlung/Dickhoff_Essener Straßen_2015_zusammenfügen/ocr/ocr_lauf.py" strassen/ocr_lauf.py
```

- [ ] **Schritt 2: README schreiben**

Pflichtinhalte, jeweils mit den echten Zahlen aus `docs/qualitaet.md`:
- Was der Datensatz enthält und was nicht (ausdrücklich: keine Erläuterungstexte)
- Quelle mit vollständiger bibliographischer Angabe und ISBN
- Methode in fünf Sätzen: Scan → OCR mit Bundsteg-Teilung → regelbasierter Parser → drei Selbstprüfungen → Ableitung
- Data Dictionary: alle Spalten beider Tabellen mit Wertebereich (die Tabellen aus Abschnitt 4 der Spec übernehmen)
- Bezifferte Qualität: Anzahl Einträge, Prüflisten-Umfang, Ergebnisse der drei Prüfungen
- Zitierhinweis für den Datensatz **und** für Dickhoff als Quelle
- Der Hinweis, dass für abgeleitete Arbeiten Dickhoff 2015 zu zitieren ist

- [ ] **Schritt 3: LICENSE und CITATION.cff anlegen**

`LICENSE`: CC-BY-4.0-Volltext, mit einer vorangestellten Klarstellung, dass sich die Lizenz auf die Struktur, den Code und die Zusammenstellung bezieht, nicht auf die zugrunde liegenden Sachangaben aus Dickhoff 2015.

**Vor dem Schreiben der Datei:** Vor- und Nachname sowie eine etwaige ORCID und
Institutionszugehörigkeit beim Nutzer erfragen. Diese Angaben dürfen **nicht** aus der
Git-Konfiguration oder der E-Mail-Adresse abgeleitet werden — sie erscheinen dauerhaft in
den Zenodo-Metadaten und im DOI-Eintrag.

```yaml
# CITATION.cff
cff-version: 1.2.0
title: "Essener Straßenverzeichnis: Namen und Umbenennungen"
message: "Wenn Sie diesen Datensatz nutzen, zitieren Sie ihn bitte wie folgt."
type: dataset
authors:
  - family-names: "…vom Nutzer erfragen…"
    given-names: "…vom Nutzer erfragen…"
abstract: >-
  Strukturiertes Verzeichnis der Essener Straßen mit datierter Namensgeschichte,
  erschlossen aus Erwin Dickhoff: Essener Straßen (Klartext-Verlag, Essen 2015).
  Erlaubt die Auflösung historischer Essener Adressen zu beliebigen Stichtagen.
keywords:
  - Essen
  - Straßennamen
  - historische Geographie
  - Digital Humanities
  - Adressbuch
license: CC-BY-4.0
references:
  - type: book
    title: "Essener Straßen"
    authors:
      - family-names: "Dickhoff"
        given-names: "Erwin"
    publisher:
      name: "Klartext-Verlag"
    year: 2015
    isbn: "978-3-8375-1231-1"
```

- [ ] **Schritt 4: datapackage.json anlegen**

```json
{
  "name": "essener-strassen",
  "title": "Essener Straßenverzeichnis: Namen und Umbenennungen",
  "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/"}],
  "sources": [{
    "title": "Erwin Dickhoff: Essener Straßen. Klartext-Verlag, Essen 2015",
    "path": "urn:isbn:9783837512311"
  }],
  "resources": [
    {
      "name": "strassen",
      "path": "daten/strassen.csv",
      "format": "csv",
      "encoding": "utf-8",
      "schema": {
        "primaryKey": "schl_nr",
        "fields": [
          {"name": "schl_nr", "type": "string", "description": "amtliche Schlüsselnummer, fünfstellig"},
          {"name": "lemma", "type": "string", "description": "heutiger Straßenname (Stichwort des Eintrags)"},
          {"name": "stadtteile", "type": "string", "description": "Stadtteil(e), mehrere mit '; ' getrennt"},
          {"name": "strassenklasse", "type": "string", "description": "Gemeindestraße, Kreisstraße, Landstraße; mehrere mit '; ' getrennt"},
          {"name": "namensgruppe", "type": "string", "description": "Str.-Gr. der Quelle, wörtlich übernommen"},
          {"name": "verweis_auf", "type": "string", "description": "Ziel-Lemma bei 'Siehe X', sonst leer"},
          {"name": "buchseite", "type": "integer", "description": "Beleg: Seite in Dickhoff 2015"},
          {"name": "status", "type": "string", "constraints": {"enum": ["automatisch", "geprueft", "unsicher"]}}
        ]
      }
    },
    {
      "name": "namen",
      "path": "daten/namen.csv",
      "format": "csv",
      "encoding": "utf-8",
      "schema": {
        "primaryKey": ["schl_nr", "stadium"],
        "foreignKeys": [{"fields": "schl_nr", "reference": {"resource": "strassen", "fields": "schl_nr"}}],
        "fields": [
          {"name": "schl_nr", "type": "string", "description": "Fremdschlüssel auf strassen.csv"},
          {"name": "stadium", "type": "integer", "description": "laufende Nummer der Namensstufe, 1 = älteste"},
          {"name": "gueltig_ab", "type": "string", "description": "ISO-Datum oder Jahr, leer wenn unbekannt"},
          {"name": "datum_praezision", "type": "string", "constraints": {"enum": ["tag", "monat", "jahr", "vor", "nach", "unbekannt"]}},
          {"name": "name", "type": "string", "description": "Straßenname in diesem Stadium"},
          {"name": "ist_urspruenglich", "type": "string", "constraints": {"enum": ["wahr", "falsch"]}}
        ]
      }
    },
    {
      "name": "konkordanz_1936",
      "path": "daten/konkordanz_1936.csv",
      "format": "csv",
      "encoding": "utf-8",
      "schema": {
        "fields": [
          {"name": "stadtteil", "type": "string"},
          {"name": "ehemalig", "type": "string", "description": "Name zum Erhebungsstand des Adressbuchs 1936"},
          {"name": "heutig", "type": "string", "description": "heutiger Name"},
          {"name": "schl_nr", "type": "string"},
          {"name": "datum_praezision", "type": "string", "description": "Genauigkeit der zugrunde liegenden Datierung"},
          {"name": "quelle", "type": "string"}
        ]
      }
    }
  ]
}
```

- [ ] **Schritt 5: Prüfen, dass keine geschützten Inhalte im Publikationsstand liegen**

Run:
```bash
git ls-files | grep -c "^ocr/seiten"     # muss 0 sein
python3 -c "
import csv
for datei in ['daten/strassen.csv','daten/namen.csv','daten/konkordanz_1936.csv']:
    lang = [z for z in open(datei,encoding='utf-8') if len(z) > 300]
    print(datei, '– auffällig lange Zeilen:', len(lang))
"
```
Erwartet: `0` und keine langen Zeilen — lange Zeilen wären ein Hinweis auf eingeschleppten Fließtext.

- [ ] **Schritt 6: Committen**

```bash
git add README.md LICENSE CITATION.cff datapackage.json strassen/ocr_lauf.py
git commit -m "Veröffentlichungsformalia: README, Lizenz, Zitierangabe, Datenpaket-Schema"
```

---

## Nach dem Plan

- **Goldstandard-Stichprobe:** 50 zufällige Einträge Zeichen für Zeichen gegen den Scan prüfen, Feldfehlerquote ins README. Braucht menschliche Prüfung, deshalb kein automatisierbarer Task.
- **Prüfliste abarbeiten:** `pruefung.csv` sichten, Korrekturen einpflegen, Lauf wiederholen.
- **Übergabe an das Kartenprojekt:** `konkordanz_1936.csv` dort einbinden und die Widersprüche zum bisherigen Wikipedia-Extrakt protokollieren.
- **Zenodo:** GitHub-Release anlegen und mit Zenodo verknüpfen.
