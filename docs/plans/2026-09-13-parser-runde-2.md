# Parser-Runde 2 nach der LLM-Lesung — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die sieben Musterklassen aus der Sichtung der LLM-Prüfliste im Parser beheben, die Seitenende-Phantome der Prüfliste beseitigen, Prüfbilder für die manuelle Sichtung erzeugen und das Vorgehen chronologisch dokumentieren; danach Datensatz, Prüfliste und README regenerieren.

**Architecture:** Regeln R1/R3 in `aufbereitung.py`, R2 in `namen.py`, R4/R6 in `segmentierung.py` (Eintrag bekommt `hinweise`), R5 in `kopf.py` (+ Aufruf in `erschliessen.py`), R7 in `llm_vergleich.py`. Neues Modul `pruefbilder.py` (Rendering über `goldstandard.rendere_ausschnitt`). Doku `docs/vorgehen.md`. Sicherung über `differenz.py` und den Goldstandard-Regressionstest.

**Tech Stack:** Python ≥ 3.12, Standardbibliothek; pytest (Funktionsstil); Rendering nur in `pruefbilder.py`/`goldstandard.py`.

**Spec:** `docs/specs/2026-09-13-parser-runde-2-design.md`

## Global Constraints

- Deutsch für Bezeichner, Kommentare, Docstrings, Commits. Trailer exakt: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
- Nur Standardbibliothek. Kein Netzzugriff in Tests. Keine neue LLM-Lesung (Prüfliste aus dem Cache).
- precision-first: Toleranz-Erkennung = Wert übernehmen **und** Hinweis (→ `status=unsicher`). Hinweis-Texte sind Konstanten und werden wörtlich zu Prüfgründen (Mechanismus `erschliessen.main`, Zeilen ~242–248).
- Testfixtures: reale OCR-Ausschnitte (Kopf/Kette), niemals Erläuterungstext.
- Jeder Task: Test zuerst, Fehlschlag sehen, minimal implementieren, `python3 -m pytest -q` grün (aktuell 354), committen.
- Arbeit auf Branch `parser-runde-2` ab `parser-und-validierung` (b1d3787).
- Regeneration erst in Task 8; Tasks 1–7 ändern `daten/` nicht.

---

### Task 1: R1 Trennstrich vor Großbuchstabe und R3 Großumlaut-Wörterbuch (`aufbereitung`)

**Files:**
- Modify: `strassen/aufbereitung.py` (nach `_TRENNUNG`, in `verbinde_zeilen`)
- Test: `tests/test_aufbereitung.py`

**Interfaces:**
- Produces: `aufbereitung._TRENNUNG_GROSS = re.compile(r"-\n\s*(?=[A-ZÄÖÜ])")`, `aufbereitung.GROSSUMLAUTE: dict`, `aufbereitung._GROSSUMLAUT_WORT` (Regex über die Schlüssel mit Wortgrenzen).

- [ ] **Step 1: Failing tests**

```python
def test_trennstrich_vor_grossbuchstabe_bleibt_ohne_leerzeichen():
    # S. 23, Adolf-Rath-Straße 00013 (Prüfliste: 184 Zeilen 'Adolf- Rath-Straße')
    roh = "10. Januar 1929: Adolf-\nRath-Straße. Adolf Rath *28. August 1863"
    assert "Adolf-Rath-Straße." in verbinde_zeilen(roh)
    assert "Adolf- Rath" not in verbinde_zeilen(roh)


def test_trennstrich_vor_grossbuchstabe_in_stadtteilen():
    roh = "Stadtteile Überruhr-\nHinsel und Überruhr-Holthausen, Str.-Kl.: Gemeindestraße"
    assert "Überruhr-Hinsel und" in verbinde_zeilen(roh)


def test_trennstrich_vor_kleinbuchstabe_weiterhin_aufgeloest():
    assert verbinde_zeilen("Katern-\nberger Straße") == "Katernberger Straße"


def test_grossumlaut_woerterbuch_korrigiert_bekannte_woerter():
    roh = "Str.-Gr.: Essener Geschichte und Ortlichkeit, Bergbau, 1906: Abtissin"
    aus = verbinde_zeilen(roh)
    assert "Örtlichkeit" in aus and "Äbtissin" in aus


def test_grossumlaut_woerterbuch_nur_ganze_woerter():
    assert "Ostviertel" in verbinde_zeilen("Stadtteile Stadtkern und Ostviertel")
    assert "Östviertel" not in verbinde_zeilen("Stadtteile Stadtkern und Östviertel")   # OCR-Ö → O
```

- [ ] **Step 2: Run, expect failures**

Run: `python3 -m pytest tests/test_aufbereitung.py -q`

- [ ] **Step 3: Implementieren**

