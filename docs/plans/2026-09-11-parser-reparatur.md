# Parser-Reparatur nach der Goldstandard-Stichprobe: Implementierungsplan

> **Für agentische Bearbeiter:** ERFORDERLICHE SUB-SKILL: `superpowers:subagent-driven-development` (empfohlen) oder `superpowers:executing-plans`, um diesen Plan Aufgabe für Aufgabe umzusetzen. Die Schritte nutzen Checkbox-Syntax (`- [ ]`) zur Nachverfolgung.

**Ziel:** Die 21 in der Spec katalogisierten Parser- und OCR-Muster beheben, sodass der Datensatz rund 44 zusätzliche Namensketten gewinnt, keine unmarkierten Kopffeld-Lücken mehr enthält und jede Änderung gegenüber dem bisherigen Stand in einem Differenzbericht nachgewiesen ist.

**Architektur:** Ein neues Modul `strassen/datum.py` wird die einzige Quelle für Datumsstempel und die Satzende-Regel; `kopf.py` (Abgrenzung der Namenskette) und `namen.py` (Parsen der Stadien) nutzen es gemeinsam. Toleranzen liefern einen `hinweis`, der in `erschliessen.py` zum Prüfgrund wird. Normalisierungen des Rohtexts liegen in `aufbereitung.py`. Ein Differenzwerkzeug und ein Goldstandard-Regressionstest sichern die Regeneration ab.

**Tech Stack:** Python 3.12, ausschließlich Standardbibliothek (`re`, `csv`, `pathlib`), pytest für Tests. Keine neuen Abhängigkeiten.

**Spec:** `docs/specs/2026-09-11-parser-reparatur-design.md` (Regelnummern im Plan beziehen sich auf deren Abschnitt 4)

## Globale Randbedingungen

- **Precision-first:** Nichts wird geraten. Ein tolerant erkannter Wert wird übernommen **und** der Eintrag über einen Prüfgrund `status=unsicher` (Spec, Abschnitt 1, Entscheidungen).
- **Deutschsprachige Bezeichner** in Code, Tests und Daten.
- **Keine externen Abhängigkeiten** außer pytest.
- **Testdaten sind echte OCR-Ausschnitte** aus `ocr/seiten/` mit Schlüsselnummer und Buchseite im Docstring. Die in diesem Plan zitierten Ausschnitte stammen aus der Nachmessung vom 2026-09-11 und sind wörtlich zu übernehmen.
- **Bestehende Tests bleiben grün.** Wo ein bestehender Test altes Fehlverhalten festschreibt, wird er angepasst und die Anpassung in der Commit-Nachricht begründet.
- **`ocr/seiten/` ist gitignored und nur lokal vorhanden.** Tests, die darauf zugreifen, überspringen sich mit `pytest.skip`, wenn das Verzeichnis fehlt.
- **Commit-Trailer:** `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
- **Arbeitsverzeichnis:** `/home/christos/Projekte/essener-strassen`. Tests laufen mit `python3 -m pytest -q`.

## Sollwerte aus dem Prototyp (Spec, Abschnitt 1)

Nach Task 11 müssen die Kennzahlen mindestens diese Größenordnung erreichen; deutliche Abweichungen sind vor dem Commit zu erklären:

| Kennzahl | vorher | Soll (mindestens) |
|---|--:|--:|
| Straßen ohne Namenskette | 84 | ≤ 40 |
| Namensstadien | 5.283 | ≥ 5.370 |
| Namen nur „St"/„I"/„II"/„IV" | 16 | 0 |
| leere Straßenklasse | 54 | ≤ 45 (davor Regel 19/20 → weniger) |

---

## Dateistruktur

| Datei | Verantwortung | Task |
|---|---|---|
| `strassen/datum.py` (neu) | Datumsstempel aller Varianten, Tag-/Monatsvalidierung, Präzision, Hinweise, Satzende-Regel, unscharfer Wortvergleich | 1, 2 |
| `strassen/namen.py` | Namenskette aus `rest`; nutzt `datum`; `Stadium.hinweis` | 3 |
| `strassen/kopf.py` | Kopffelder, Kettenabgrenzung, Marker-Toleranz, Klassenwort-Regeln; `Kopf.hinweise` | 4, 5 |
| `strassen/segmentierung.py` | Lemma mit „St. "-Abkürzung | 6 |
| `strassen/aufbereitung.py` | Abschnittskopf klein, Randrauschen, Stadtteil-Marker, `xundX` | 7 |
| `strassen/erschliessen.py` | Hinweise → Prüfgründe; leere Kopffelder | 8 |
| `datapackage.json`, `README.md`, Spec 2026-08-20 | Präzision `jahrhundert` | 9 |
| `strassen/differenz.py` (neu) | Vergleich zweier Datenstände, Markdown-Bericht | 10 |
| `tests/test_goldstandard_regression.py` (neu) | 17 Korrekturen der Stichprobe gegen den Parser | 11 |
| `daten/`, `docs/qualitaet.md`, `docs/regression/` | Regeneration und Nachweis | 12 |

---

### Task 1: `strassen/datum.py` — Satzende-Regel und sichere Datumsformen

**Files:**
- Create: `strassen/datum.py`
- Test: `tests/test_datum.py`

**Interfaces:**
- Produces:
  - `MONATE: dict[str, int]` (zieht von `namen.py` hierher um; `namen.MONATE` bleibt als Re-Export, weil `kopf.py` es importiert)
  - `SATZENDE: str` — Regex-Baustein (kein kompiliertes Muster), Punkt der ein Satzende ist
  - `DATUMSSTEMPEL_MUSTER: str` und `DATUMSSTEMPEL: re.Pattern` — benannte Gruppen `jh, num_tag, num_monat, num_jahr, tag, tag_trenner, monat, jahr_tag, qualifier, jahr_qual, jahr2, jahr_bloss, jahr2b, trenner`
  - `class Datum(NamedTuple): gueltig_ab: str; praezision: str; hinweis: str; trenner: str`
  - `lese_datum(m: re.Match) -> Datum`

- [ ] **Step 1: Failing Tests für Satzende und die sicheren Formen schreiben**

```python
# tests/test_datum.py
import re

import pytest

from strassen.datum import SATZENDE, DATUMSSTEMPEL, lese_datum, MONATE


_SATZ = re.compile(SATZENDE)


def _stempel(text):
    m = DATUMSSTEMPEL.search(text)
    assert m, text
    return lese_datum(m)


# --- Satzende (Regel 4) ---

def test_satzende_nach_wort_vor_grossbuchstabe():
    assert _SATZ.search("Kronenstraße. Die Pottgasse")


def test_kein_satzende_nach_st_abkuerzung():
    """St. Annental, Schl.-Nr. 02727, S. 309: 'St. Annental' wurde zu 'St'."""
    assert not _SATZ.search("St. Annental")


def test_kein_satzende_nach_roemischer_zahl():
    """Gerswidastraße, Schl.-Nr. 01022, S. 127: 'II. Weberstraße' wurde zu 'II'."""
    for zahl in ["I", "II", "III", "IV"]:
        assert not _SATZ.search(f"{zahl}. Weberstraße"), zahl


def test_kein_satzende_nach_ziffer():
    """Die Tagesziffer eines Datums ('26. Mai') ist kein Satzende."""
    assert not _SATZ.search("26. Mai 1939")


def test_satzende_am_stringende():
    assert _SATZ.search("Am Schroer.")


# --- sichere Datumsformen (Regeln 7, 8 und Bestand) ---

def test_tagesdatum():
    d = _stempel("26. Mai 1939: Kamerunstraße")
    assert (d.gueltig_ab, d.praezision, d.hinweis, d.trenner) == ("1939-05-26", "tag", "", ":")


def test_numerisches_datum():
    """Schlenterstraße, Schl.-Nr. 02774, S. 291: '29.08.1927: Schlenterstraße'."""
    d = _stempel("29.08.1927: Schlenterstraße")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1927-08-29", "tag", "")


def test_jahrhundert():
    """Bungertstraße 00491 (S. 85) '16. Jahrhundert:', Oefte 03731 (S. 251) '9. Jahrh.:',
    Limbecker Straße 01971 (S. 223) 'im 16. Jahrhundert:'."""
    assert _stempel("16. Jahrhundert: Bungertstraße").gueltig_ab == "1501"
    assert _stempel("16. Jahrhundert: Bungertstraße").praezision == "jahrhundert"
    assert _stempel("9. Jahrh.: Oefte").gueltig_ab == "0801"
    assert _stempel("im 16. Jahrhundert: Lyndenbeker Straße").praezision == "jahrhundert"


def test_qualifier_vor_nach_jahr():
    assert _stempel("vor 1826: II. Weberstraße").praezision == "vor"
    assert _stempel("nach 1900: X").praezision == "nach"
    assert _stempel("etwa 1921: Nelkenstraße").praezision == "jahr"
    assert _stempel("um 1850: X").gueltig_ab == "1850"


def test_blosses_jahr():
    d = _stempel("1902: Barkhofstraße")
    assert (d.gueltig_ab, d.praezision) == ("1902", "jahr")


def test_stempel_setzt_nicht_mitten_in_ziffernfolge_an():
    """'19862:' (Spervogelweg 02949, S. 306) darf nicht als '9862:' oder '1986' gelesen werden."""
    assert DATUMSSTEMPEL.search("Minnesängerr 27. September 19862: Spervogelweg") is None \
        or DATUMSSTEMPEL.search("Minnesängerr 27. September 19862: Spervogelweg").group("jahr_tag") is None


def test_monate_vollstaendig():
    assert len(MONATE) == 12 and MONATE["März"] == 3
```

- [ ] **Step 2: Tests laufen lassen, Fehlschlag prüfen**

Run: `python3 -m pytest tests/test_datum.py -q`
Expected: `ModuleNotFoundError: No module named 'strassen.datum'`

- [ ] **Step 3: Modul anlegen (sichere Formen; tolerante Formen folgen in Task 2)**

```python
# strassen/datum.py
"""Datumsstempel eines Namensstadiums und die Satzende-Regel.

Eine Quelle für kopf.py (Abgrenzung der Namenskette) und namen.py (Parsen der
Stadien). Bis 2026-09 existierte die Datumslogik doppelt mit leicht abweichenden
Regeln; in dieser Lücke saßen der Fallback-Bug und die Tagesziffer-Grenze
(Spec 2026-09-11, Abschnitt 1).

Ein Stempel ist eine der Formen
  'dd. Monat jjjj:'   'dd, Monat jjjj:'   'dd.mm.jjjj:'   'N. Jahrhundert:' / 'N. Jahrh.:'
  'vor|nach|um|etwa|gegen jjjj:'   'jjjj:'   'jjjj/jj:'
jeweils auch mit ';' oder ',' statt ':' oder ganz ohne Trennzeichen (dann liefert
lese_datum einen Hinweis; die Positionsregel dafür setzen die Aufrufer um, s.
namen.parse_namenskette und kopf._stadienkette).

precision-first: Ein ungültiger Tag oder Monat wird nicht verworfen und nicht
geraten, sondern auf die Jahresform reduziert und mit Hinweis versehen.
"""
import re
from typing import NamedTuple

MONATE = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
          "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11,
          "Dezember": 12}

# Ein Punkt ist KEIN Satzende, wenn er auf eine Ziffer ('26.'), auf 'St' ('St.
# Annental') oder auf eine römische Zahl I–IV ('II. Weberstraße') folgt.
# Lookbehinds sind je fester Breite; \b ist nullbreit und deshalb erlaubt.
_KEIN_ABKUERZUNGSPUNKT = r"(?<!\d)(?<!\bSt)(?<!\bI)(?<!\bII)(?<!\bIII)(?<!\bIV)"
SATZENDE = _KEIN_ABKUERZUNGSPUNKT + r"\.(?=\s+[0-9A-ZÄÖÜ]|\s*$)"

