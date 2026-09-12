# Unabhängige LLM-Lesung und Korrektur-Overlay — Design

Stand: 2026-09-12. Baut auf dem reparierten Parser (Spec 2026-09-11) auf.
Antwortsprache und Bezeichner im Code: Deutsch. Nur Standardbibliothek, außer dort,
wo schon heute numpy/Pillow/pdftoppm gebraucht werden (Bildrendering).

## 1. Anlass

Der Parser liefert 3.338 Straßeneinträge, davon 272 mit `status=unsicher`. Die
Goldstandard-Stichprobe (50 Einträge) ist als Entwicklungs-Stichprobe verbraucht; ein
unabhängiges Qualitätsmaß für den Endstand fehlt. Einzelfehler (ein OCR-Zeichen, ein
exotisches Datum) lassen sich nicht sinnvoll über Parser-Regeln beheben, und es gibt
bisher keinen Weg, eine manuell geprüfte Korrektur in den Datensatz zu bringen.

Der Nutzer hat unbegrenzten API-Zugriff auf zwei bildfähige Open-Weight-Modelle
(`inferenz-qwen3-8-27b`, `inferenz-mistral-small-4-119b`) über einen
OpenAI-kompatiblen Inferenzserver.

**Nicht vorhanden:** PERO-OCR-Ergebnisse oder Koordinaten. Die OCR stammt aus
tesseract (`deu`, `--psm 3`), reiner Text je Buchseite. Vorhanden sind die beiden
PDFs (Doppelseiten, 300 dpi), die Bundsteg-Schnittpositionen (`ocr/bundsteg.tsv`) und
in `goldstandard.py` eine Funktion, die eine Buchseitenhälfte als PNG rendert.

## 2. Entscheidungen

Getroffen im Brainstorm 2026-09-12:

| Frage | Entscheidung | Begründung |
|---|---|---|
| Rolle des Modells | **Unabhängiger zweiter Leser** (Extraktion aus dem Bild), nicht Prüfer der Parser-Werte | Prüfer-Variante neigt zur Bestätigung und sieht Auslassungen nicht |
| Eingabe | **Nur das Seitenbild**, kein OCR-Text, keine Parser-Werte | OCR-Text würde die tesseract-Fehler in den zweiten Leser tragen; Unabhängigkeit ist der Wert |
| Einheit | **Ganze Buchseite**, 300 dpi Graustufen | Rendering vorhanden; fortlaufende Schlüsselnummern machen Vollständigkeit je Seite prüfbar; Zuschnitt je Eintrag erst, wenn Auslassungen auftreten |
| Umfang | **Alle 388 Seiten, beide Modelle** | Zugang unbegrenzt; liefert Fehlerkandidaten auch unter `automatisch` |
| Wirkung auf `status` (Option A) | **Keine.** Modelle ändern nichts; `status` ändert nur ein Mensch über das Overlay | LLM-Konsens ist kein Goldstandard. Ein späterer Schwenk zu Option B (Konsens hebt `unsicher`) wird in README und `qualitaet.md` ausgewiesen |
| Kalibrierung | **Trennung:** Prompt-Entwicklung an Seiten ohne Goldstandard-Eintrag; Goldstandard wird genau einmal gemessen | Unverbrauchte Fehlerquote je Modell |
| Korrekturen | **Overlay** `daten/korrekturen.csv`, Status `geprueft` (bereits im Schema-Enum) | Einzelfälle lösbar, Herkunft jeder Angabe sichtbar |

## 3. Architektur

```
PDFs ──(1) seiten.py──► llm/seiten/sNNN.png            (gitignored)
                              │
                     (2) llm_leser.py ─► llm/antworten/<modell>/sNNN.json   (gitignored)
                              │
daten/strassen.csv ──(3) llm_vergleich.py ─► daten/pruefung_llm.csv (versioniert)
daten/namen.csv                             docs/qualitaet.md (Abschnitt)
                                            docs/goldstandard/ergebnis_llm.md
                              │  Mensch prüft, trägt Korrekturen ein
                              ▼
daten/korrekturen.csv ──(4) korrekturen.py in erschliessen.main ─► strassen.csv/namen.csv
```

### 3.1 `strassen/seiten.py` — Seitenbilder

- `rendere_buchseite(buchseite, quelle_dir, ziel_png, dpi=300)`: nutzt
  `goldstandard.buchseite_zu_scan` und die (um einen `dpi`-Parameter erweiterte)
  Funktion `goldstandard.rendere_ausschnitt`. Graustufen-PNG.