```python
# Trennstrich am Zeilenende VOR Großbuchstabe: Namensbestandteil ('Adolf-\nRath-Straße',
# 'Überruhr-\nHinsel'), im Deutschen gibt es kein '- ' — der Strich bleibt, das
# Zeilenende verschwindet ohne Leerzeichen. 562 Stellen im Korpus, 184 bestätigte
# Prüflistenzeilen (Spec 2026-09-13, R1). Muss VOR dem Zeilenumbruch→Leerzeichen laufen.
_TRENNUNG_GROSS = re.compile(r"-\n\s*(?=[A-ZÄÖÜ])")
# OCR liest Großumlaute am Wortanfang als O/A/U (Spec 2026-09-13, R3). Nur exakte
# Wortformen aus den Funden der Prüfliste; 'Ostviertel' ist korrekt und steht NICHT hier.
# Umgekehrt wird das OCR-'Östviertel' (2 Fälle) zu 'Ostviertel'.
GROSSUMLAUTE = {"Ortlichkeit": "Örtlichkeit", "Abtissin": "Äbtissin", "Agyptologe": "Ägyptologe",
                "Agirstraße": "Ägirstraße", "Uckendorfer": "Ückendorfer", "Östviertel": "Ostviertel"}
_GROSSUMLAUT_WORT = re.compile(r"\b(" + "|".join(map(re.escape, GROSSUMLAUTE)) + r")\b")
```

In `verbinde_zeilen` nach `_OCR_FEHLER` und vor `_TRENNUNG`: `text = _TRENNUNG_GROSS.sub("-", text)`; nach `_UND_KLEBT`: `text = _GROSSUMLAUT_WORT.sub(lambda m: GROSSUMLAUTE[m.group(1)], text)`. Modul-Docstring um beide Regeln ergänzen.

- [ ] **Step 4: Tests grün, Gesamtsuite grün; Commit**

```bash
git add strassen/aufbereitung.py tests/test_aufbereitung.py
git commit -m "aufbereitung: Trennstrich vor Großbuchstabe ohne Leerzeichen (R1), Großumlaut-Wörterbuch (R3)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: R2 Klammerzusätze normalisieren (`namen`)

**Files:**
- Modify: `strassen/namen.py`
- Test: `tests/test_namen.py`

**Interfaces:**
- Produces: `namen.HINWEIS_ZUSATZ_ERGAENZT = "Klammerzusatz ergänzt"`, `namen.normalisiere_zusatz(name: str) -> tuple[str, str]` (Name, Hinweis oder `""`), `namen.ZUSATZWOERTER: dict`.
- Angewandt in `_akzeptierte_treffer` auf jeden Namen (urspr.- und Stempel-Stadien); Hinweis wird an den bestehenden `hinweis` angehängt (`"; "`-verbunden).

- [ ] **Step 1: Failing tests**

```python
from strassen.namen import normalisiere_zusatz, parse_namenskette, HINWEIS_ZUSATZ_ERGAENZT


@pytest.mark.parametrize("roh,soll", [
    ("Moltkestraße (tiw.)", "Moltkestraße (tlw.)"),
    ("Frohnhauser Straße (tIw.)", "Frohnhauser Straße (tlw.)"),
    ("Damannstraße (t!w.)", "Damannstraße (tlw.)"),
    ("Ahnewinkelstraße (Verl)", "Ahnewinkelstraße (Verl.)"),
    ("Kapitän-Lehmann-Höhe (Umb))", "Kapitän-Lehmann-Höhe (Umb.)"),
    ("Sonnenstraße {tlw.)", "Sonnenstraße (tlw.)"),
    ("Körholzstraße [neue Führung)", "Körholzstraße (neue Führung)"),
    ("Blockstraße (verl.)", "Blockstraße (Verl.)"),
    ("Altendorfer Straße (tlw. Umb.)", "Altendorfer Straße (tlw. Umb.)"),
])
def test_normalisiere_zusatz_bekannte_varianten_ohne_hinweis(roh, soll):
    assert normalisiere_zusatz(roh) == (soll, "")


def test_normalisiere_zusatz_ortsklammer_bleibt():
    assert normalisiere_zusatz("Bahnstraße (Essen)") == ("Bahnstraße (Essen)", "")


def test_normalisiere_zusatz_abgeschnitten_wird_ergaenzt_und_gekennzeichnet():
    assert normalisiere_zusatz("Thomaestraße (tiw") == ("Thomaestraße (tlw.)", HINWEIS_ZUSATZ_ERGAENZT)
    assert normalisiere_zusatz("Im Westerbruch (Verl") == ("Im Westerbruch (Verl.)", HINWEIS_ZUSATZ_ERGAENZT)


def test_normalisiere_zusatz_ohne_klammer_unveraendert():
    assert normalisiere_zusatz("Aachener Straße") == ("Aachener Straße", "")