_MONAT_WORT = r"(?P<monat>[A-Za-zÄÖÜäöü]{3,9})"     # Prüfung gegen MONATE in lese_datum
_TRENNER = r"\s*(?P<trenner>:|;|,|)"                 # ':' regulär, sonst Hinweis

DATUMSSTEMPEL_MUSTER = (
    r"(?<![\d/])(?:"
    r"(?:im\s+)?(?P<jh>\d{1,2})\.\s*Jahrh(?:undert|\.)"
    r"|(?P<num_tag>\d{2})\.(?P<num_monat>\d{2})\.(?P<num_jahr>\d{4})"
    r"|(?P<tag>\d{1,3})(?P<tag_trenner>[.,])\s*" + _MONAT_WORT + r"\s+(?P<jahr_tag>\d{4})"
    r"|(?P<qualifier>vor|nach|um|etwa|gegen)\s+(?P<jahr_qual>\d{4})(?:/(?P<jahr2>\d{2}))?"
    r"|(?P<jahr_bloss>\d{4})(?:/(?P<jahr2b>\d{2}))?"
    r")(?!\d)" + _TRENNER
)
DATUMSSTEMPEL = re.compile(DATUMSSTEMPEL_MUSTER)

_GERICHTET = {"vor": "vor", "nach": "nach"}

HINWEIS_KOMMA_NACH_TAG = "Datum: Komma nach Tag"
HINWEIS_OHNE_DOPPELPUNKT = "Datum ohne Doppelpunkt"
HINWEIS_MONAT_KORRIGIERT = "Monatsname OCR-korrigiert"
HINWEIS_DOPPELJAHR = "Datum: Doppeljahr"
HINWEIS_TAG_UNGUELTIG = "Datum: Tag ungültig"


class Datum(NamedTuple):
    gueltig_ab: str       # ISO-Datum, Jahr (4-stellig) oder leer
    praezision: str       # tag | jahr | vor | nach | jahrhundert
    hinweis: str          # "" oder mehrere Hinweise, mit "; " verbunden
    trenner: str          # ':' ';' ',' oder ''


def lese_datum(m: re.Match) -> Datum:
    hinweise = []
    trenner = m.group("trenner")
    if trenner != ":":
        hinweise.append(HINWEIS_OHNE_DOPPELPUNKT)

    if m.group("jh"):
        jh = int(m.group("jh"))
        return Datum(f"{(jh - 1) * 100 + 1:04d}", "jahrhundert", "; ".join(hinweise), trenner)

    if m.group("num_jahr"):
        tag, monat, jahr = int(m.group("num_tag")), int(m.group("num_monat")), m.group("num_jahr")
        if 1 <= tag <= 31 and 1 <= monat <= 12:
            return Datum(f"{jahr}-{monat:02d}-{tag:02d}", "tag", "; ".join(hinweise), trenner)
        hinweise.append(HINWEIS_TAG_UNGUELTIG)
        return Datum(jahr, "jahr", "; ".join(hinweise), trenner)

    if m.group("jahr_tag"):
        return _tagesdatum(m, hinweise, trenner)

    if m.group("qualifier"):
        praezision = _GERICHTET.get(m.group("qualifier"), "jahr")
        if m.group("jahr2"):
            hinweise.append(HINWEIS_DOPPELJAHR)
        return Datum(m.group("jahr_qual"), praezision, "; ".join(hinweise), trenner)

    if m.group("jahr2b"):
        hinweise.append(HINWEIS_DOPPELJAHR)
    return Datum(m.group("jahr_bloss"), "jahr", "; ".join(hinweise), trenner)


def _tagesdatum(m: re.Match, hinweise: list, trenner: str) -> Datum:
    jahr = m.group("jahr_tag")
    if m.group("tag_trenner") == ",":
        hinweise.append(HINWEIS_KOMMA_NACH_TAG)
    monat_nr = MONATE.get(m.group("monat"))
    if monat_nr is None:
        kandidat = unscharf_eindeutig(m.group("monat"), MONATE)
        if kandidat is None:
            hinweise.append(HINWEIS_TAG_UNGUELTIG)
            return Datum(jahr, "jahr", "; ".join(hinweise), trenner)
        hinweise.append(HINWEIS_MONAT_KORRIGIERT)
        monat_nr = MONATE[kandidat]
    tag = int(m.group("tag"))
    if not 1 <= tag <= 31:
        hinweise.append(HINWEIS_TAG_UNGUELTIG)
        return Datum(jahr, "jahr", "; ".join(hinweise), trenner)
    return Datum(f"{jahr}-{monat_nr:02d}-{tag:02d}", "tag", "; ".join(hinweise), trenner)


def unscharf_eindeutig(wort: str, kandidaten) -> str | None:
    """Der eine Kandidat mit Levenshtein-Distanz genau 1 zu wort (Groß-/
    Kleinschreibung egal); None, wenn keiner oder mehrere passen. Distanz 1 ist
    bewusst die Obergrenze: ein OCR-Fehler pro Wort ('Novemner', 'Aprit', 'Mat'),
    nicht zwei — sonst würde geraten."""
    treffer = [k for k in kandidaten if _distanz_eins(wort.lower(), k.lower())]
    return treffer[0] if len(treffer) == 1 else None


def _distanz_eins(a: str, b: str) -> bool:
    if a == b:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if abs(len(a) - len(b)) != 1:
        return False
    lang, kurz = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(lang)):
        if lang[:i] + lang[i + 1:] == kurz:
            return True
    return False
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_datum.py -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/datum.py tests/test_datum.py
git commit -m "datum.py: gemeinsame Satzende-Regel und Datumsstempel (Regeln 4, 7, 8)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `datum.py` — tolerante Formen mit Hinweis

**Files:**
- Modify: `strassen/datum.py` (nur Tests ergänzen; der Code aus Task 1 deckt die Formen bereits ab — dieser Task **beweist** das und fixt, was fehlt)
- Test: `tests/test_datum.py`

**Interfaces:**
- Consumes: `DATUMSSTEMPEL`, `lese_datum`, Hinweis-Konstanten aus Task 1
- Produces: verifizierte Hinweistexte (wörtlich, werden in Task 8 zu Prüfgründen):
  `"Datum: Komma nach Tag"`, `"Datum ohne Doppelpunkt"`, `"Monatsname OCR-korrigiert"`, `"Datum: Doppeljahr"`, `"Datum: Tag ungültig"`

- [ ] **Step 1: Failing Tests anhängen**

```python
# tests/test_datum.py (anhängen)

# --- tolerante Formen (Regeln 6, 14, 15, 16, 18) ---

def test_komma_nach_tag_mit_hinweis():
    """Eskenshof, Schl.-Nr. 00817, S. 110: '13, Juni 1973: Eskenshof'."""
    d = _stempel("13, Juni 1973: Eskenshof")
    assert d.gueltig_ab == "1973-06-13"
    assert d.hinweis == "Datum: Komma nach Tag"


def test_ohne_doppelpunkt_mit_hinweis():
    """Berghausbusch, Schl.-Nr. 00471, S. 84: '11. Dezember 1974 Berghausbusch'."""
    d = _stempel("11. Dezember 1974 Berghausbusch")
    assert d.gueltig_ab == "1974-12-11"
    assert d.trenner == ""
    assert d.hinweis == "Datum ohne Doppelpunkt"


def test_semikolon_und_komma_statt_doppelpunkt():
    """Hobirkheide 01320 (S. 162) '05. Juni 1934; Hobirkheide';
    Havelring 01416 (S. 152) '07. September 1960, Havelring'."""
    assert _stempel("05. Juni 1934; Hobirkheide").trenner == ";"
    assert _stempel("05. Juni 1934; Hobirkheide").hinweis == "Datum ohne Doppelpunkt"
    assert _stempel("07. September 1960, Havelring").trenner == ","


def test_monatsname_mit_einem_ocr_fehler_wird_korrigiert():
    """Deilbachufer 00608 (S. 95) 'Novemner'; Einbleckstraße 00745 'Nobember';
    Möllneys Nocken 02149 'Aprit'; Bonsiepen 02515 'Mat'."""
    assert _stempel("13. Novemner 1900: Uferstraße").gueltig_ab == "1900-11-13"
    assert _stempel("13. Novemner 1900: Uferstraße").hinweis == "Monatsname OCR-korrigiert"
    assert _stempel("28. Nobember 1895: Einbleckstraße").gueltig_ab == "1895-11-28"
    assert _stempel("13. Aprit 1908: Möllneys Nocken").gueltig_ab == "1908-04-13"
    assert _stempel("18. Mat 1989: Bonsiepen").gueltig_ab == "1989-05-18"


def test_unbekanntes_monatswort_reduziert_auf_jahr():
    d = _stempel("13. Xyzabc 1900: Uferstraße")
    assert (d.gueltig_ab, d.praezision) == ("1900", "jahr")
    assert "Datum: Tag ungültig" in d.hinweis


def test_ungueltiger_tag_reduziert_auf_jahr():
    """Graudenzstraße, Schl.-Nr. 01073, S. 146: '085. Februar 1929'."""
    d = _stempel("085. Februar 1929: Heinrich-Lersch-Straße")
    assert (d.gueltig_ab, d.praezision) == ("1929", "jahr")
    assert d.hinweis == "Datum: Tag ungültig"


def test_ungueltiger_numerischer_monat_reduziert_auf_jahr():
    d = _stempel("29.18.1927: X")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1927", "jahr", "Datum: Tag ungültig")


def test_doppeljahr_mit_hinweis():
    """Henglerplatz, Schl.-Nr. 01273, S. 155: 'etwa 1910/11: Henglerplatz'."""
    d = _stempel("etwa 1910/11: Henglerplatz")
    assert (d.gueltig_ab, d.praezision, d.hinweis) == ("1910", "jahr", "Datum: Doppeljahr")


def test_mehrere_hinweise_werden_verbunden():
    d = _stempel("13, Novemner 1900 Uferstraße")
    assert d.hinweis == "Datum ohne Doppelpunkt; Datum: Komma nach Tag; Monatsname OCR-korrigiert"


def test_unscharf_eindeutig_verlangt_eindeutigkeit():
    from strassen.datum import unscharf_eindeutig
    assert unscharf_eindeutig("Novemner", MONATE) == "November"
    assert unscharf_eindeutig("Jun", MONATE) == "Juni"
    assert unscharf_eindeutig("Xyz", MONATE) is None
    assert unscharf_eindeutig("Mai", MONATE) is None      # exakt gleich zählt nicht als Distanz 1
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_datum.py -q`
Expected: Fälle, die der Code aus Task 1 schon abdeckt, sind grün; jeder rote Fall ist ein Befund. Erwartet rot ist mindestens keiner — falls doch, in Step 3 im Code beheben, nicht im Test.

- [ ] **Step 3: Rote Fälle im Code beheben (falls vorhanden), sonst überspringen**

Typische Ursache: Reihenfolge der Alternativen in `DATUMSSTEMPEL_MUSTER` (die Jahrhundert- und die numerische Form müssen vor der Tagesform stehen, die Qualifier-Form vor dem bloßen Jahr). Nur an `DATUMSSTEMPEL_MUSTER` oder `lese_datum` ändern.

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_datum.py -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/datum.py tests/test_datum.py
git commit -m "datum.py: tolerante Formen mit Hinweis (Regeln 6, 14, 15, 16, 18)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `namen.py` auf `datum.py` umstellen, `Stadium.hinweis`, `urspr.` ohne Doppelpunkt

**Files:**
- Modify: `strassen/namen.py` (gesamte Datei)
- Test: `tests/test_namen.py`