- CLI `python3 -m strassen.seiten [--quelle DIR] [--seiten 23-30]`: rendert alle
  Buchseiten 2–388 nach `llm/seiten/sNNN.png`, überspringt vorhandene Dateien.
- `.gitignore`: `llm/` komplett (Seitenbilder und Rohantworten sind urheberrechtlich
  geschützte Inhalte bzw. Transkriptionen).

### 3.2 `strassen/llm_leser.py` — Leser

**Anbindung.** OpenAI-kompatibles `POST {LLM_BASE_URL}/chat/completions` mit
`urllib.request`, Bild als `data:image/png;base64,…` im `image_url`-Teil. Konfiguration:
Umgebungsvariablen `LLM_BASE_URL`, `LLM_API_KEY`; Modellname als CLI-Argument
`--modell`. Eine lokale `.env` wird gelesen, wenn vorhanden (einfacher
`KEY=WERT`-Parser, keine Abhängigkeit), und ist gitignored. `temperature=0`,
`max_tokens` großzügig (Seiten mit bis zu ~20 Einträgen).

**Prompt (fest, versioniert in `strassen/llm_prompt.md`).** Kernregeln:

- Transkribiere nur, was auf der Seite steht; nichts ergänzen, nichts modernisieren.
- Gib eine JSON-Liste aller Einträge der Seite. Ein Eintrag beginnt mit dem
  Straßennamen (Stichwort) und enthält `Schl.-Nr.:`. Einträge, die auf der Seite
  beginnen, aber nicht enden, werden bis zum Seitenende transkribiert und mit
  `"unvollstaendig": true` markiert; Einträge, die von der Vorseite hereinlaufen
  (kein Stichwort auf dieser Seite), werden ausgelassen.