def test_parse_namenskette_normalisiert_zusaetze():
    # Ahnewinkelstraße 00021, S. 23 (Prüfliste)
    st = parse_namenskette("vor 1898: Ahnewinkelstraße (Verl), 16. Mai 1902: Ahnewinkelstraße (tiw.)")
    assert [s.name for s in st] == ["Ahnewinkelstraße (Verl.)", "Ahnewinkelstraße (tlw.)"]
    assert all(s.hinweis == "" for s in st)


def test_parse_namenskette_abgeschnittener_zusatz_am_kettenende():
    st = parse_namenskette("29. März 1892: Thomaestraße (tiw")
    assert st[-1].name == "Thomaestraße (tlw.)"
    assert HINWEIS_ZUSATZ_ERGAENZT in st[-1].hinweis
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implementieren**

```python
HINWEIS_ZUSATZ_ERGAENZT = "Klammerzusatz ergänzt"
# Dickhoffs drei Vermerke am Namensende und ihre OCR-Varianten (Spec 2026-09-13, R2):
# 'tlw.' (teilweise), 'Verl.' (Verlängerung), 'Umb.' (Umbenennung). Wortweise, exakt.
ZUSATZWOERTER = {"tlw": "tlw.", "tiw": "tlw.", "tIw": "tlw.", "t!w": "tlw.", "tw": "tlw.", "tl": "tlw.",
                 "tlw.": "tlw.", "Verl": "Verl.", "verl": "Verl.", "Verl.": "Verl.", "verl.": "Verl.",
                 "Ver1": "Verl.", "Umb": "Umb.", "Umb.": "Umb."}
_ZUSATZ = re.compile(r"^(?P<kern>.*?)\s*(?P<auf>[\(\{\[])(?P<inhalt>[^\(\)\{\}\[\]]*?)(?P<zu>[\)\}\]]*)\s*$")


def normalisiere_zusatz(name: str):
    """Klammerzusatz am Namensende auf die drei Vermerke normalisieren.
    -> (name, hinweis). Unbekannte Wörter (Ortsklammern) bleiben; fehlt die schließende
    Klammer, wird sie ergänzt und der Hinweis gesetzt (Rest des Zusatzes kann fehlen)."""
    m = _ZUSATZ.match(name)
    if not m or not m.group("inhalt").strip():
        return name, ""
    woerter = [ZUSATZWOERTER.get(w, w) for w in m.group("inhalt").split()]
    hinweis = "" if m.group("zu") else HINWEIS_ZUSATZ_ERGAENZT
    return f"{m.group('kern')} ({' '.join(woerter)})".strip(), hinweis
```

In `_akzeptierte_treffer`: nach `name = ...strip()` jeweils `name, hz = normalisiere_zusatz(name)` und den Hinweis anhängen: `hinweis = "; ".join(filter(None, [hinweis, hz]))` (für Stempel-Stadien: `d.hinweis` und `hz` verbinden). Achtung: `_NAME` endet vor `,`/`;`/Satzende — ein abgeschnittenes `(tiw` am Kettenende bleibt im Namen erhalten, weil das Kettenende (`kopf._stadienkette`) am Satzpunkt bzw. Textende schneidet; prüfen, dass `(tiw.)` mit Punkt nicht als Satzende gewertet wird (der Punkt steht vor `)` → `SATZENDE` verlangt Leerraum/Ende danach → korrekt).

- [ ] **Step 4: Tests grün; Gesamtsuite (auch `test_stichtag`, `test_erschliessen`); Commit**

```bash
git add strassen/namen.py tests/test_namen.py
git commit -m "namen: Klammerzusätze (tlw./Verl./Umb.) normalisieren, abgeschnittene ergänzen und kennzeichnen (R2)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: R4 römischer Präfix und R6 Anker-/Trenner-Toleranz (`segmentierung`, `erschliessen`)

**Files:**
- Modify: `strassen/segmentierung.py` (`ANKER`, `_LEMMA`, `Eintrag`, `segmentiere`)
- Modify: `strassen/erschliessen.py` (Hinweise des Eintrags → Gründe)
- Test: `tests/test_segmentierung.py`, `tests/test_erschliessen.py`

**Interfaces:**
- Produces: `segmentierung.HINWEIS_ANKER_KORRIGIERT = "Anker OCR-korrigiert"`, `Eintrag.hinweise: tuple = ()`, `segmentierung._ANKER_KANONISCH = re.compile(r"Schl\.\s*-\s*Nr\.\s*:")`.
- `erschliessen.main` übernimmt `e.hinweise` in `gruende` (wie `k.hinweise`).

- [ ] **Step 1: Failing tests**

```python
def _eintraege(text, seite=1):
    return segmentiere([(seite, text)])