**Interfaces:**
- Consumes: `datum.DATUMSSTEMPEL_MUSTER`, `datum.SATZENDE`, `datum.lese_datum`, `datum.MONATE`
- Produces:
  - `MONATE` (Re-Export aus `datum`, weil `kopf.py` `from strassen.namen import MONATE` nutzt — bleibt bis Task 4, danach importiert `kopf` direkt aus `datum`)
  - `class Stadium(NamedTuple): stadium: int; gueltig_ab: str; datum_praezision: str; name: str; ist_urspruenglich: bool; hinweis: str = ""`
  - `parse_namenskette(rest: str) -> list[Stadium]` (Signatur unverändert)
  - Hinweistext `"urspr. ohne Doppelpunkt"`

- [ ] **Step 1: Failing Tests anhängen**

```python
# tests/test_namen.py (anhängen)

def test_st_abkuerzung_bleibt_im_namen():
    """St. Annental, Schl.-Nr. 02727, S. 309 — Goldstandard-Fehler: Stadium 3 hieß 'St'."""
    rest = ("04. Februar 1904: Kapellenstraße, 16. September 1910: Walpurgisstraße (tiw.), "
            "18. September 1926: St. Annental.")
    s = parse_namenskette(rest)
    assert [x.name for x in s] == ["Kapellenstraße", "Walpurgisstraße (tiw.)", "St. Annental"]


def test_roemische_zahl_bleibt_im_namen():
    """Gerswidastraße, Schl.-Nr. 01022, S. 127 — Goldstandard-Fehler: Stadium 1 hieß 'II'."""
    s = parse_namenskette("vor 1826: II. Weberstraße, 13. Juni 1966: Gerswidastraße.")
    assert s[0].name == "II. Weberstraße"
    assert s[0].datum_praezision == "vor"
    assert s[1].name == "Gerswidastraße"


def test_stadium_traegt_hinweis_aus_datum():
    s = parse_namenskette("13, Juni 1973: Eskenshof.")
    assert s[0].gueltig_ab == "1973-06-13"
    assert s[0].hinweis == "Datum: Komma nach Tag"


def test_regulaeres_stadium_hat_leeren_hinweis():
    s = parse_namenskette("16. Mai 1902: Kruppstraße.")
    assert s[0].hinweis == ""


def test_datum_ohne_doppelpunkt_am_kettenanfang():
    """Berghausbusch, Schl.-Nr. 00471, S. 84: '11. Dezember 1974 Berghausbusch. Jan Hendrich B…'"""
    s = parse_namenskette("11. Dezember 1974 Berghausbusch.")
    assert [x.name for x in s] == ["Berghausbusch"]
    assert s[0].hinweis == "Datum ohne Doppelpunkt"


def test_datum_ohne_doppelpunkt_nach_komma_in_der_kette():
    s = parse_namenskette("urspr.: Pottgasse, 07. Februar 1908 Kronenstraße.")
    assert [x.name for x in s] == ["Pottgasse", "Kronenstraße"]


def test_datum_ohne_doppelpunkt_tief_im_text_wird_ignoriert():
    """Ein Datum, dem ein Wort vorausgeht ('Am 25. Juli 1516 wurde …'), ist Prosa,
    kein Stadium — auch wenn kopf.rest es einmal enthalten sollte."""
    s = parse_namenskette("18. September 1926: St. Annental. Am 25. Juli 1516 Wurde")
    assert [x.name for x in s] == ["St. Annental"]


def test_datum_ohne_doppelpunkt_verlangt_grossgeschriebenen_namen():
    s = parse_namenskette("18. September 1926: St. Annental, 25. Juli 1516 wurde bei")
    assert [x.name for x in s] == ["St. Annental"]


def test_urspr_ohne_doppelpunkt():
    """Velberter Sträßchen 03203 (S. 330) 'urspr. Velberter Sträßchen.';
    Bocholder Straße 00379 (S. 72) 'urspr. Bocholder Landstraße, 30. April 1891: Hochstraße'."""
    s = parse_namenskette("urspr. Bocholder Landstraße, 30. April 1891: Hochstraße.")
    assert s[0].name == "Bocholder Landstraße"
    assert s[0].ist_urspruenglich is True
    assert s[0].hinweis == "urspr. ohne Doppelpunkt"
    assert s[1].name == "Hochstraße"


def test_jahrhundert_stadium():
    """Viehauser Berg, Schl.-Nr. 03213, S. 332."""
    s = parse_namenskette("16. Jahrh.: Viehauser Straße, 02. Juni 1922: Viehauser Berg.")
    assert (s[0].gueltig_ab, s[0].datum_praezision, s[0].name) == ("1501", "jahrhundert", "Viehauser Straße")


def test_numerisches_datum_stadium():
    s = parse_namenskette("29.08.1927: Schlenterstraße.")
    assert (s[0].gueltig_ab, s[0].name) == ("1927-08-29", "Schlenterstraße")
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_namen.py -q`
Expected: die neuen Tests FAIL (`'St'`, `'II'`, `AttributeError: 'Stadium' object has no attribute 'hinweis'`, `TypeError`), die alten PASS

- [ ] **Step 3: `namen.py` neu schreiben**

```python
# strassen/namen.py
"""Namensstadien mit Datum aus dem Kopfrest lesen.

Jedes Stadium ist ein Datum-Name-Paar. Fehlt das Datum ('urspr.:'), wird das im
Feld datum_praezision ausgewiesen — nicht geschätzt. Die Datumsformen und die
Satzende-Regel kommen aus strassen.datum (eine Quelle für kopf.py und namen.py).

'urspr.:' kann mehrfach in derselben Kette vorkommen (22 Einträge im Material,
z. B. Altenessener Straße Schl.-Nr. 00053) — alle Vorkommen werden erfasst und
nach Textposition einsortiert. 'urspr.' ohne Doppelpunkt (8 Fälle, z. B. Velberter
Sträßchen 03203) wird erkannt und mit Hinweis versehen.

Der Name endet an Komma/Semikolon oder an einem echten Satzende (datum.SATZENDE):
Abkürzungs-/Klammerpunkte ('St. Annental', 'II. Weberstraße', '(Verl.)') bleiben
Namensbestandteil.

Positionsregel für Stempel ohne Doppelpunkt (Spec Regel 15): Sie zählen nur, wenn
sie am Anfang von rest stehen oder direkt auf ein Komma folgen (Kettentrenner) UND
der Name großgeschrieben beginnt. Ein Datum, dem ein Wort vorausgeht ('Am 25. Juli
1516 wurde'), ist Prosa.
"""
import re
from typing import NamedTuple

from strassen.datum import DATUMSSTEMPEL_MUSTER, SATZENDE, MONATE, lese_datum

__all__ = ["MONATE", "Stadium", "parse_namenskette"]

_NAME = r"(?:(?!,|;|" + SATZENDE + r")[^\n]){1,80}"

_URSPR = re.compile(r"urspr\.(?P<trenner>:?)\s*(?P<name>" + _NAME + r")")
_STADIUM = re.compile(DATUMSSTEMPEL_MUSTER + r"\s*(?P<name>" + _NAME + r")")

HINWEIS_URSPR_OHNE_DOPPELPUNKT = "urspr. ohne Doppelpunkt"


class Stadium(NamedTuple):
    stadium: int
    gueltig_ab: str
    datum_praezision: str
    name: str
    ist_urspruenglich: bool
    hinweis: str = ""


def _position_erlaubt(rest: str, start: int) -> bool:
    """Für Stempel ohne regulären Doppelpunkt: Kettenanfang oder direkt nach Komma."""
    davor = rest[:start].rstrip()
    return davor == "" or davor.endswith(",")


def parse_namenskette(rest: str) -> list:
    roh = []

    for mu in _URSPR.finditer(rest):
        hinweis = "" if mu.group("trenner") == ":" else HINWEIS_URSPR_OHNE_DOPPELPUNKT
        roh.append((mu.start(), "", "unbekannt", mu.group("name").strip(), True, hinweis))

    for m in _STADIUM.finditer(rest):
        name = m.group("name").strip()
        d = lese_datum(m)
        if d.trenner != ":":
            if not _position_erlaubt(rest, m.start()) or not name[:1].isupper():
                continue
        roh.append((m.start(), d.gueltig_ab, d.praezision, name, False, d.hinweis))

    roh.sort(key=lambda x: x[0])
    return [Stadium(stadium=i, gueltig_ab=g, datum_praezision=p, name=n,
                     ist_urspruenglich=u, hinweis=h)
            for i, (_, g, p, n, u, h) in enumerate(roh, 1)]
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS. Schlägt ein alter Test in `test_namen.py` oder `test_kopf.py` fehl, prüfen, ob er altes Fehlverhalten festschreibt (z. B. einen an „St." gekappten Namen); dann Test anpassen und im Commit begründen. Schlägt etwas anderes fehl: Code, nicht Test.

- [ ] **Step 5: Commit**

```bash
git add strassen/namen.py tests/test_namen.py
git commit -m "namen.py: Datumslogik aus datum.py, Stadium.hinweis, urspr. ohne Doppelpunkt (Regeln 4, 15, 17)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `kopf.py` — Feldgrenzen, Fallback, Kettenabgrenzung, Marker-Varianten

**Files:**
- Modify: `strassen/kopf.py` (Konstanten `_M_STR`, `_M_KLASSE`, `_DATUM`, `_STADTTEIL`, `_KLASSE`, `_GRUPPE`, `_NAMENSTEIL`, `_STADIUM`; Funktionen `_stadienkette`, `parse_kopf`; `Kopf`)
- Test: `tests/test_kopf.py`

**Interfaces:**
- Consumes: `datum.DATUMSSTEMPEL_MUSTER`, `datum.SATZENDE`, `datum.MONATE`, `datum.lese_datum`
- Produces:
  - `class Kopf(NamedTuple): schl_nr, stadtteile, strassenklassen, namensgruppe, rest, hinweise: list = []` — **Achtung:** `NamedTuple` mit veränderlichem Default ist unschön; Default ist `()` (Tupel) und wird in `parse_kopf` als `tuple(hinweise)` gesetzt.
  - `parse_kopf(rumpf: str) -> Kopf | None` (Signatur unverändert)

- [ ] **Step 1: Failing Tests anhängen**