- Felder je Eintrag: `schl_nr` (fünfstellig wie gedruckt), `lemma`, `stadtteile`
  (Liste), `strassenklasse` (Liste), `namensgruppe`, `verweis_auf` (nur bei „Siehe …"),
  `stadien` (Liste von `{"datum": "<wörtlich wie gedruckt>", "name": "…",
  "urspruenglich": true|false}`), `unvollstaendig`.
- Daten **wörtlich** („29.08.1927", „um 1900", „vor 1898", „16. Jh.", „1927"), keine
  Umformung. Namen mit Klammerzusätzen wie gedruckt („Victoriastraße (tlw.)").
- Der Erläuterungstext (Prosa nach der Namenskette) wird **nicht** transkribiert.

**Ablauf je Seite.** Antwort nach `llm/antworten/<modell>/sNNN.json` (Rohtext der
Modellantwort plus Metadaten: Modell, Zeitstempel, Prompt-Hash). Vorhandene Antwort
→ Seite überspringen (idempotent, `--neu` erzwingt). JSON-Extraktion tolerant
(Code-Fence, Text davor/danach); schlägt sie fehl, bis zu zwei Wiederholungen mit
identischem Prompt; danach `{"fehler": "unlesbar"}` speichern. HTTP-Fehler 429/5xx:
exponentielles Warten, maximal fünf Versuche, dann Abbruch des Laufs mit klarer
Meldung (die Seite bleibt ohne Antwort und wird beim nächsten Lauf nachgeholt).

CLI: `python3 -m strassen.llm_leser --modell NAME [--seiten 23-30] [--neu]`.

### 3.3 `strassen/llm_vergleich.py` — Vergleich

**Normalisierung.** Aus jeder Antwort werden Zeilen in der Form von `strassen.csv`
und `namen.csv` gebaut:

- `stadtteile`/`strassenklasse`: Liste mit `; ` gejoint (wie der Parser).
- `datum` → `gueltig_ab`/`datum_praezision` über `datum.DATUMSSTEMPEL` und
  `datum.lese_datum`; passt kein Muster: `datum_praezision=unbekannt`,
  `gueltig_ab=""`, und das Feld gilt als „Modell: Datum nicht normalisierbar"
  (eigene Zeile in der Prüfliste, damit ein Prompt- oder Musterproblem sichtbar wird).
- `ist_urspruenglich` aus `urspruenglich`.
- `buchseite` aus dem Dateinamen; `unvollstaendig=true`-Einträge werden gegen den
  Parser-Eintrag derselben `schl_nr` nur in den Kopffeldern verglichen, nicht in der
  Kette.

**Paarung und Vergleich.** `differenz.vergleiche` wird so erweitert, dass es neben
Verzeichnissen auch bereits geladene `(strassen, namen)`-Strukturen entgegennimmt
(`_lade` wird zu einer optionalen Vorstufe). Je Modell: Parser = „alt", Modell = „neu".
Zusätzlich ein Vollständigkeitsabgleich je Buchseite: Schlüsselnummern des Parsers
gegen die des Modells → Kategorien `eintrag_fehlt_modell` und `eintrag_nur_modell`
(Kandidat für eine Parser-Auslassung, die wichtigste Fundklasse).

**Ausgabe `daten/pruefung_llm.csv`** (versioniert; enthält nur Kopffeld- und
Namensinhalte, also dieselbe Informationsklasse wie der publizierte Datensatz):

```
schl_nr, buchseite, feld, wert_parser, wert_qwen, wert_mistral, status_parser, einig, korrektur, beleg
```

- Eine Zeile je Feld, bei dem mindestens ein Modell vom Parser abweicht. `feld` wie
  in der Goldstandard-Stichprobe (`lemma`, `stadtteile`, …, `stadium_N_datum`,
  `stadium_N_name`, außerdem `eintrag` für fehlende/überzählige Einträge).
- `einig`: `beide` (beide Modelle gleich und ≠ Parser), `eines` (nur ein Modell weicht
  ab oder Modelle uneins), `unlesbar` (mindestens eine Modellantwort fehlt).
- Sortierung: `beide` zuerst, dann `eines`, innerhalb nach `schl_nr`.
- `korrektur`, `beleg`: leer, Eingabemaske für den Menschen. Eingetragene Werte
  werden per `python3 -m strassen.llm_vergleich uebernehmen` als Zeilen nach
  `daten/korrekturen.csv` übertragen (Quelle `llm-lauf`), damit die Prüfliste bei
  einem Neulauf gefahrlos überschrieben werden kann.

**Kennzahlen** (Abschnitt „Unabhängige LLM-Lesung" in `docs/qualitaet.md`, erzeugt von
`veroeffentlichen.py`, wenn `pruefung_llm.csv` vorliegt): je Modell Anzahl gelesener
Seiten, unlesbare Seiten, Einträge gefunden/fehlend/überzählig, je Feldtyp
Übereinstimmungsquote mit dem Parser, getrennt nach `status_parser`. Dazu der Satz, dass
die Modelle den Status nicht verändern (Option A).

### 3.4 `strassen/korrekturen.py` — Overlay

**Datei `daten/korrekturen.csv`** (versioniert, Teil des Datensatzes):

```
schl_nr, feld, wert_alt, wert_neu, beleg, quelle, datum
```

- `feld`: `lemma`, `stadtteile`, `strassenklasse`, `namensgruppe`, `verweis_auf`,
  `stadium_N_datum`, `stadium_N_name`, `stadium_N_urspruenglich`, oder `eintrag`.
- `wert_alt`: der Parser-Wert zum Zeitpunkt der Prüfung. Stimmt er beim Anwenden
  nicht mehr mit dem aktuellen Parser-Wert überein, **bricht der Lauf mit Fehler ab**
  (der Parser liest die Stelle inzwischen anders; die Korrektur muss neu geprüft werden).
- Stadium nachtragen: `feld=stadium_N_datum` und `stadium_N_name` mit leerem
  `wert_alt`, N = Position in der gedruckten Kette; nachfolgende Parser-Stadien rücken
  auf. Stadium streichen: `wert_neu` leer bei beiden Feldern des Stadiums.
- `feld=eintrag`, `wert_alt` und `wert_neu` leer: **Bestätigung** — der Eintrag wurde
  vollständig gegen den Scan geprüft und ist korrekt; nur der Status ändert sich.
- `wert_neu` bei `stadium_N_datum` trägt den **gedruckten** Datumstext („29.08.1927",
  „um 1900"); `gueltig_ab`/`datum_praezision` entstehen daraus über `datum.lese_datum`,
  also mit derselben Funktion wie beim Parser und beim Leser. Nicht normalisierbarer
  Text → Fehler beim Anwenden.
- `beleg`: gedruckter Wortlaut (≤ 200 Zeichen), `quelle`: `goldstandard` oder
  `llm-lauf`, `datum`: ISO-Tag der Prüfung.

**Konvention.** Wer eine Korrekturzeile einträgt, hat den **ganzen Eintrag** gegen den
Scan geprüft (Kopf und Kette), nicht nur das eine Feld. Deshalb bekommt jeder Eintrag
mit mindestens einer Korrektur- oder Bestätigungszeile `status=geprueft`, und alle
Prüfgründe des Parsers für diesen Eintrag verfallen. `geprueft` ist die höchste Stufe
und wird in README und Data Dictionary so beschrieben.

**Anwendung.** `korrekturen.wende_an(strassen, namen, korrekturen) -> (strassen, namen,
protokoll)` läuft in `erschliessen.main` nach der Dubletten-Markierung und vor dem
Schreiben. Fehlende `schl_nr` → Fehler. `veroeffentlichen.py`: alle Filter
`status == "automatisch"` werden zu `status in ("automatisch", "geprueft")`
(Konkordanz-Ableitung, Erhebungsstand, Kennzahlen).

Erste Einträge: die Goldstandard-Fehler, die der Parser nicht behoben hat (3 von 17
laut Regressionstest), mit `quelle=goldstandard`.

### 3.5 Schema und Dokumentation

- `datapackage.json`: neue Ressource `korrekturen` (Felder wie oben); Beschreibung des
  Feldes `status` nennt alle drei Werte mit Bedeutung; `pruefung_llm.csv` wird als
  Prüfdatei (nicht als Datensatz-Ressource) im README-Publikationsumfang aufgeführt.
- README: Abschnitt „Bezifferte Qualität" bekommt „Unabhängige LLM-Lesung" mit den
  Kennzahlen und der Aussage zu Option A; Abschnitt „Methode" nennt Overlay und
  Statusstufen; Abhängigkeiten nennen den Inferenzzugang als optional (nur für die
  Neuerstellung der Prüfliste, nicht für die Nachvollziehbarkeit des Datensatzes).

## 4. Kalibrierung und Messung

1. **Entwicklungsseiten:** acht Buchseiten ohne Goldstandard-Eintrag, vier je Band,
   festgehalten in der Spec-Umsetzung (Plan). Prompt und JSON-Extraktion werden nur an
   diesen Seiten entwickelt; Ergebnisse werden dort manuell gegen den Scan geprüft.
2. **Goldstandard-Messung:** `python3 -m strassen.llm_vergleich goldstandard --modell
   NAME` liest die Antworten der Goldstandard-Seiten und vergleicht jedes Prüffeld der
   Stichprobe (`korrektur`, sonst `wert`, für `korrekt=ja`) mit dem Modellwert.
   Ausgabe `docs/goldstandard/ergebnis_llm.md`: Fehlerquote je Modell, Feldtyp und
   Schicht; nachgetragene Zeilen zählen als „vom Modell gefunden/nicht gefunden".
   Der Prompt wird danach **nicht** mehr geändert; muss er es doch, wird die Messung
   als Entwicklungs-Messung ausgewiesen.
3. **Volllauf** über alle 388 Seiten mit beiden Modellen, dann Vergleich und Prüfliste.

## 5. Tests

Standardbibliothek `unittest`, kein Netzzugriff:

- `tests/test_llm_leser.py`: JSON-Extraktion (Code-Fence, Vor-/Nachtext, ungültig);
  Anfrage-Aufbau (Bild-Base64, Modellname); Wiederholungslogik mit gefaktem
  `urlopen`; Idempotenz (vorhandene Antwort wird nicht neu angefordert).
- `tests/test_llm_vergleich.py`: Normalisierung einer gespeicherten Beispielantwort
  (Fixture aus einer Entwicklungsseite, nur Kopf/Kette) in Datensatzform;
  Vollständigkeitsabgleich; Sortierung und `einig`-Klassen der Prüfliste;
  Goldstandard-Auswertung an einer Mini-Stichprobe.
- `tests/test_korrekturen.py`: Feldkorrektur, Stadium nachtragen, Stadium streichen,
  Bestätigung, Abbruch bei abweichendem `wert_alt`, Abbruch bei unbekannter
  `schl_nr`, Statuswechsel und Verfall der Prüfgründe.
- `tests/test_differenz.py`: Erweiterung um den Struktur-Eingang.
- Bestehende Tests für `veroeffentlichen`/`stichtag` um `geprueft` erweitern.
- `tests/test_goldstandard_regression.py` bleibt grün (Overlay verändert die dort
  geprüften 17 Zeilen nur in Richtung „korrigiert").

## 6. Nicht-Ziele

- Keine Transkription oder Speicherung der Erläuterungstexte.
- Keine Statusänderung durch Modelle (Option A); kein automatisches Übernehmen von
  Modellwerten in den Datensatz.
- Kein Zuschnitt je Eintrag, keine Koordinaten, keine neue OCR (PERO o. ä.).
- Keine Veröffentlichung von Seitenbildern oder Rohantworten (`llm/` gitignored).
- Keine Änderung des Parsers selbst; Fundstellen des Laufs, die auf ein Muster
  hindeuten, werden in der Prüfliste gesammelt und sind Anlass für eine eigene
  Parser-Runde.