def test_roemischer_praefix_bleibt_im_lemma():
    # S. 86, 00502/00503 (Prüfliste: 24 Lemmata ohne I./II./III.)
    e = _eintraege("Akten: STAD Best. Reg. Düsseldorf Nr. 19164. I. Buschlandweg: Schl.-Nr.: 00502, Stadtteil Frillendorf, "
                   "Str.-Kl.: Gemeindestraße. II. Buschlandweg: Schl.-Nr.: 00503, Stadtteil Frillendorf")
    assert [x.lemma_roh for x in e] == ["I. Buschlandweg", "II. Buschlandweg"]


def test_satzpunkt_vor_lemma_bricht_weiterhin_ab():
    e = _eintraege("gehört zur Flur. Aachener Straße: Schl.-Nr.: 00001, Stadtteil Frohnhausen")
    assert e[0].lemma_roh == "Aachener Straße"


@pytest.mark.parametrize("text,lemma,hinweis", [
    ("Bd. 85/1970; 5. 5 ff. Brunhildenstraße; Schl.-Nr.: 00465, Stadtteil Kray", "Brunhildenstraße", ()),           # S. 82
    ("Rep. 113 Nr. 565. Waldblick; Schl.-Nr.: 03297, Stadtteil Stadtwald", "Waldblick", ()),                         # S. 338
    ("an Rutger von Bergerhausen. Am Schloss Schellenberg:; Schl.-Nr.: 00710, Stadtteil", "Am Schloss Schellenberg", ()),  # S. 42
    ("zur Kenntnis gegeben. Graitengraben: Sch}.-Nr.: 01067, Stadtteil", "Graitengraben", ("Anker OCR-korrigiert",)),  # S. 133
    ("eine Ballonfabrik. Riegelweg: Sch).-Nr.: 02599, Stadtteil", "Riegelweg", ("Anker OCR-korrigiert",)),           # S. 274
    ("Bedeutung gewonnen. Schraeplerstraße:  Schl.-N.: 02821, Stadtteil", "Schraeplerstraße", ("Anker OCR-korrigiert",)),  # S. 296
    ("auch Markesfeld. Marreweg: -Schl.-Nr.: 02086, Stadtteil", "Marreweg", ("Anker OCR-korrigiert",)),              # S. 231
    ("Siehe Mallinckrodtplatz. Malmedystraße: Schl.-Nr.; 02070, Stadtteil", "Malmedystraße", ("Anker OCR-korrigiert",)),  # S. 229
])
def test_anker_und_trenner_varianten(text, lemma, hinweis):
    e = _eintraege(text)
    assert len(e) == 1 and e[0].lemma_roh == lemma
    assert e[0].hinweise == hinweis
```

Integrationstest in `tests/test_erschliessen.py` (Muster `_lauf` der Datei nutzen): Mini-Seite mit `Graitengraben: Sch}.-Nr.: 01067, Stadtteil Rüttenscheid, Str.-Kl.: Gemeindestraße, Str.-Gr.: Flurname, 1900: Graitengraben.` → Eintrag vorhanden, `status == "unsicher"`, `pruefung.csv` enthält Grund `Anker OCR-korrigiert`.

- [ ] **Step 2: Run, expect failures**

- [ ] **Step 3: Implementieren**

```python
# Anker: kanonisch 'Schl.-Nr.:'. Toleriert: OCR-Buchstaben nach 'Sch' (auch '}' ')'),
# 'N.' statt 'Nr.', führender Bindestrich, ';' statt ':' (Spec 2026-09-13, R6). Jede
# Abweichung von der kanonischen Form wird als Hinweis gemeldet.
ANKER = re.compile(r"-?\s*Sch[a-zA-Z!|}\)]{0,3}[.,]?\s*-?\s*N(?:r)?\.?\s*[:;]")
_ANKER_KANONISCH = re.compile(r"^Schl\.-Nr\.:$")
HINWEIS_ANKER_KORRIGIERT = "Anker OCR-korrigiert"
# Lemma: Punkt nach römischer Zahl I–IV ist Abkürzungspunkt ('I. Buschlandweg'), kein
# Satzende (R4); Trenner ':' oder ';' (auch ':;', R6).
_LEMMA = re.compile(
    r"((?:(?!,|;|:|(?<!\bSt)(?<!\bI)(?<!\bII)(?<!\bIII)(?<!\bIV)\.(?!-|[A-Za-zÄÖÜäöüß]))[^\n]){2,60}?)\s*[:;]+\s*$"
)
```

`Eintrag` erhält `hinweise: tuple = ()`. In `segmentiere`: je Anker `anker_text = re.sub(r"\s+", "", volltext[m.start():m.end()]).lstrip("-")`; wenn `not _ANKER_KANONISCH.match(anker_text)`: Hinweis `(HINWEIS_ANKER_KORRIGIERT,)` in die Kandidaten aufnehmen und dem `Eintrag` mitgeben. Achtung Lemma-Regex: `;` ist innerhalb des Lemmas weiterhin ausgeschlossen, nur am Ende als Trenner erlaubt — der Test „Am Schloss Schellenberg:;" muss `:;` als Ende fressen, ohne dass der Rückwärtslauf am `;` stoppt (Lookahead prüft das Zeichen vor dem Verbrauch; `[:;]+` am Ende greift zuerst durch das `?`-Minimum — verifizieren, ggf. Trenner-Gruppe als `\s*:?;?\s*$` mit mindestens einem Zeichen formulieren).

`erschliessen.main`: nach dem Block `for hinweis in k.hinweise:` analog `for hinweis in e.hinweise:`.

- [ ] **Step 4: Tests grün; Gesamtsuite; Commit**

```bash
git add strassen/segmentierung.py strassen/erschliessen.py tests/test_segmentierung.py tests/test_erschliessen.py
git commit -m "segmentierung: römischer Präfix im Lemma (R4), Anker-/Trenner-Varianten mit Hinweis (R6)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: R5 Kopffeld-Ränder (`kopf`, `erschliessen`)