```python
# tests/test_kopf.py (anhängen)
from strassen.namen import parse_namenskette


def test_fallback_kappt_nicht_am_tagespunkt():
    """Kamerunstraße, Schl.-Nr. 01635, S. 188 — Goldstandard-Fehler: keine Kette.
    Die strenge Kettenerkennung scheitert, weil nach dem letzten Stadium ein Komma
    statt eines Punkts steht; der alte Fallback zerschnitt den Rest bei '26. '."""
    rumpf = ("01635, Stadtteil Gerschede, Str.-Kl.: Gemeindestraße, Str.-Gr.: Stadt und Ort, "
             "26. Mai 1939: Kamerunstraße, Kamerun, eine ehemalige deutsche Kolonie im Westen "
             "Zentralafrikas, nach 1918 französisches bzw. britisches Mandatsgebiet, seit 1961 "
             "unabhängige Republik. Siehe auch Askaristraße,")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Stadt und Ort"
    s = parse_namenskette(k.rest)
    assert [(x.gueltig_ab, x.name) for x in s] == [("1939-05-26", "Kamerunstraße")]


def test_feldgrenze_springt_nicht_auf_tagesziffer():
    """An der Blumenwiese, Schl.-Nr. 01552, S. 48: Namensgruppe endete bei '14'."""
    rumpf = ("01552, Stadtteil Kray, Str.-Kl.: Gemeindestraße, Str.-Gr.: Lagebezeichnung, "
             "14. Dezember 1999: An der Blumenwiese. Sie war eine von zwei Straßen.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Lagebezeichnung"
    assert parse_namenskette(k.rest)[0].gueltig_ab == "1999-12-14"


def test_komma_vor_datum_darf_fehlen():
    """Hirtsieferstraße, Schl.-Nr. 01316, S. 160: '… Stadtverordneter 01. Oktober 1920: …'"""
    rumpf = ("01316, Stadtteil Holsterhausen, Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, Mann, "
             "Deutscher, Politiker, Stadtverordneter 01. Oktober 1920: Mercatorstraße, "
             "29. August 1946: Hirtsieferstraße. Heinrich Hirtsiefer *1876.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Person, Mann, Deutscher, Politiker, Stadtverordneter"
    assert [x.gueltig_ab for x in parse_namenskette(k.rest)] == ["1920-10-01", "1946-08-29"]


def test_namensgruppe_endet_vor_verstuemmeltem_datum():
    """Overhammshof, Schl.-Nr. 02356, S. 254 (Seitenumbruch mit Rauschen): Namensgruppe
    war 'Hofname, 21'. Das Rauschen selbst entfernt Task 7; hier zählt nur die Grenze."""
    rumpf = ("02356, Stadtteil Fischlaken, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
             "21. Januar mm nm mm nn nn 1970: Overhammshof. Nach dem Hofe Overhamm.")
    assert parse_kopf(rumpf).namensgruppe == "Hofname"


def test_namensgruppe_endet_vor_stern_tagesziffer():
    """Eligiushöhe, Schl.-Nr. 00756, S. 106: '…, Heiliger, *03. Oktober 1932: Eligiushöhe'."""
    rumpf = ("00756, Stadtteil Kupferdreh, Str.-Kl.: Gemeindestraße, Str.-Gr.: Person, Mann, "
             "Deutscher, Bischof, Heiliger, *03. Oktober 1932: Eligiushöhe. Eligius war.")
    assert parse_kopf(rumpf).namensgruppe == "Person, Mann, Deutscher, Bischof, Heiliger"


def test_kette_mit_st_abkuerzung_bleibt_vollstaendig():
    """St. Annental, Schl.-Nr. 02727, S. 309."""
    rumpf = ("02727, Stadtteile Bergerhausen und Rellinghausen, Str.-Kl.: Gemeindestraße, "
             "Str.-Gr.: Kirche und Kloster, 04. Februar 1904: Kapellenstraße, 16. September 1910: "
             "Walpurgisstraße (tiw.), 18. September 1926: St. Annental. Am 25. Juli 1516 wurde bei "
             "Gelegenheit einer Kirmes aus der Rellinghauser Kirche ein Gefäß gestohlen.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("St. Annental.")
    assert [x.name for x in parse_namenskette(k.rest)][-1] == "St. Annental"


def test_marker_varianten_strassenklasse():
    """Adolfstraße 00015 'Str.-KL:', Amselweg 00265 'Str.-K.:', An den Friedhöfen 00150
    'Str.-Kt.:', Dachsfeld 00590 'Str:-Kl.:', Cäcilienstraße 00540 'Str.-Kl.;',
    Brandstorstraße 00421 'Str.-Kl.;:'."""
    for marker in ["Str.-KL:", "Str.-K.:", "Str.-Kt.:", "Str:-Kl.:", "Str.-Kl.;", "Str.-Kl.;:"]:
        rumpf = (f"00015, Stadtteil Rüttenscheid, {marker} Gemeindestraße, Str.-Gr.: "
                 "Männlicher Vorname, 06. September 1897: Adolfstraße.")
        k = parse_kopf(rumpf)
        assert k.strassenklassen == ["Gemeindestraße"], marker
        assert k.namensgruppe == "Männlicher Vorname", marker


def test_kopf_hat_hinweise_tupel():
    rumpf = "00127, Stadtteil Byfang, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, 31. März 1955: Am Schroer."
    assert parse_kopf(rumpf).hinweise == ()


def test_stadium_ohne_doppelpunkt_in_kette_wird_abgegrenzt():
    """Berghausbusch, Schl.-Nr. 00471, S. 84."""
    rumpf = ("00471, Stadtteil Kupferdreh, Str.-Kl.: Gemeindestraße, Str.-Gr.: Familienname, "
             "11. Dezember 1974 Berghausbusch. Jan Hendrich Berghaus war Bauer.")
    k = parse_kopf(rumpf)
    assert k.namensgruppe == "Familienname"
    assert [x.name for x in parse_namenskette(k.rest)] == ["Berghausbusch"]


def test_prosa_datum_nach_kette_wird_nicht_angehaengt():
    """Kein Stadium aus 'Am 25. Juli 1516 Wurde' (Wort vor dem Datum)."""
    rumpf = ("02727, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Kirche, "
             "18. September 1926: St. Annental. Am 25. Juli 1516 Wurde bei Gelegenheit.")
    k = parse_kopf(rumpf)
    assert k.rest.endswith("St. Annental.")
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_kopf.py -q`
Expected: neue Tests FAIL, alte PASS

- [ ] **Step 3: `kopf.py` anpassen**

Ersetze in `strassen/kopf.py` den Import und die Konstanten ab `_M_STR` bis einschließlich `_MAX_LUECKE`, sowie `Kopf`, `_stadienkette` und `parse_kopf`:

```python
# Import ersetzen:
from strassen.datum import DATUMSSTEMPEL_MUSTER, SATZENDE, lese_datum

# Konstanten (ersetzen; die erläuternden Kommentare der alten Fassung zu _NUMMER,
# _M_STR/_M_GRUPPE, _STADTTEIL, _MARKER_FRAGMENT bleiben erhalten):
# 'S[tl]r?[.:]?' toleriert zusätzlich 'Str:-Kl' (Dachsfeld 00590, S. 90).
_M_STR = r"S[tl]r?[.:]?\s*-?\s*"
# Klassen-Marker: 'Kl', 'KI', 'KL' (Adolfstraße 00015 u. a., 4 Fälle), 'K.' (Amselweg
# 00265, 9 Fälle), 'Kt' (An den Friedhöfen 00150, 2 Fälle); Trenner ':' oder ';',
# auch doppelt ('Str.-Kl.;:', Brandstorstraße 00421). 8 Fälle mit ';' ließen die
# Straßenklasse bisher leer (Goldstandard: Cäcilienstraße 00540).
_M_KLASSE = _M_STR + r"K[lILt]?\.?\s*[:;]+"
_M_GRUPPE = _M_STR + r"Gr?\.?\s*[:;]"

# Feldende: ein Punkt mit Leerzeichen, der NICHT auf eine Ziffer folgt — sonst
# springt die Grenze auf die Tagesziffer eines Datums ('14. Dezember', An der
# Blumenwiese 01552; 46 Namensgruppen im Material endeten so auf einer Zahl).
_FELDENDE = r"(?<!\d)\.\s"
# Namensgruppe endet außerdem vor einer Tagesziffer (mit optionalem OCR-Stern
# '*03.', Eligiushöhe 00756) — auch dann, wenn das Datum dahinter verstümmelt ist
# (Overhammshof 02356: '21. Januar mm nm …'). So bleibt die Namensgruppe sauber und
# das kaputte Datum landet sichtbar im Rest statt unsichtbar in der Gruppe.
_TAGESZIFFER = r",?\s*\*?\d{1,3}[.,]\s"

_STADTTEIL = re.compile(
    r"Stadtteile?\s+(.+?)(?=,?\s*" + _M_KLASSE + r"|,?\s*" + _M_GRUPPE + r"|" + _FELDENDE + r"|$)"
)
_KLASSE = re.compile(_M_KLASSE + r"\s*(.+?)(?=,?\s*" + _M_GRUPPE + r"|" + _FELDENDE + r"|$)")
_GRUPPE = re.compile(
    _M_GRUPPE + r"\s*(.+?)"
    r"(?=,?\s*(?:urspr\.|" + DATUMSSTEMPEL_MUSTER + r")|" + _TAGESZIFFER + r"|" + _FELDENDE + r"|$)"
)
# Namensteil eines Stadiums in der strengen Kettenerkennung: keine Ziffern, endet am
# gemeinsamen Satzende (datum.SATZENDE — Abkürzungspunkte 'St.', 'II.' zählen nicht).
_NAMENSTEIL = r"(?:(?!" + SATZENDE + r")[^\d\n]){1,80}"
_STADIUM = re.compile(DATUMSSTEMPEL_MUSTER + r"\s*(?P<name>" + _NAMENSTEIL + r")" + SATZENDE)
_SATZENDE = re.compile(SATZENDE)
_MAX_LUECKE = 40


class Kopf(NamedTuple):
    schl_nr: str
    stadtteile: list
    strassenklassen: list
    namensgruppe: str
    rest: str
    hinweise: tuple = ()


def _position_erlaubt(schwanz: str, start: int) -> bool:
    davor = schwanz[:start].rstrip()
    return davor == "" or davor.endswith(",")


def _stadienkette(schwanz: str) -> list:
    """Nur eine ununterbrochene Kette von Stadien direkt nach dem Kopfbereich
    akzeptieren (Lücke ≤ _MAX_LUECKE). Stempel ohne regulären Doppelpunkt zählen nur
    am Kettenanfang oder nach Komma und mit großgeschriebenem Namen (Spec Regel 15) —
    dieselbe Positionsregel wie namen.parse_namenskette."""
    kette = []
    for t in _STADIUM.finditer(schwanz):
        if t.group("trenner") != ":":
            if not _position_erlaubt(schwanz, t.start()) or not t.group("name").strip()[:1].isupper():
                continue
        if kette and t.start() - kette[-1].end() > _MAX_LUECKE:
            break
        kette.append(t)
    return kette


def parse_kopf(rumpf: str):
    m = _NUMMER.match(rumpf)
    if not m:
        return None
    ziffern = m.group(1).replace(" ", "")
    if not (1 <= len(ziffern) <= 5):
        return None
    schl_nr = ziffern.zfill(5)
    hinweise = []

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

    start = mg.end() if mg else (mk.end() if mk else m.end())
    schwanz = rumpf[start:]
    stadien = _stadienkette(schwanz)
    if stadien:
        rest = schwanz[:stadien[-1].end()]
    else:
        # Fallback: bis zum ersten echten Satzende — NICHT bis zum ersten '. ', das
        # die Tagesziffer eines sauber gedruckten Datums traf (38 Namensketten im
        # Material, Goldstandard: Kamerunstraße 01635).
        ms_ende = _SATZENDE.search(schwanz)
        rest = schwanz[:ms_ende.end()] if ms_ende else schwanz

    return Kopf(schl_nr=schl_nr, stadtteile=stadtteile, strassenklassen=klassen,
                namensgruppe=gruppe, rest=rest.strip(), hinweise=tuple(hinweise))
```

Entferne `from strassen.namen import MONATE` und die alte `_MONAT`/`_DATUM`-Definition aus `kopf.py`.

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS. Ein möglicherweise fehlschlagender Alt-Test ist `test_kopf.py::test_fehlende_strassenklasse_ergibt_leere_liste` — er bleibt gültig (kein Klassenwort im Text) und muss weiter PASS liefern; falls nicht, liegt der Fehler im Code.

- [ ] **Step 5: Commit**

```bash
git add strassen/kopf.py tests/test_kopf.py
git commit -m "kopf.py: Fallback und Feldgrenzen ohne Tagesziffer-Falle, Kette über datum.py, Marker-Varianten (Regeln 1, 2, 3, 9)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: `kopf.py` — Klassenwort ohne Marker und OCR-korrigierter Klassenwert

**Files:**
- Modify: `strassen/kopf.py` (`parse_kopf`, neue Konstanten `STRASSENKLASSEN`, `_KLASSENWORT`)
- Test: `tests/test_kopf.py`

**Interfaces:**
- Consumes: `datum.unscharf_eindeutig`
- Produces: Hinweistexte `"Straßenklasse ohne Marker"`, `"Straßenklasse OCR-korrigiert"` in `Kopf.hinweise`; `STRASSENKLASSEN: tuple[str, ...]`

- [ ] **Step 1: Failing Tests anhängen**

```python
# tests/test_kopf.py (anhängen)