**Files:**
- Modify: `strassen/kopf.py`, `strassen/erschliessen.py`
- Test: `tests/test_kopf.py`, `tests/test_erschliessen.py`

**Interfaces:**
- Produces: `kopf.HINWEIS_RANDZEICHEN = "Randzeichen entfernt"`, `kopf.bereinige_rand(wert: str) -> tuple[str, str]` (Wert, Hinweis), `kopf._FELDREST = re.compile(r"\s*;\s*[_\s]*$")`.
- `parse_kopf` wendet `_FELDREST` auf `stadtteile`/`strassenklassen`-Rohwerte an (kein Hinweis) und `bereinige_rand` auf Straßenklassen-Elemente; `erschliessen.main` wendet `bereinige_rand` auf `e.lemma_roh` an (Hinweis → Grund) und nutzt den bereinigten Wert als `lemma`.

- [ ] **Step 1: Failing tests**

```python
from strassen.kopf import bereinige_rand, HINWEIS_RANDZEICHEN, parse_kopf


@pytest.mark.parametrize("roh,soll", [
    (") Am Richtenberg", "Am Richtenberg"), ("” An der Braut", "An der Braut"),
    ("„ Gemeindestraße", "Gemeindestraße"), ("nn Hattenheimer Straße", "Hattenheimer Straße"),
    ("ia Auf dem Sutan", "Auf dem Sutan"),
])
def test_bereinige_rand_entfernt_rauschen_mit_hinweis(roh, soll):
    assert bereinige_rand(roh) == (soll, HINWEIS_RANDZEICHEN)


@pytest.mark.parametrize("wert", ["Am Handelshof", "Aachener Straße", "I. Buschlandweg", "Auf'm Uhlenbroich"])
def test_bereinige_rand_laesst_saubere_werte(wert):
    assert bereinige_rand(wert) == (wert, "")


def test_feldrest_semikolon_unterstrich_entfernt():
    k = parse_kopf("01008, Stadtteil Holsterhausen; _, Str.-Kl.: Gemeindestraße; _, Str.-Gr.: Flurname, 1900: Test.")
    assert k.stadtteile == ["Holsterhausen"] and k.strassenklassen == ["Gemeindestraße"]
```

Integrationstest in `test_erschliessen.py`: Mini-Seite mit Lemma `) Am Richtenberg: Schl.-Nr.: 00238, …` → `lemma == "Am Richtenberg"`, `status == "unsicher"`, Grund `Randzeichen entfernt`.

- [ ] **Step 2: Run, expect failures**

- [ ] **Step 3: Implementieren**

```python
HINWEIS_RANDZEICHEN = "Randzeichen entfernt"
# Führendes Scanrauschen vor einem Kopfwert (Spec 2026-09-13, R5): Anführungs-/
# Klammerzeichen oder eine Kleinbuchstabenfolge ≤ 3 Zeichen plus Leerzeichen, danach
# muss ein Großbuchstabe folgen. 'Am Handelshof' u. ä. bleiben (Großbuchstabe am Anfang).
_RAND = re.compile(r"^(?:[„”\"')\]\}|]+\s*|[a-zäöü]{1,3}\s+)(?=[A-ZÄÖÜ])")
_FELDREST = re.compile(r"\s*;\s*[_\s]*$")


def bereinige_rand(wert: str):
    neu = _RAND.sub("", wert, count=1)
    return (neu, HINWEIS_RANDZEICHEN) if neu != wert else (wert, "")
```

In `parse_kopf`: Rohwert von `_STADTTEIL`/`_KLASSE` vor `_teile` mit `_FELDREST.sub("", …)` bereinigen; jedes Klassen-Element durch `bereinige_rand` (Hinweis in `hinweise`, falls gesetzt). In `erschliessen.main`: `lemma, hz = bereinige_rand(e.lemma_roh)`; `hz` in `gruende`; `lemma` statt `e.lemma_roh` in die Straßenzeile (die `pruefung`-Zeilen behalten `lemma_roh`).

- [ ] **Step 4: Tests grün; Gesamtsuite; Commit**

```bash
git add strassen/kopf.py strassen/erschliessen.py tests/test_kopf.py tests/test_erschliessen.py
git commit -m "kopf: Randzeichen vor Kopfwerten entfernen und kennzeichnen, '; _'-Feldreste (R5)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: R7 Prüfliste — letzter Eintrag je Seite nur im Kopf (`llm_vergleich`)

**Files:**
- Modify: `strassen/llm_vergleich.py` (`baue_pruefliste`, `_kennzahlen`, `formatiere_kennzahlen_md`)
- Test: `tests/test_llm_vergleich.py`

**Interfaces:**
- Produces: `llm_vergleich.letzte_eintraege_je_seite(strassen: list) -> set[str]` (schl_nr des jeweils letzten Eintrags je `buchseite` in Zeilenreihenfolge); Kennzahl `seitenende_ausgelassen` je Modell; Satz im Markdown.
- `baue_pruefliste` erhält den Parser als **Liste** (Reihenfolge!) — `als_struktur` darf erst danach laufen.

- [ ] **Step 1: Failing tests**

```python
def test_letzte_eintraege_je_seite():
    s = [{"schl_nr": "1", "buchseite": 23}, {"schl_nr": "2", "buchseite": 23}, {"schl_nr": "3", "buchseite": 24}]
    assert lv.letzte_eintraege_je_seite(s) == {"2", "3"}


def test_pruefliste_letzter_eintrag_je_seite_nur_kopf():
    # Arendahls Wiese 00189, S. 54: Kette läuft auf S. 55 weiter, Modelle sehen nur S. 54.
    strassen, namen = _parser()
    strassen.append({"schl_nr": "00189", "lemma": "Arendahls Wiese", "stadtteile": "Stoppenberg", "strassenklasse": "Gemeindestraße",
                     "namensgruppe": "Flurname", "verweis_auf": "", "buchseite": 23, "status": "automatisch"})
    namen += [{"schl_nr": "00189", "stadium": 1, "gueltig_ab": "1892-03-29", "datum_praezision": "tag", "name": "Lohstraße (tlw.)", "ist_urspruenglich": "falsch"},
              {"schl_nr": "00189", "stadium": 2, "gueltig_ab": "1937-11-20", "datum_praezision": "tag", "name": "Arendahls Wiese", "ist_urspruenglich": "falsch"},
              {"schl_nr": "00189", "stadium": 3, "gueltig_ab": "1963-12-17", "datum_praezision": "tag", "name": "Arendahls Wiese (Verl.)", "ist_urspruenglich": "falsch"}]
    antwort = _antwort()
    antwort["eintraege"].append({"schl_nr": "00189", "lemma": "Arendahls Wiese", "stadtteile": ["Stoppenberg"], "strassenklasse": ["Gemeindestraße"],
                                 "namensgruppe": "Flurname", "verweis_auf": "", "unvollstaendig": False,
                                 "stadien": [{"datum": "29.03.1892", "name": "Lohstraße (tlw.)", "urspruenglich": False}]})
    zeilen, kz = lv.baue_pruefliste((strassen, namen), {"qwen": {"antworten": {23: antwort}}, "mistral": {"antworten": {23: antwort}}})
    assert not [z for z in zeilen if z["schl_nr"] == "00189" and z["feld"].startswith("stadium")]
    assert kz["qwen"]["seitenende_ausgelassen"] == 1
    assert "Seitenende" in lv.formatiere_kennzahlen_md(kz)
```

- [ ] **Step 2: Run, expect failures**

- [ ] **Step 3: Implementieren** — `letzte_eintraege_je_seite` (Dict `buchseite → schl_nr`, letzter gewinnt, Rückgabe der Werte als Menge). In `baue_pruefliste`: vor `als_struktur(*parser)` die Menge berechnen (wenn `parser[0]` ein Dict ist, dessen `.values()` in Einfügereihenfolge nutzen); `unvollst` wird um diese schl_nr erweitert (Ketten beidseitig ausgeblendet, Kopf weiter verglichen); `seitenende_ausgelassen = len(letzte & set(p_s_teil))` in `_kennzahlen`; Markdown-Satz: „Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): N".

- [ ] **Step 4: Tests grün; Gesamtsuite; Commit**

```bash
git add strassen/llm_vergleich.py tests/test_llm_vergleich.py
git commit -m "llm_vergleich: letzter Eintrag je Seite nur im Kopf vergleichen (R7, Seitenumbruch-Phantome)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: W1 Prüfbilder je Prüfzeile (`strassen/pruefbilder.py`)

**Files:**
- Create: `strassen/pruefbilder.py`
- Test: `tests/test_pruefbilder.py`