def test_klassenwort_ohne_marker_wird_uebernommen_mit_hinweis():
    """Eibergweg, Schl.-Nr. 00733, S. 105: '…, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: …'
    (13 Fälle im Material; geschlossenes Vokabular)."""
    rumpf = ("00733, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: Stadt und Ort, "
             "20. November 1937: Eibergweg.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.stadtteile == ["Freisenbruch"]
    assert "Straßenklasse ohne Marker" in k.hinweise


def test_klassenwort_ohne_marker_mehrere():
    rumpf = ("00905, Stadtteile Freisenbruch und Steele, Landstraße, Gemeindestraße, Str.-Gr.: "
             "Stadt und Ort, 01. Januar 1900: Freisenbruchstraße.")
    assert parse_kopf(rumpf).strassenklassen == ["Landstraße", "Gemeindestraße"]


def test_klassenwort_ohne_marker_nur_zwischen_stadtteil_und_gruppe():
    """Ein Klassenwort erst in der Namenskette ('… 1901: Hauptstraße') zählt nicht."""
    rumpf = ("00127, Stadtteil Byfang, Str.-Gr.: Flurname, 31. März 1955: Hauptstraße.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == []
    assert k.hinweise == ()


def test_klassenwert_mit_ocr_fehler_wird_korrigiert():
    """Auf der Bredde, Schl.-Nr. 00210, S. 57: 'Str.-Kl.: Gemeindstraße' (5 Fälle)."""
    rumpf = ("00210, Stadtteil Frillendorf, Str.-Kl.: Gemeindstraße, Str.-Gr.: Flurname, "
             "01. August 1921: Auf der Bredde.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeindestraße"]
    assert k.hinweise == ("Straßenklasse OCR-korrigiert",)


def test_klassenwert_mit_zwei_fehlern_bleibt_wie_gelesen():
    rumpf = ("00210, Stadtteil Frillendorf, Str.-Kl.: Gemeidstrase, Str.-Gr.: Flurname, "
             "01. August 1921: Auf der Bredde.")
    k = parse_kopf(rumpf)
    assert k.strassenklassen == ["Gemeidstrase"]
    assert k.hinweise == ()
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_kopf.py -q`
Expected: neue Tests FAIL

- [ ] **Step 3: Implementieren**

In `strassen/kopf.py` ergänzen (Import erweitern um `unscharf_eindeutig`), Konstanten nach `_MARKER_FRAGMENT`:

```python
from strassen.datum import DATUMSSTEMPEL_MUSTER, SATZENDE, lese_datum, unscharf_eindeutig

# Geschlossenes Vokabular der Straßenklassen (Auszählung strassen.csv 2026-09-11:
# Gemeindestraße 3.059, Landstraße 93, Kreisstraße 39, Hauptstraße 22, Bundesstraße 15;
# Mehrfachnennungen als Kombinationen daraus). Fehlt der Marker 'Str.-Kl.:' ganz, aber
# ein Wort aus diesem Vokabular steht zwischen Stadtteil-Angabe und 'Str.-Gr.:', wird
# es übernommen — mit Hinweis, weil der Marker fehlt (13 Fälle, z. B. Eibergweg 00733).
STRASSENKLASSEN = ("Gemeindestraße", "Kreisstraße", "Landstraße", "Hauptstraße",
                   "Bundesstraße")
_KLASSENWORT = re.compile(r"\b(" + "|".join(STRASSENKLASSEN) + r")\b")

HINWEIS_KLASSE_OHNE_MARKER = "Straßenklasse ohne Marker"
HINWEIS_KLASSE_KORRIGIERT = "Straßenklasse OCR-korrigiert"
```

In `parse_kopf` den Block `klassen = []` … ersetzen durch:

```python
    klassen = []
    mk = _KLASSE.search(rumpf)
    if mk:
        klassen = _teile(mk.group(1))

    gruppe = ""
    mg = _GRUPPE.search(rumpf)
    if mg:
        gruppe = mg.group(1).strip().rstrip(",")

    if not klassen and mg:
        # Regel 19: Klassenwort ohne Marker, nur im Bereich vor 'Str.-Gr.:'
        bereich_start = ms.end() if ms else m.end()
        gefunden = _KLASSENWORT.findall(rumpf[bereich_start:mg.start()])
        if gefunden:
            klassen = gefunden
            hinweise.append(HINWEIS_KLASSE_OHNE_MARKER)

    # Regel 20: ein OCR-Fehler im Klassenwert ('Gemeindstraße') wird auf das
    # Vokabular korrigiert, mit Hinweis; zwei Fehler bleiben wie gelesen.
    korrigiert = []
    for klasse in klassen:
        if klasse in STRASSENKLASSEN:
            korrigiert.append(klasse)
            continue
        kandidat = unscharf_eindeutig(klasse, STRASSENKLASSEN)
        if kandidat:
            korrigiert.append(kandidat)
            if HINWEIS_KLASSE_KORRIGIERT not in hinweise:
                hinweise.append(HINWEIS_KLASSE_KORRIGIERT)
        else:
            korrigiert.append(klasse)
    klassen = korrigiert
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/kopf.py tests/test_kopf.py
git commit -m "kopf.py: Klassenwort ohne Marker und OCR-korrigierter Klassenwert mit Hinweis (Regeln 19, 20)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: `segmentierung.py` — Lemma mit „St. "-Abkürzung

**Files:**
- Modify: `strassen/segmentierung.py` (`_LEMMA`)
- Test: `tests/test_segmentierung.py`

**Interfaces:**
- Produces: unverändert `segmentiere(seiten, verworfene=None) -> list[Eintrag]`

- [ ] **Step 1: Failing Test anhängen**

```python
# tests/test_segmentierung.py (anhängen)

def test_lemma_mit_st_abkuerzung_und_leerzeichen():
    """St. Annental, Schl.-Nr. 02727, S. 309 — Goldstandard-Fehler: Lemma war 'Annental'.
    15 Lemmata im Material beginnen mit 'St. ' (Leerzeichen, nicht Bindestrich)."""
    seiten = [(309, "Lit.: Herbert Steinhardt. In: Das Münster am Hellweg 1975, S. 139 ff. "
                    "St. Annental: Schl.-Nr.: 02727, Stadtteile Bergerhausen und Rellinghausen, "
                    "Str.-Kl.: Gemeindestraße.")]
    eintraege = segmentiere(seiten)
    assert eintraege[0].lemma_roh == "St. Annental"


def test_lemma_mit_st_bindestrich_bleibt():
    seiten = [(309, "Text. St.-Ingbert-Höhe: Schl.-Nr.: 02728, Stadtteil Leithe.")]
    assert segmentiere(seiten)[0].lemma_roh == "St.-Ingbert-Höhe"


def test_lemma_endet_weiterhin_am_satzpunkt():
    seiten = [(211, "Erläuterung endet hier. Kruselbeek: Schl.-Nr.: 01827, Stadtteil Fischlaken.")]
    assert segmentiere(seiten)[0].lemma_roh == "Kruselbeek"
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_segmentierung.py -q`
Expected: erster Test FAIL mit `'Annental'`

- [ ] **Step 3: `_LEMMA` anpassen**

```python
# strassen/segmentierung.py — _LEMMA ersetzen; Kommentar davor ergänzen:
# … Ein Punkt nach 'St' ('St. Annental', 15 Lemmata im Material) ist ebenfalls
# Abkürzungspunkt und beendet die Rückwärtssuche nicht (Goldstandard 02727).
_LEMMA = re.compile(
    r"((?:(?!,|;|:|(?<!\bSt)\.(?!-|[A-Za-zÄÖÜäöüß]))[^\n]){2,60}?)\s*:\s*$"
)
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/segmentierung.py tests/test_segmentierung.py
git commit -m "segmentierung.py: 'St. X' mit Leerzeichen als Lemma (Regel 5)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: `aufbereitung.py` — Abschnittskopf klein, Randrauschen, Stadtteil-Marker, `xundX`

**Files:**
- Modify: `strassen/aufbereitung.py` (`_ABSCHNITTSKOPF`, neue `_RANDRAUSCHEN`, `_STADTTEIL_MARKER`, `_UND_KLEBT`; `bereinige`, `verbinde_zeilen`)
- Test: `tests/test_aufbereitung.py`

**Interfaces:**
- Produces: unverändert `bereinige(text) -> str`, `verbinde_zeilen(text) -> str`, `aufbereiten(verzeichnis) -> list[(nr, text)]`

- [ ] **Step 1: Failing Tests anhängen**

```python
# tests/test_aufbereitung.py (anhängen)

def test_abschnittskopf_als_kleinbuchstabe_wird_entfernt():
    """S. 87: OCR las den Abschnittskopf 'C' als 'c' — Lemma wurde 'c Cäcilienstraße'
    (Goldstandard 00540). 29 Einzel-Kleinbuchstaben-Zeilen im Material, 28 davon Rauschen."""
    roh = "Gefangenschaft).\n\nc\n\nCäcilienstraße: Sch!.-Nr.: 00540, Stadtteil Rüttenscheid,"
    sauber = bereinige(roh)
    assert "\nc\n" not in sauber
    assert "Cäcilienstraße" in sauber


def test_randrauschen_letzte_zeile_wird_entfernt():
    """S. 254 endet mit 'mm nm mm nn nn' (Scanrand), mitten im Kopf von Overhammshof 02356."""
    roh = "Overhammshof: Schl.-Nr.: 02356, Stadtteil Fischlaken,\nStr.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, 21. Januar\n\nmm nm mm nn nn\n"
    sauber = bereinige(roh)
    assert "mm nm" not in sauber
    assert "21. Januar" in sauber


def test_randrauschen_erste_zeile_wird_entfernt():
    roh = "Vs u\n\nAachener Straße: Schl.-Nr.: 00001, Stadtteil Frohnhausen"
    assert "Vs u" not in bereinige(roh)


def test_randrauschen_greift_nicht_mitten_im_text():
    roh = "Aachener Straße: Schl.-Nr.: 00001,\nan der A\nStadtteil Frohnhausen, Str.-Kl.: Gemeindestraße."
    assert "an der A" in bereinige(roh)


def test_legitime_kurze_randzeile_bleibt():
    """Zeilen mit Ziffer oder Satzzeichen ('S. 33.', 'Hude.', '18.') sind kein Rauschen."""
    for zeile in ["1886, 5. 33.", "Hude.", "18."]:
        roh = f"Text davor.\n{zeile}\n"
        assert zeile in bereinige(roh), zeile


def test_stadtteil_marker_varianten_werden_normalisiert():
    """Am Stoppenberger Bach 01615 'Stadt-teil', Auf der Bucht 00211 'Stadttei!',
    Diestweg 02505 'Stadteil', Schönscheidts Hof 02812 'Stadttteil', In der Nähe der
    Armin… 02874 'Stadtteit', AmWasserturm 00268 'StadtteilBurgaltendorf',
    Manderscheidtstraße 02191 'Stadt-teile' (Goldstandard)."""
    faelle = {
        "01615, Stadt-teil Stoppenberg, Str.-Kl.:": "Stadtteil Stoppenberg",
        "00211, Stadttei! Heisingen, Str.-Kl.:": "Stadtteil Heisingen",
        "02505, Stadteil Bochold, Str.-Kl.:": "Stadtteil Bochold",
        "02812, Stadttteil Kray, Str.-Kl.:": "Stadtteil Kray",
        "02874, Stadtteit Nordviertel, Str.-Kl.:": "Stadtteil Nordviertel",
        "00268, StadtteilBurgaltendorf, Str.-Kl.:": "Stadtteil Burgaltendorf",
        "02191, Stadt-teile FrillendorfundStoppenberg, Str.-Kl.:": "Stadtteile Frillendorf und Stoppenberg",
    }
    for roh, erwartet in faelle.items():
        assert erwartet in verbinde_zeilen(roh), roh


def test_stadtteilen_in_prosa_bleibt_unangetastet():
    assert "Stadtteilen" in verbinde_zeilen("in den Stadtteilen Kray und Leithe")


def test_und_zwischen_klein_und_gross_wird_getrennt():
    assert verbinde_zeilen("FrillendorfundStoppenberg") == "Frillendorf und Stoppenberg"
    assert verbinde_zeilen("Hundstraße") == "Hundstraße"
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_aufbereitung.py -q`
Expected: neue Tests FAIL

- [ ] **Step 3: Implementieren**

```python
# strassen/aufbereitung.py — Konstanten ersetzen/ergänzen:

# Abschnittskopf: auch ein einzelner Kleinbuchstabe (OCR las 'C' als 'c', S. 87 —
# Goldstandard 00540 'c Cäcilienstraße'). Von 29 solchen Zeilen im Material ist
# eine ein echter Abschnittskopf, 28 sind Randrauschen; beides darf weg.
_ABSCHNITTSKOPF = re.compile(
    r"^[ \t]*[A-Za-zÄÖÜäöü](?:[ \t]*,[ \t]*[A-ZÄÖÜ])?[ \t]*$", re.MULTILINE)
# Randrauschen (Scanrand, 36 Seiten): eine Zeile nur aus Wörtern mit ≤3 Buchstaben,
# ohne Ziffer und Satzzeichen ('mm nm mm nn nn', 'EEE EEE', 'Vs u'). Wird NUR als
# erste oder letzte nichtleere Zeile einer Seite entfernt — mitten im Text könnte
# eine solche Zeile ('an der A') legitim sein.
_RANDRAUSCHEN = re.compile(r"^\s*(?:[A-Za-zÄÖÜäöüß]{1,3}\s+)*[A-Za-zÄÖÜäöüß]{1,3}\s*$")
# Stadtteil-Marker-Varianten (13 der 14 leeren Stadtteil-Felder): 'Stadt-teil',
# 'Stadttei!', 'Stadteil', 'Stadttteil', 'Stadtteit', 'StadtteilX' ohne Leerzeichen.
# Lookahead verlangt Leerzeichen/Großbuchstabe/Bindestrich danach, damit
# 'Stadtteilen' in der Prosa unangetastet bleibt.
_STADTTEIL_MARKER = re.compile(r"Stadt-?t{0,2}ei[l!t](?P<pl>e?)-?(?=[ \tA-ZÄÖÜ])")
# OCR-Blocksatz klebt 'und' zwischen zwei Namen zusammen ('FrillendorfundStoppenberg',
# Manderscheidtstraße 02191 — Goldstandard). Nur Klein-und-Groß, nie innerhalb
# eines Wortes wie 'Hundstraße'.
_UND_KLEBT = re.compile(r"([a-zäöüß])und([A-ZÄÖÜ])")


def _entferne_randrauschen(text: str) -> str:
    zeilen = text.split("\n")
    nichtleer = [i for i, z in enumerate(zeilen) if z.strip()]
    if not nichtleer:
        return text
    for i in {nichtleer[0], nichtleer[-1]}:
        if _RANDRAUSCHEN.match(zeilen[i]):
            zeilen[i] = ""
    return "\n".join(zeilen)


def bereinige(text: str) -> str:
    text = _KOLUMNENTITEL.sub("", text)
    text = _SEITENZAHL.sub("", text)
    text = _ABSCHNITTSKOPF.sub("", text)
    return _entferne_randrauschen(text)


def verbinde_zeilen(text: str) -> str:
    for muster, ersatz in _MARKER:
        text = muster.sub(ersatz, text)
    text = _OCR_FEHLER.sub(r"\1ß", text)
    text = _TRENNUNG.sub("", text)
    text = text.replace("\n", " ")
    text = _STADTTEIL_MARKER.sub(lambda m: "Stadtteil" + m.group("pl") + " ", text)
    text = _UND_KLEBT.sub(r"\1 und \2", text)
    return re.sub(r"\s+", " ", text).strip()
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/aufbereitung.py tests/test_aufbereitung.py
git commit -m "aufbereitung.py: Abschnittskopf klein, Randrauschen, Stadtteil-Marker, 'xundX' (Regeln 10–13)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: `erschliessen.py` — Hinweise als Prüfgründe, leere Kopffelder

**Files:**
- Modify: `strassen/erschliessen.py` (Moduldoc, `main`)
- Test: `tests/test_erschliessen.py`

**Interfaces:**
- Consumes: `Stadium.hinweis` (Task 3), `Kopf.hinweise` (Task 4/5)
- Produces: neue Werte in `pruefung.csv`-Spalte `grund`: jeder Hinweistext wörtlich, dazu `"Stadtteil fehlt"`, `"Straßenklasse fehlt"`

- [ ] **Step 1: Failing Tests anhängen**

Die bestehenden Tests in `test_erschliessen.py` schreiben OCR-Seiten nach `tmp_path` und rufen `main(ocr_dir=..., ausgabe_dir=...)`. Dasselbe Muster (Hilfsfunktion nachsehen, z. B. wie in `test_auffaelliges_lemma_wird_gekennzeichnet_aber_trotzdem_aufgenommen`) hier verwenden:

```python
# tests/test_erschliessen.py (anhängen)
import csv as _csv


def _lauf(tmp_path, seitentext, nummer=100):
    ocr = tmp_path / "ocr"
    ocr.mkdir()
    (ocr / f"s{nummer:03d}.txt").write_text(seitentext, encoding="utf-8")
    aus = tmp_path / "daten"
    main(ocr_dir=str(ocr), ausgabe_dir=str(aus))
    strassen = list(_csv.DictReader(open(aus / "strassen.csv", encoding="utf-8")))
    pruefung = list(_csv.DictReader(open(aus / "pruefung.csv", encoding="utf-8")))
    return strassen, pruefung


def test_datums_hinweis_wird_pruefgrund_und_unsicher(tmp_path):
    """Eskenshof, Schl.-Nr. 00817, S. 110: '13, Juni 1973: Eskenshof'."""
    strassen, pruefung = _lauf(tmp_path,
        "Eskenshof: Schl.-Nr.: 00817, Stadtteil Überruhr-Holthausen, Str.-Kl.: Gemeindestraße, "
        "Str.-Gr.: Hofname, 13, Juni 1973: Eskenshof. Nach dem Behandigungsgut Esken.\n")
    assert strassen[0]["status"] == "unsicher"
    assert [z["grund"] for z in pruefung] == ["Datum: Komma nach Tag"]


def test_kopf_hinweis_wird_pruefgrund(tmp_path):
    strassen, pruefung = _lauf(tmp_path,
        "Eibergweg: Schl.-Nr.: 00733, Stadtteil Freisenbruch, Gemeindestraße, Str.-Gr.: "
        "Stadt und Ort, 20. November 1937: Eibergweg. Erläuterung.\n")
    assert strassen[0]["strassenklasse"] == "Gemeindestraße"
    assert strassen[0]["status"] == "unsicher"
    assert "Straßenklasse ohne Marker" in [z["grund"] for z in pruefung]


def test_mehrere_hinweise_eines_stadiums_werden_einzelne_gruende(tmp_path):
    strassen, pruefung = _lauf(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Stadtteil X, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
        "13, Novemner 1900: Testweg. Erläuterung.\n")
    gruende = sorted(z["grund"] for z in pruefung)
    assert gruende == ["Datum: Komma nach Tag", "Monatsname OCR-korrigiert"]


def test_leerer_stadtteil_wird_pruefgrund(tmp_path):
    """Manderscheidtstraße 02191 (Goldstandard) war trotz leerem Stadtteil 'automatisch'."""
    strassen, pruefung = _lauf(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Str.-Kl.: Gemeindestraße, Str.-Gr.: Hofname, "
        "01. Januar 1900: Testweg. Erläuterung.\n")
    assert strassen[0]["status"] == "unsicher"
    assert "Stadtteil fehlt" in [z["grund"] for z in pruefung]


def test_leere_strassenklasse_wird_pruefgrund(tmp_path):
    strassen, pruefung = _lauf(tmp_path,
        "Testweg: Schl.-Nr.: 00001, Stadtteil X, Str.-Gr.: Hofname, "
        "01. Januar 1900: Testweg. Erläuterung.\n")
    assert "Straßenklasse fehlt" in [z["grund"] for z in pruefung]


def test_reiner_verweis_eintrag_ohne_klasse_bleibt_automatisch(tmp_path):
    """Grendgasse 01078 (S. 142): '…, Str.-Gr.: X. Siehe Grendplatz.' — kein Stadium,
    Verweis im Kopf; fehlende Felder sind hier kein Parserfehler."""
    strassen, pruefung = _lauf(tmp_path,
        "Grendgasse: Schl.-Nr.: 01078, Stadtteil Stadtkern, Str.-Gr.: Essener Geschichte. "
        "Siehe Grendplatz.\n")
    assert strassen[0]["verweis_auf"] == "Grendplatz"
    assert "Straßenklasse fehlt" not in [z["grund"] for z in pruefung]
    assert strassen[0]["status"] == "automatisch"
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_erschliessen.py -q`
Expected: neue Tests FAIL

- [ ] **Step 3: `main` ergänzen**

In `strassen/erschliessen.py`, im Block `gruende = []` nach `"Feld auffällig (Länge)"`:

```python
        # Toleranz-Hinweise aus Kopf und Stadien werden wörtlich zu Prüfgründen
        # (Spec 2026-09-11, Regeln 6, 14–20): Wert übernommen UND gekennzeichnet.
        for hinweis in k.hinweise:
            if hinweis not in gruende:
                gruende.append(hinweis)
        for s in stadien:
            for hinweis in filter(None, s.hinweis.split("; ")):
                if hinweis not in gruende:
                    gruende.append(hinweis)
        # Leere Kopffelder (Regel 21): im Druck hat praktisch jeder Eintrag Stadtteil
        # und Straßenklasse; fehlt eines, hat der Parser versagt. Ausnahme: reiner
        # Verweis-Eintrag (Siehe im Kopf, keine Namenskette), z. B. Grendgasse 01078.
        reiner_verweis = bool(mv_kopf) and not stadien
        if not k.stadtteile and not reiner_verweis:
            gruende.append("Stadtteil fehlt")
        if not k.strassenklassen and not reiner_verweis:
            gruende.append("Straßenklasse fehlt")
```

Moduldoc um die neuen Gründe ergänzen (je eine Zeile in der bestehenden Liste):

```
  - Hinweise aus datum.py/kopf.py wörtlich ("Datum: Komma nach Tag", "Datum ohne
    Doppelpunkt", "Monatsname OCR-korrigiert", "Datum: Doppeljahr", "Datum: Tag
    ungültig", "urspr. ohne Doppelpunkt", "Straßenklasse ohne Marker",
    "Straßenklasse OCR-korrigiert"): tolerant erkannter Wert, übernommen und markiert.
  - "Stadtteil fehlt" / "Straßenklasse fehlt": Kopffeld leer, obwohl kein reiner
    Verweis-Eintrag.
```

- [ ] **Step 4: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS. `test_erschliessen.py::test_normaler_eintrag_bleibt_automatisch` und `test_kennzahlen_gesamtlauf` müssen weiter PASS liefern — falls deren Fixture keinen Stadtteil/keine Klasse enthält, Fixture um `Stadtteil X, Str.-Kl.: Gemeindestraße` ergänzen und im Commit begründen.

- [ ] **Step 5: Commit**

```bash
git add strassen/erschliessen.py tests/test_erschliessen.py
git commit -m "erschliessen.py: Toleranz-Hinweise als Prüfgründe, leere Kopffelder markiert (Regel 21)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: Schema — Präzision `jahrhundert`

**Files:**
- Modify: `datapackage.json:40` (enum), `README.md:120` und `README.md:148`, `docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md:170`
- Test: `tests/test_datapackage.py`

**Interfaces:**
- Produces: enum `["tag", "monat", "jahr", "jahrhundert", "vor", "nach", "unbekannt"]`

- [ ] **Step 1: Failing Test anhängen**

```python
# tests/test_datapackage.py (anhängen)
import json
from pathlib import Path


def test_datum_praezision_enum_enthaelt_jahrhundert():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    namen = next(r for r in paket["resources"] if r["name"] == "namen")
    feld = next(f for f in namen["schema"]["fields"] if f["name"] == "datum_praezision")
    assert "jahrhundert" in feld["constraints"]["enum"]
```

(Falls die Ressource anders heißt: `python3 -c "import json;print([r['name'] for r in json.load(open('datapackage.json'))['resources']])"` — den Namen der `namen.csv`-Ressource verwenden.)

- [ ] **Step 2: Test laufen lassen**

Run: `python3 -m pytest tests/test_datapackage.py -q`
Expected: FAIL

- [ ] **Step 3: Schema und Doku ändern**

`datapackage.json`, Zeile 40: `"enum": ["tag", "monat", "jahr", "jahrhundert", "vor", "nach", "unbekannt"]`

`README.md`, Zeile 120 (Feldtabelle `namen.csv`):
```
| `datum_praezision` | Genauigkeit der Datierung | `tag` \| `monat` \| `jahr` \| `jahrhundert` (nur Jahrhundert bekannt; `gueltig_ab` = erstes Jahr, z. B. 16. Jh. → 1501) \| `vor` \| `nach` \| `unbekannt` |
```

`README.md`, Zeile 119 (`gueltig_ab`): `ISO-Datum, Jahr, erstes Jahr eines Jahrhunderts bei `jahrhundert`, oder leer bei `unbekannt``

`docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md`, Zeile 170: dieselbe Werteliste wie im README.

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add datapackage.json README.md docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md tests/test_datapackage.py
git commit -m "Schema: datum_praezision 'jahrhundert' (Regel 8)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: `strassen/differenz.py` — Vergleich zweier Datenstände

**Files:**
- Create: `strassen/differenz.py`
- Test: `tests/test_differenz.py`

**Interfaces:**
- Produces:
  - `vergleiche(alt_dir, neu_dir) -> dict` mit Schlüsseln `stadium_gewonnen, stadium_verloren, datum_veraendert, name_veraendert, kopffeld_veraendert, status_zu_unsicher, status_zu_automatisch, eintrag_neu, eintrag_entfallen` (je Liste von dicts mit `schl_nr`, `lemma` und fallabhängigen Feldern `alt`, `neu`, `feld`)
  - `formatiere_bericht(diff: dict) -> str` (Markdown)
  - CLI: `python3 -m strassen.differenz <alt_dir> <neu_dir> [--ausgabe PFAD]`

- [ ] **Step 1: Failing Tests schreiben**

```python
# tests/test_differenz.py
import csv
from pathlib import Path

from strassen.differenz import vergleiche, formatiere_bericht

_S = ["schl_nr", "lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf", "buchseite", "status"]
_N = ["schl_nr", "stadium", "gueltig_ab", "datum_praezision", "name", "ist_urspruenglich"]


def _schreibe(d: Path, strassen, namen):
    d.mkdir(parents=True, exist_ok=True)
    for name, felder, zeilen in [("strassen.csv", _S, strassen), ("namen.csv", _N, namen)]:
        with open(d / name, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=felder)
            w.writeheader()
            w.writerows(zeilen)


def _s(schl, lemma, status="automatisch", **k):
    z = {"schl_nr": schl, "lemma": lemma, "stadtteile": "X", "strassenklasse": "Gemeindestraße",
         "namensgruppe": "Hofname", "verweis_auf": "", "buchseite": "1", "status": status}
    z.update(k)
    return z


def _n(schl, stadium, datum, name, praez="tag"):
    return {"schl_nr": schl, "stadium": str(stadium), "gueltig_ab": datum,
            "datum_praezision": praez, "name": name, "ist_urspruenglich": "falsch"}


def test_stadium_gewonnen_und_verloren(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A"), _s("2", "B")],
              [_n("2", 1, "1900-01-01", "Alt")])
    _schreibe(tmp_path / "neu", [_s("1", "A"), _s("2", "B")],
              [_n("1", 1, "1939-05-26", "Kamerunstraße")])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["stadium_gewonnen"] == [{"schl_nr": "1", "lemma": "A", "neu": "1939-05-26 Kamerunstraße"}]
    assert d["stadium_verloren"] == [{"schl_nr": "2", "lemma": "B", "alt": "1900-01-01 Alt"}]


def test_datum_und_name_veraendert(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [_n("1", 1, "1920", "II", "jahr")])
    _schreibe(tmp_path / "neu", [_s("1", "A")], [_n("1", 1, "1920-10-01", "II. Weberstraße")])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["datum_veraendert"] == [{"schl_nr": "1", "lemma": "A", "stadium": "1",
                                      "alt": "1920 (jahr)", "neu": "1920-10-01 (tag)"}]
    assert d["name_veraendert"] == [{"schl_nr": "1", "lemma": "A", "stadium": "1",
                                     "alt": "II", "neu": "II. Weberstraße"}]


def test_kopffeld_und_status(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A", stadtteile=""), _s("2", "B", status="unsicher")], [])
    _schreibe(tmp_path / "neu", [_s("1", "A", stadtteile="Kray", status="unsicher"), _s("2", "B")], [])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["kopffeld_veraendert"] == [{"schl_nr": "1", "lemma": "A", "feld": "stadtteile",
                                         "alt": "", "neu": "Kray"}]
    assert d["status_zu_unsicher"] == [{"schl_nr": "1", "lemma": "A"}]
    assert d["status_zu_automatisch"] == [{"schl_nr": "2", "lemma": "B"}]


def test_eintrag_neu_und_entfallen(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [])
    _schreibe(tmp_path / "neu", [_s("2", "B")], [])
    d = vergleiche(tmp_path / "alt", tmp_path / "neu")
    assert d["eintrag_neu"] == [{"schl_nr": "2", "lemma": "B"}]
    assert d["eintrag_entfallen"] == [{"schl_nr": "1", "lemma": "A"}]


def test_bericht_enthaelt_zaehlung_und_zeilen(tmp_path):
    _schreibe(tmp_path / "alt", [_s("1", "A")], [])
    _schreibe(tmp_path / "neu", [_s("1", "A")], [_n("1", 1, "1939-05-26", "Kamerunstraße")])
    md = formatiere_bericht(vergleiche(tmp_path / "alt", tmp_path / "neu"))
    assert "| Stadium gewonnen | 1 |" in md
    assert "Kamerunstraße" in md
```

- [ ] **Step 2: Tests laufen lassen**

Run: `python3 -m pytest tests/test_differenz.py -q`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Modul schreiben**

```python
# strassen/differenz.py
"""Zwei Stände von daten/strassen.csv und daten/namen.csv vergleichen.

Sicherung für Parser-Änderungen (Spec 2026-09-11, Abschnitt 5.1): Jede Änderung
gegenüber dem vorigen Stand wird je Schlüsselnummer ausgewiesen, damit nichts
stillschweigend kippt. Aufruf:

  git show HEAD:daten/strassen.csv > /tmp/alt/strassen.csv   (analog namen.csv)
  python3 -m strassen.differenz /tmp/alt daten --ausgabe docs/regression/<datum>.md
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

_KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe"]

_KATEGORIEN = [
    ("eintrag_neu", "Eintrag neu"),
    ("eintrag_entfallen", "Eintrag entfallen"),
    ("stadium_gewonnen", "Stadium gewonnen"),
    ("stadium_verloren", "Stadium verloren"),
    ("datum_veraendert", "Datum verändert"),
    ("name_veraendert", "Name verändert"),
    ("kopffeld_veraendert", "Kopffeld verändert"),
    ("status_zu_unsicher", "Status automatisch → unsicher"),
    ("status_zu_automatisch", "Status unsicher → automatisch"),
]


def _lade(verzeichnis):
    verzeichnis = Path(verzeichnis)
    with open(verzeichnis / "strassen.csv", encoding="utf-8", newline="") as f:
        strassen = {z["schl_nr"]: z for z in csv.DictReader(f)}
    namen = defaultdict(list)
    with open(verzeichnis / "namen.csv", encoding="utf-8", newline="") as f:
        for z in csv.DictReader(f):
            namen[z["schl_nr"]].append(z)
    for stadien in namen.values():
        stadien.sort(key=lambda z: int(z["stadium"]))
    return strassen, namen


def _stadium_text(z):
    return f"{z['gueltig_ab']} {z['name']}".strip()


def vergleiche(alt_dir, neu_dir) -> dict:
    alt_s, alt_n = _lade(alt_dir)
    neu_s, neu_n = _lade(neu_dir)
    d = {k: [] for k, _ in _KATEGORIEN}

    for schl in sorted(set(alt_s) | set(neu_s)):
        if schl not in alt_s:
            d["eintrag_neu"].append({"schl_nr": schl, "lemma": neu_s[schl]["lemma"]})
            continue
        if schl not in neu_s:
            d["eintrag_entfallen"].append({"schl_nr": schl, "lemma": alt_s[schl]["lemma"]})
            continue
        a, n = alt_s[schl], neu_s[schl]
        basis = {"schl_nr": schl, "lemma": a["lemma"]}

        for feld in _KOPFFELDER:
            if a[feld] != n[feld]:
                d["kopffeld_veraendert"].append({**basis, "feld": feld, "alt": a[feld], "neu": n[feld]})
        if a["status"] == "automatisch" and n["status"] == "unsicher":
            d["status_zu_unsicher"].append(basis)
        elif a["status"] == "unsicher" and n["status"] == "automatisch":
            d["status_zu_automatisch"].append(basis)

        alt_st, neu_st = alt_n.get(schl, []), neu_n.get(schl, [])
        # Paarweise nach Position; überzählige Stadien sind gewonnen/verloren.
        for i in range(max(len(alt_st), len(neu_st))):
            if i >= len(alt_st):
                d["stadium_gewonnen"].append({**basis, "neu": _stadium_text(neu_st[i])})
            elif i >= len(neu_st):
                d["stadium_verloren"].append({**basis, "alt": _stadium_text(alt_st[i])})
            else:
                x, y = alt_st[i], neu_st[i]
                if (x["gueltig_ab"], x["datum_praezision"]) != (y["gueltig_ab"], y["datum_praezision"]):
                    d["datum_veraendert"].append({**basis, "stadium": x["stadium"],
                                                  "alt": f"{x['gueltig_ab']} ({x['datum_praezision']})",
                                                  "neu": f"{y['gueltig_ab']} ({y['datum_praezision']})"})
                if x["name"] != y["name"]:
                    d["name_veraendert"].append({**basis, "stadium": x["stadium"],
                                                 "alt": x["name"], "neu": y["name"]})
    return d


def formatiere_bericht(diff: dict) -> str:
    zeilen = ["# Differenzbericht\n", "| Kategorie | Anzahl |", "|---|--:|"]
    for k, titel in _KATEGORIEN:
        zeilen.append(f"| {titel} | {len(diff[k])} |")
    for k, titel in _KATEGORIEN:
        if not diff[k]:
            continue
        zeilen += ["", f"## {titel}\n"]
        for e in diff[k]:
            rest = "; ".join(f"{f}: {e[f]}" for f in e if f not in ("schl_nr", "lemma"))
            zeilen.append(f"- {e['schl_nr']} {e['lemma']}" + (f" — {rest}" if rest else ""))
    return "\n".join(zeilen) + "\n"


def _cli():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("alt_dir")
    p.add_argument("neu_dir")
    p.add_argument("--ausgabe", help="Markdown-Datei; ohne Angabe nur Konsole")
    a = p.parse_args()
    bericht = formatiere_bericht(vergleiche(a.alt_dir, a.neu_dir))
    if a.ausgabe:
        Path(a.ausgabe).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ausgabe).write_text(bericht, encoding="utf-8")
    print(bericht)


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 -m pytest tests/test_differenz.py -q`
Expected: alle PASS

- [ ] **Step 5: Commit**

```bash
git add strassen/differenz.py tests/test_differenz.py
git commit -m "differenz.py: Vergleich zweier Datenstände mit Markdown-Bericht (Spec 5.1)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Goldstandard-Regressionstest

**Files:**
- Create: `tests/test_goldstandard_regression.py`

**Interfaces:**
- Consumes: `docs/goldstandard/stichprobe.csv` (Spalten `schl_nr, lemma, status, buchseite, band, pdf_seite, haelfte, feld, wert, korrekt, korrektur`), `strassen.erschliessen.main`, lokales `ocr/seiten/`

- [ ] **Step 1: Test schreiben**

```python
# tests/test_goldstandard_regression.py
"""Die 17 Korrekturen der Goldstandard-Stichprobe (Entwicklungs-Stichprobe, 2026-09-11)
gegen den aktuellen Parser: Jede Korrektur ist entweder umgesetzt ODER der Eintrag ist
status=unsicher (precision-first: korrigiert oder gekennzeichnet, nie still falsch).

Braucht die lokalen OCR-Seiten (gitignored); ohne sie wird übersprungen."""
import csv
from collections import defaultdict
from pathlib import Path

import pytest

from strassen.erschliessen import main

WURZEL = Path(__file__).resolve().parent.parent
OCR = WURZEL / "ocr" / "seiten"
STICHPROBE = WURZEL / "docs" / "goldstandard" / "stichprobe.csv"

pytestmark = pytest.mark.skipif(not OCR.is_dir(), reason="ocr/seiten/ nur lokal vorhanden")


@pytest.fixture(scope="module")
def datensatz(tmp_path_factory):
    aus = tmp_path_factory.mktemp("daten")
    main(ocr_dir=str(OCR), ausgabe_dir=str(aus))
    strassen = {z["schl_nr"]: z for z in csv.DictReader(open(aus / "strassen.csv", encoding="utf-8"))}
    namen = defaultdict(dict)
    for z in csv.DictReader(open(aus / "namen.csv", encoding="utf-8")):
        namen[z["schl_nr"]][int(z["stadium"])] = z
    return strassen, namen


def _fehlerzeilen():
    with open(STICHPROBE, encoding="utf-8", newline="") as f:
        return [z for z in csv.DictReader(f) if z["korrekt"].strip().lower() == "nein"]


def _ist_wert(strassen, namen, schl, feld):
    if feld.startswith("stadium_"):
        _, n, art = feld.split("_")
        st = namen.get(schl, {}).get(int(n))
        if st is None:
            return None
        return st["gueltig_ab"] if art == "datum" else st["name"]
    return strassen.get(schl, {}).get(feld)


@pytest.mark.parametrize("zeile", _fehlerzeilen(), ids=lambda z: f"{z['schl_nr']}-{z['feld']}")
def test_korrektur_umgesetzt_oder_gekennzeichnet(datensatz, zeile):
    strassen, namen = datensatz
    schl = zeile["schl_nr"]
    assert schl in strassen, "Eintrag verschwunden"
    ist = _ist_wert(strassen, namen, schl, zeile["feld"])
    korrigiert = ist == zeile["korrektur"]
    gekennzeichnet = strassen[schl]["status"] == "unsicher"
    assert korrigiert or gekennzeichnet, f"ist={ist!r}, soll={zeile['korrektur']!r}, status={strassen[schl]['status']}"


def test_mindestens_zwoelf_korrekturen_umgesetzt(datensatz):
    """Sollwert aus der Spec: Alle Fehler außer reinem OCR-Rauschen (Spervogelweg:
    'Minnesängerr', '19862') sind durch Regeln behebbar — mindestens 12 von 17."""
    strassen, namen = datensatz
    umgesetzt = sum(1 for z in _fehlerzeilen()
                    if _ist_wert(strassen, namen, z["schl_nr"], z["feld"]) == z["korrektur"])
    assert umgesetzt >= 12, umgesetzt
```

- [ ] **Step 2: Test laufen lassen**

Run: `python3 -m pytest tests/test_goldstandard_regression.py -v`
Expected: alle 17 parametrisierten Fälle PASS (korrigiert oder unsicher) und der Zähltest PASS. Schlägt ein Fall FAIL, den Grund im OCR-Text prüfen (`grep -n "<Lemma>" ocr/seiten/s<buchseite>.txt`) und die zuständige Regel (Tasks 3–8) nachbessern — nicht den Test.

- [ ] **Step 3: Commit**

```bash
git add tests/test_goldstandard_regression.py
git commit -m "Goldstandard-Regressionstest: 17 Korrekturen umgesetzt oder gekennzeichnet (Spec 5.2)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Regeneration, Differenzbericht, Kennzahlen

**Files:**
- Modify: `daten/strassen.csv`, `daten/namen.csv`, `daten/konkordanz_1936.csv`, `daten/pruefung_validierung.csv`, `docs/qualitaet.md`, `README.md` (Abschnitt „Bezifferte Qualität")
- Create: `docs/regression/2026-09-parser-reparatur.md`

**Interfaces:**
- Consumes: `python3 -m strassen.differenz` (Task 10)

- [ ] **Step 1: Alten Stand sichern**

```bash
mkdir -p /tmp/claude-alt && git show HEAD:daten/strassen.csv > /tmp/claude-alt/strassen.csv && git show HEAD:daten/namen.csv > /tmp/claude-alt/namen.csv
```

- [ ] **Step 2: Regenerieren**

```bash
python3 -m strassen.erschliessen && python3 -m strassen.veroeffentlichen
```

Expected: `erschliessen` druckt Kennzahlen; `strassen` bleibt ≈ 3.338, `namensstadien` ≥ 5.370. `veroeffentlichen.main` führt die drei Selbstprüfungen aus `validierung.py` aus und schreibt `docs/qualitaet.md`, `daten/pruefung_validierung.csv`, `daten/konkordanz_1936.csv` und `daten/pruefung_konkordanz.csv` (Adressbuch und amtliches Verzeichnis per `--adressbuch` / `--amtliches-verzeichnis` überschreibbar, Standardpfade stehen im Modul).

- [ ] **Step 3: Differenzbericht erzeugen und Verluste prüfen**

```bash
python3 -m strassen.differenz /tmp/claude-alt daten --ausgabe docs/regression/2026-09-parser-reparatur.md
```

Jeden Eintrag unter „Stadium verloren", „Datum verändert" und „Status unsicher → automatisch" am OCR-Text prüfen (`grep -n "<Lemma>" ocr/seiten/s<buchseite>.txt`, Buchseite aus `daten/strassen.csv`). Ergebnis je Eintrag als Kommentarzeile unter dem Listenpunkt im Bericht festhalten, Format: `  - Prüfung: <Befund, z. B. 'korrekt: Druck hat 01. Oktober 1920' oder 'Verlust akzeptiert: Datum OCR-verstümmelt, Eintrag jetzt unsicher'>`. Kein Verlust bleibt unkommentiert. Zeigt die Prüfung einen echten Fehler (neuer Wert falsch, Eintrag nicht `unsicher`), zurück in die zuständige Task, Fix mit Test, dann Step 2 wiederholen.

- [ ] **Step 4: Kennzahlen prüfen und Dokumentation aktualisieren**

```bash
python3 - <<'EOF'
import csv, re, collections
s = list(csv.DictReader(open("daten/strassen.csv", encoding="utf-8")))
n = list(csv.DictReader(open("daten/namen.csv", encoding="utf-8")))
k = list(csv.DictReader(open("daten/konkordanz_1936.csv", encoding="utf-8")))
print("strassen", len(s), collections.Counter(z["status"] for z in s))
print("namen", len(n), collections.Counter(z["datum_praezision"] for z in n))
print("ohne Stadium", len({z["schl_nr"] for z in s} - {z["schl_nr"] for z in n}))
print("Kurznamen", sum(1 for z in n if re.fullmatch(r"(St|I{1,3}|IV)", z["name"])))
print("leere Klasse", sum(1 for z in s if not z["strassenklasse"]), "leere Stadtteile", sum(1 for z in s if not z["stadtteile"]))
print("konkordanz", len(k), collections.Counter(z["eindeutig"] for z in k))
EOF
```

Mit den Sollwerten oben vergleichen. Dann im README, Abschnitt „Bezifferte Qualität", die Zahlen ersetzen: Zeilen `strassen.csv` (Gesamt, `unsicher`, `automatisch`), `namen.csv` (Gesamt und Präzisionsverteilung inkl. `jahrhundert`), `konkordanz_1936.csv` (Zeilen, `eindeutig`), Tabelle „Drei unabhängige Selbstprüfungen" aus `docs/qualitaet.md` übernehmen. Unter dem Goldstandard-Abschnitt einen Satz ergänzen: „Die 21 Regeln der Reparatur sind in `docs/specs/2026-09-11-parser-reparatur-design.md` beschrieben, der Nachweis jeder Änderung in `docs/regression/2026-09-parser-reparatur.md`."

- [ ] **Step 5: Alle Tests laufen lassen**

Run: `python3 -m pytest -q`
Expected: alle PASS, inklusive `test_goldstandard_regression.py`

- [ ] **Step 6: Commit**

```bash
git add daten/strassen.csv daten/namen.csv daten/konkordanz_1936.csv daten/pruefung_validierung.csv docs/qualitaet.md docs/regression/2026-09-parser-reparatur.md README.md
git commit -m "Regeneration nach Parser-Reparatur: Datensatz, Konkordanz, Qualitätsbericht, Differenzbericht

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

`daten/pruefung.csv` und `daten/pruefung_konkordanz.csv` sind gitignored und werden nicht committet.

---

## Selbstprüfung des Plans gegen die Spec

- Regeln 1–3, 9 → Task 4; Regel 4 → Tasks 1, 3, 4; Regel 5 → Task 6; Regeln 6, 7, 8, 14, 15, 16, 18 → Tasks 1–3 (Regel 15 Positionsregel in Tasks 3 und 4); Regeln 10–13 → Task 7; Regel 17 → Task 3; Regeln 19, 20 → Task 5; Regel 21 → Task 8; Schema `jahrhundert` → Task 9; Differenzlauf (Spec 5.1) → Tasks 10, 12; Goldstandard-Regressionstest (5.2) → Task 11; TDD je Regel (5.3) → alle Tasks; Regeneration und Doku (Spec 6) → Task 12.
- Typen: `Datum(gueltig_ab, praezision, hinweis, trenner)`, `Stadium(..., hinweis="")`, `Kopf(..., hinweise=())` sind in Tasks 1, 3, 4 definiert und in 5, 8, 11 gleichlautend verwendet. Hinweistexte sind in Task 2 (Datum), Task 3 (`urspr.`), Task 5 (Klasse) festgelegt und in Task 8 wörtlich erwartet.
- `MONATE` wandert nach `datum.py`; `namen.py` re-exportiert, `kopf.py` importiert nach Task 4 nur noch aus `datum`.