**Interfaces:**
- Produces: `pruefbilder.eintraege_aus_pruefliste(zeilen, einig=("beide",)) -> list[dict]` (je Eintrag: `schl_nr`, `buchseite`, `felder` sortiert, dedupliziert, Reihenfolge nach `einig`-Rang und `schl_nr`), `pruefbilder.bilddateiname(schl_nr, buchseite) -> str` (= `goldstandard.scan_dateiname`), `pruefbilder.formatiere_index(eintraege) -> str` (Markdown-Tabelle), `pruefbilder.erzeuge(pruefliste_pfad, ziel_dir, quelle_dir, einig, render) -> int`, CLI `python3 -m strassen.pruefbilder [--einig beide] [--quelle DIR] [--ziel DIR]`; Standardziel `llm/pruefbilder/` (gitignored über `llm/`).

- [ ] **Step 1: Failing tests**

```python
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
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implementieren** — Modul mit Docstring (Zweck: Sichtung der Prüfliste am Scan, Spec 2026-09-13 W1), `WURZEL`, `ZIEL_DIR = WURZEL / "llm" / "pruefbilder"`, Import `QUELLE_PFAD, buchseite_zu_scan, rendere_ausschnitt, scan_dateiname` aus `goldstandard`; `_EINIG_RANG = {"beide": 0, "eines": 1, "unlesbar": 2}`; `erzeuge` liest die CSV, baut die Einträge, rendert fehlende Bilder mit `dpi=150`, schreibt `index.md` neu, gibt die Zahl neu gerenderter Bilder zurück; CLI mit argparse.

- [ ] **Step 4: Tests grün; Gesamtsuite; Commit**

```bash
git add strassen/pruefbilder.py tests/test_pruefbilder.py
git commit -m "pruefbilder: Seitenausschnitte und Index je Prüflisteneintrag für die Sichtung (W1)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: W2 Vorgehensseite und README-Verweis

**Files:**
- Create: `docs/vorgehen.md`
- Modify: `README.md` (Abschnitt „Methode", ein Verweis-Satz), `docs/goldstandard/ANLEITUNG.md` (Absatz zur Sichtung der LLM-Prüfliste mit `pruefbilder`)
- Test: `tests/test_datapackage.py` (ein Test, dass `docs/vorgehen.md` existiert und alle fünf Schritte nennt)

- [ ] **Step 1: Failing test**

```python
def test_vorgehensseite_nennt_alle_schritte():
    text = Path("docs/vorgehen.md").read_text(encoding="utf-8")
    for stichwort in ["2026-08-20", "Goldstandard", "Entwicklungs-Stichprobe", "Parser-Reparatur",
                      "LLM-Lesung", "Option A", "Korrektur-Overlay", "Parser-Runde 2"]:
        assert stichwort in text
```

- [ ] **Step 2: Run, expect FileNotFoundError**

- [ ] **Step 3: `docs/vorgehen.md`** — Überschrift „Vorgehen — Chronik der Entscheidungen", je Schritt Datum, drei bis fünf Sätze, Verweise:
  1. 2026-08-20 Datensatz-Design: Dickhoff 2015 als Quelle, OCR mit tesseract, Regex-Parser, Publikationsgrenzen (Spec `docs/specs/2026-08-20-…`).
  2. 2026-09-11 Goldstandard-Stichprobe: 50 Einträge geprüft, 17 Fehler, alle systematisch; Entscheidung Entwicklungs-Stichprobe, keine Neuziehung (`docs/goldstandard/ergebnis.md`).
  3. 2026-09-11/12 Parser-Reparatur: 21 Regeln, Straßen ohne Kette 84 → 10, Differenzbericht (`docs/regression/2026-09-parser-reparatur.md`).
  4. 2026-09-12/13 LLM-Lesung: zwei Bildmodelle als unabhängige zweite Leser, Option A (Modelle ändern keinen Status), Goldstandard-Messung qwen 6,1 % / mistral 22,4 %, Prüfliste, Korrektur-Overlay mit `status=geprueft` (`docs/llm_kalibrierung.md`, `docs/llm_lesung.md`, `docs/goldstandard/ergebnis_llm.md`).
  5. 2026-09-13 Parser-Runde 2: Sichtung der 712 `einig=beide`-Zeilen, sieben Regeln, Prüfbilder (`docs/specs/2026-09-13-parser-runde-2-design.md`, `docs/regression/2026-09-13-parser-runde-2.md`).
  Abschluss: „Was als Nächstes offen ist" (manuelle Sichtung der Einzelfälle, Zenodo-Release).
  README „Methode": Satz „Die Chronik der Entscheidungen steht in `docs/vorgehen.md`." ANLEITUNG: Absatz „Sichtung der LLM-Prüfliste": `python3 -m strassen.pruefbilder`, `llm/pruefbilder/index.md` öffnen, Bild ansehen, `korrektur`/`beleg` in `daten/pruefung_llm.csv`, dann `uebernehmen`.

- [ ] **Step 4: Tests grün; Commit**

```bash
git add docs/vorgehen.md README.md docs/goldstandard/ANLEITUNG.md tests/test_datapackage.py
git commit -m "docs: Vorgehens-Chronik, Sichtungsanleitung für die LLM-Prüfliste (W2)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Regeneration, Differenzbericht, Prüfliste, Zahlen

**Files:**
- Create: `docs/regression/2026-09-13-parser-runde-2.md`
- Modify: `daten/*.csv` (regeneriert), `docs/qualitaet.md`, `docs/erhebungsstand.md`, `docs/llm_lesung.md`, `README.md` (Zahlen), ggf. `daten/korrekturen.csv`

- [ ] **Step 1: Alten Stand sichern**

```bash
mkdir -p /tmp/claude-1000/alt && git show 54c5e2a:daten/strassen.csv > /tmp/claude-1000/alt/strassen.csv && git show 54c5e2a:daten/namen.csv > /tmp/claude-1000/alt/namen.csv
```

- [ ] **Step 2: Parser neu laufen lassen** — `python3 -m strassen.erschliessen` (wendet `daten/korrekturen.csv` an). Bricht er mit `KorrekturFehler` ab (ein `wert_alt` passt nicht mehr, z. B. weil R2 einen Klammerzusatz geändert hat), die betroffene Zeile in `korrekturen.csv` auf den neuen Parser-Wert setzen und im Differenzbericht vermerken. Kennzahlen notieren.

- [ ] **Step 3: Differenzbericht**

```bash
python3 -m strassen.differenz /tmp/claude-1000/alt daten --ausgabe docs/regression/2026-09-13-parser-runde-2.md
```

Bericht annotieren wie `docs/regression/2026-09-parser-reparatur.md`: Kopfabsatz (alt = 54c5e2a, Regeln R1–R6), je Kategorie ein Satz zur Erwartung; **jede** Zeile in „Stadium verloren" und „Status automatisch → unsicher" mit `- Prüfung:` bewerten; Sollwerte aus Spec 4.2 gegenrechnen (Eintrag neu = 9; Stadium verloren nur bei gleichzeitig „Stadium gewonnen" mit normalisiertem Namen; Lemma-Dubletten in `pruefung_validierung.csv` −22). Weicht etwas ab, das nicht erklärbar ist: STOP und melden (DONE_WITH_CONCERNS), nichts stillschweigend akzeptieren.

- [ ] **Step 4: Veröffentlichung und Prüfliste**

```bash
python3 -m strassen.veroeffentlichen
python3 -m strassen.llm_vergleich pruefliste
python3 -m pytest -q
```

`pruefliste` liest den Cache unter `llm/antworten/`; sie verweigert, falls `pruefung_llm.csv` ausgefüllte `korrektur`-Zellen hat (aktuell keine). Kennzahlen: Zeilen je `einig`, Sollwert `beide < 250`; Zahl `seitenende_ausgelassen`.

- [ ] **Step 5: README-Zahlen** — Data Dictionary (Zeilen strassen/namen/konkordanz), `automatisch`/`unsicher`/`geprueft`, „Unabhängige LLM-Lesung" (Prüfzeilen je `einig`, Hinweis auf R7), „Bekannte Grenzen" falls ein Satz zu Klammerzusätzen/Trennstrichen dort steht. `docs/vorgehen.md` Schritt 5 um die Ergebniszahlen ergänzen.

- [ ] **Step 6: Commit**

```bash
git add daten/ docs/ README.md
git commit -m "Parser-Runde 2: Regeneration, Differenzbericht, Prüfliste und Zahlen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Selbstprüfung

- **Spec-Abdeckung:** R1/R3 → Task 1; R2 → Task 2; R4/R6 → Task 3; R5 → Task 4; R7 → Task 5; W1 → Task 6; W2 → Task 7; Abschnitt 4 (Sicherungen, Regeneration, Sollwerte) → Task 8; Nicht-Ziele eingehalten (kein Namens-Wörterbuch, keine Modellwerte, keine neue Lesung).
- **Typkonsistenz:** `bereinige_rand -> (str, str)` in Task 4 für Lemma (erschliessen) und Klassen (kopf); `normalisiere_zusatz -> (str, str)` in Task 2; `Eintrag.hinweise: tuple` in Task 3 und Verbrauch in `erschliessen`; `letzte_eintraege_je_seite(list) -> set` in Task 5 vor `als_struktur`; `render`-Signatur in Task 6 = `goldstandard.rendere_ausschnitt(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi)`.
- **Reihenfolge:** Tasks 1–4 ändern die Parser-Ausgabe, aber `daten/` wird erst in Task 8 regeneriert; `test_goldstandard_regression` läuft in jedem Task mit (lokal), muss grün bleiben.
- **Platzhalter:** keine; Zahlen im README werden in Task 8 aus den Artefakten gesetzt.
