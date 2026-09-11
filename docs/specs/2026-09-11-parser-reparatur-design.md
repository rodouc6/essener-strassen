# Parser-Reparatur nach der Goldstandard-Stichprobe — Design

Stand: 2026-09-11. Ergänzt die Stufe-2-Beschreibung in
`2026-08-20-strassenverzeichnis-datensatz-design.md`, Abschnitt 3.

## 1. Anlass

Die Goldstandard-Stichprobe (50 Einträge, Seed 1936, Ergebnis in
`docs/goldstandard/ergebnis.md`) fand 17 Feldfehler in 8 Einträgen. Alle gehen auf
systematische Parser- oder OCR-Muster zurück, keiner auf Zufall. Die Nachmessung auf dem
Gesamtmaterial (3.338 Einträge) zeigte, dass die Stichprobe nur die Spitze zeigt: Die
größte Einzelursache ist ein Fallback in `kopf.parse_kopf`, der den Text bei
fehlgeschlagener Kettenerkennung am ersten „. " zerschneidet — also an der Tagesziffer
eines völlig sauber gedruckten Datums. Das allein kostet 38 Namensketten.

Ein Wegwerf-Prototyp der Kernregeln ergab auf dem Gesamtmaterial:

| Kennzahl | vorher | Prototyp |
|---|--:|--:|
| Straßen ohne Namenskette | 84 | 40 |
| Namensstadien | 5.283 | 5.370 |
| Namen, die nur aus „St", „I", „II", „IV" bestehen | 16 | 0 |
| leere Straßenklasse | 54 | 45 |
| unsichere Einträge (ohne Dubletten/Anker) | 236 | 202 |

Regressionen des Prototyps: 7 auffällige Einträge, davon 3 tatsächliche Verbesserungen,
1 echter Fehler (Tag 85, durch Validierung abzufangen), 3 Verluste eines Stadiums mit
OCR-verstümmeltem Datum, die vom alten Code still auf bloßes Jahr degradiert und jetzt
sichtbar als `unsicher` markiert werden. Stille Regressionen: keine gefunden.

**Entscheidungen (Projektinhaber, 2026-09-11):** voller Regelkatalog; tolerante
Erkennungen werden extrahiert **und** gekennzeichnet; leere Kopffelder werden Prüfgrund
mit `status=unsicher`; Jahrhundert-Datierungen erhalten die neue Präzision
`jahrhundert`; keine neue Stichprobe.

## 2. Ziel und Erfolgskriterien

- Alle 17 Goldstandard-Fehler sind entweder korrigiert oder der betroffene Eintrag ist
  `unsicher` (precision-first: korrigiert oder gekennzeichnet, nie still falsch).
- Kein Eintrag verliert ein Stadium oder ändert ein Datum, ohne dass die Änderung im
  Differenzbericht steht und am OCR-Text geprüft wurde.
- Die Datumslogik existiert genau einmal (`strassen/datum.py`).
- Die Fehlerquote der Schicht `automatisch` (Goldstandard: 0,3 %) bleibt haltbar, weil
  die bislang unmarkierte Fehlerklasse „leeres Kopffeld" jetzt markiert ist.

## 3. Architektur

### 3.1 Neues Modul `strassen/datum.py`

Eine Quelle für alle Datumsstempel und für die Satzende-Regel. Öffentliche Schnittstelle:

```python
class Datum(NamedTuple):
    gueltig_ab: str          # ISO-Datum, Jahr, oder leer
    praezision: str          # tag | jahr | vor | nach | jahrhundert | unbekannt
    hinweis: str             # "" oder Prüfgrund (s. Abschnitt 4, Regeln 14–18)

DATUMSSTEMPEL: re.Pattern    # alle Varianten, endet am Trennzeichen zum Namen
SATZENDE: str                # Regex-Baustein: Punkt, der ein Satzende ist

def lese_datum(match) -> Datum          # ungültiger Tag/Monat: Jahresform + Hinweis
```

`DATUMSSTEMPEL` erkennt: `dd. Monat jjjj:`, `dd, Monat jjjj:`, `dd.mm.jjjj:`,
`vor|nach|um|etwa|gegen jjjj:`, `jjjj:`, `jjjj/jj:`, `N. Jahrhundert:` /
`N. Jahrh.:`, sowie jede dieser Formen mit Komma, Semikolon oder ohne Trennzeichen statt
Doppelpunkt (Regel 15). Ein Tagesdatum mit ungültigem Tag (z. B. „085. Februar 1929")
wird nicht verworfen, sondern auf die Jahresform reduziert (`praezision=jahr`) und mit
dem Hinweis „Datum: Tag ungültig" versehen (Regel 6) — das Jahr ist korrekt, der
Informationsverlust wird sichtbar. Der Monatsname wird gegen `MONATE` geprüft; ein Wort mit
Levenshtein-Distanz 1 zu genau einem Monatsnamen gilt als OCR-korrigiert (Regel 16).

`SATZENDE`: ein Punkt, der **nicht** unmittelbar auf eine Ziffer, auf „St" oder auf eine
römische Zahl I–IV folgt, und auf den Leerzeichen + Großbuchstabe/Ziffer oder das
Stringende folgt. `kopf._NAMENSTEIL`, `kopf._STADIUM`, `namen._NAME`, die Feldgrenzen
in `kopf` und der Fallback benutzen ausschließlich diesen Baustein.

### 3.2 Änderungen in `kopf.py`

- Feldgrenzen `_STADTTEIL`, `_KLASSE`, `_GRUPPE`: Satzende über `datum.SATZENDE`
  statt `\.\s`; Komma vor dem Datumsstempel optional (`,?\s*`); `_GRUPPE` endet
  zusätzlich vor einer Tagesziffer `\d{1,2}[.,]\s` (Regel 3), damit die Namensgruppe
  auch bei verstümmeltem Datum sauber bleibt.
- Fallback ohne erkannte Kette: `rest` reicht bis zum ersten `SATZENDE`, nicht bis
  zum ersten „. " (Regel 1).
- `_M_KLASSE` toleriert `KL`, `K.`, `Kt`, `Str:-` und `;` statt `:` (Regel 9).
- Klassenwort ohne Marker (Regel 19): fehlt der Marker, aber zwischen Stadtteil und
  `Str.-Gr.` steht ein Wort aus dem geschlossenen Vokabular {Gemeindestraße,
  Kreisstraße, Landstraße, Hauptstraße, Bundesstraße}, wird es übernommen. Klassenwert
  mit Levenshtein-Distanz 1 zum Vokabular wird korrigiert (Regel 20). Beides liefert
  einen Hinweis. `Kopf` bekommt dafür ein Feld `hinweise: list[str]`.

### 3.3 Änderungen in `namen.py`

- `_STADIUM` wird durch `datum.DATUMSSTEMPEL` + Namensmuster ersetzt; `_NAME` nutzt
  `datum.SATZENDE`.
- `urspr.` ohne Doppelpunkt wird erkannt, mit Hinweis (Regel 17).
- `Stadium` erhält das Feld `hinweis: str`.
- Regel 15 (Stempel ohne Doppelpunkt) gilt nur, wenn der Treffer entweder am Anfang
  von `rest` steht oder unmittelbar (nach Komma/Leerzeichen) auf ein vorheriges Stadium
  folgt — nie tief in der Erläuterung. `kopf` liefert `rest` ohnehin auf die Kette
  begrenzt; diese Bedingung ist die zweite Sicherung.

### 3.4 Änderungen in `segmentierung.py`

`_LEMMA` erlaubt den Punkt einer „St."-Abkürzung mit folgendem Leerzeichen als
Lemma-Bestandteil (Regel 5), so wie heute schon „St.-" mit Bindestrich.

### 3.5 Änderungen in `aufbereitung.py`

- `_ABSCHNITTSKOPF` auch für eine Zeile mit einem einzelnen Kleinbuchstaben (Regel 11;
  im Material 29 solche Zeilen, 1 echter Abschnittskopf „c", 28 Rauschen — beides wird
  entfernt, nichts Legitimes geht verloren).
- Randrauschen (Regel 12): erste und letzte nichtleere Zeile einer Seite wird
  entfernt, wenn sie ausschließlich aus Wörtern mit höchstens 3 Buchstaben besteht und
  weder Ziffer noch Satzzeichen enthält. Gilt nur an Seitenrändern.
- Stadtteil-Marker (Regel 10): `Stadtt?ei[l!t]`, `Stadteil`, `Stadt-teil` (auch ohne
  Zeilenumbruch), `Stadtteil` direkt vor Großbuchstabe ohne Leerzeichen — alle zu
  `Stadtteil ` bzw. `Stadtteile `.
- `xundX` → `x und X` nur zwischen Klein- und Großbuchstabe (Regel 13).

### 3.6 Änderungen in `erschliessen.py`

- Neue Prüfgründe: „Stadtteil fehlt", „Straßenklasse fehlt" (Regel 21; ausgenommen
  Verweis-Einträge mit „Siehe" im Kopfbereich und ohne Namenskette), sowie jeder
  `hinweis` aus `Stadium` und `Kopf.hinweise` wörtlich als Grund.
- Jeder Grund führt wie bisher zu `status=unsicher`.

### 3.7 Schema

`datum_praezision` erhält den Wert `jahrhundert`; `gueltig_ab` trägt dann das erste
Jahr des Jahrhunderts (16. Jh. → `1501`). `stichtag._vergleichbar` behandelt
vierstellige Werte bereits konservativ als Jahresende; für die Konkordanz 1936 sind alle
Jahrhundert-Stadien ohnehin Jahrhunderte älter als der Stichtag. Zu ändern:
`datapackage.json` (enum), README (Feldtabelle `namen.csv` und Kennzahlen), Spec
2026-08-20 Abschnitt 4.

## 4. Regelkatalog

Fallzahlen aus der Nachmessung im Kopfbereich aller Einträge (2026-09-11).
„sicher" = deterministisch, kein Prüfgrund. „tolerant" = Wert wird übernommen, Eintrag
erhält den genannten Prüfgrund und `status=unsicher`.

| Nr. | Muster | Fälle | Ort | Einstufung |
|---|---|--:|---|---|
| 1 | Fallback zerschneidet `rest` am Tagespunkt | 38 | kopf | sicher (Bugfix) |
| 2 | Feldgrenze `. ` springt auf Tagesziffer; Komma vor Datum fehlt | 46 | kopf | sicher (Bugfix) |
| 3 | Namensgruppe endet vor Tagesziffer, auch bei verstümmeltem Datum | – | kopf | sicher |
| 4 | Punkt nach „St." / röm. Zahl beendet Namen | 16 | datum | sicher |
| 5 | Lemma „St. X" mit Leerzeichen | 15 | segmentierung | sicher |
| 6 | Tagesvalidierung 1–31, Monat gültig; sonst nur Jahr | ≥1 | datum | tolerant: „Datum: Tag ungültig" |
| 7 | numerisches Datum `dd.mm.jjjj:` | 7 | datum | sicher |
| 8 | `N. Jahrhundert:` / `Jahrh.:` → `jahrhundert` | 8 | datum | sicher |
| 9 | Marker `Str.-KL:`, `Str.-K.:`, `Str.-Kt.:`, `Str:-Kl`, `Str.-Kl.;` | 23 | kopf | sicher |
| 10 | Stadtteil-Marker-Varianten | 13 | aufbereitung | sicher |
| 11 | Abschnittskopf als Kleinbuchstabe-Zeile | 29 | aufbereitung | sicher |
| 12 | Randrauschen erste/letzte Zeile | 36 | aufbereitung | sicher |
| 13 | `xundX` → `x und X` | 1 | aufbereitung | sicher |
| 14 | Komma nach Tag `13, Juni 1973:` | 17 | datum | tolerant: „Datum: Komma nach Tag" |
| 15 | Stempel ohne Doppelpunkt bzw. mit Komma/Semikolon | 48 | datum | tolerant: „Datum ohne Doppelpunkt" |
| 16 | Monatsname mit einem OCR-Fehler, eindeutig | ~10 | datum | tolerant: „Monatsname OCR-korrigiert" |
| 17 | `urspr.` ohne Doppelpunkt | 8 | namen | tolerant: „urspr. ohne Doppelpunkt" |
| 18 | Doppeljahr `1910/11:` → Jahr 1910 | 1 | datum | tolerant: „Datum: Doppeljahr" |
| 19 | Klassenwort ohne Marker, geschlossenes Vokabular | 13 | kopf | tolerant: „Straßenklasse ohne Marker" |
| 20 | Klassenwert mit einem OCR-Fehler (`Gemeindstraße`) | 5 | kopf | tolerant: „Straßenklasse OCR-korrigiert" |
| 21 | Stadtteil / Straßenklasse leer | 14 / 54 | erschliessen | Prüfgrund „Stadtteil fehlt" / „Straßenklasse fehlt" |

Nicht durch Regeln lösbar und bewusst nicht versucht: OCR-Rauschen in Namen und
Namensgruppen („Minnesängerr", „Deutschen"), verstümmelte Jahreszahlen („19862",
„19377"), Rauschen mitten im Datum („28. Mai Tas Echstenkämperweg 1919"). Diese Fälle
bleiben `unsicher` und sind die Zielmenge des später geplanten LLM-Prüfschritts.

## 5. Sicherungen

### 5.1 Differenzlauf `strassen/differenz.py`

Vergleicht zwei Stände von `strassen.csv` und `namen.csv` (Pfade als Argumente, z. B.
`git show HEAD:daten/…` gegen den neuen Lauf) je Schlüsselnummer und schreibt einen
Markdown-Bericht mit Zählung und Einzelliste je Kategorie:

- Stadium gewonnen / verloren
- Datum verändert (alt → neu, Präzision alt → neu)
- Name verändert
- Kopffeld verändert (lemma, stadtteile, strassenklasse, namensgruppe)
- Statuswechsel `automatisch → unsicher` und `unsicher → automatisch`, mit Gründen
- Einträge neu / entfallen

Bericht: `docs/regression/2026-09-parser-reparatur.md`. Jeder Verlust und jede
Umdatierung wird vor der Übernahme am OCR-Text geprüft und im Bericht kommentiert.

### 5.2 Goldstandard-Regressionstest

`tests/test_goldstandard_regression.py` liest `docs/goldstandard/stichprobe.csv`,
parst die betroffenen OCR-Seiten und prüft je Zeile mit `korrekt=nein`: der Parser
liefert jetzt den Wert aus `korrektur`, **oder** der Eintrag ist `unsicher`. Der Test
wird übersprungen (`pytest.skip`), wenn `ocr/seiten/` fehlt. Die Stichprobe bleibt
eingefroren; ihre Spalte `wert` dokumentiert den Stand vor der Reparatur.

### 5.3 TDD je Regel

Jede Regel bekommt vor der Implementierung mindestens einen Test mit einem realen
Beleg aus dem Material (Schlüsselnummer und Seite im Testnamen oder Docstring, wie in
den bestehenden Tests). Bestehende Tests bleiben unverändert grün; wo ein Test altes
Fehlverhalten festschreibt, wird das im Commit begründet.

## 6. Regeneration und Dokumentation

Nach grünem Testlauf: `python3 -m strassen.erschliessen`, `validierung`,
`veroeffentlichen`, Differenzbericht, dann Kennzahlen in README („Bezifferte
Qualität", `namen.csv`-Verteilung der Präzision, Konkordanz-Zeilen) und
`docs/qualitaet.md` aktualisieren. `docs/goldstandard/ANLEITUNG.md` verweist bereits
auf die Entwicklungs-Stichprobe; `ergebnis.md` bleibt als Stand vor der Reparatur.

## 7. Nicht-Ziele

- Kein Neuschrieb des Kopf-Parsers als Tokenizer.
- Keine neue Goldstandard-Ziehung.
- Keine Korrektur von OCR-Rauschen in Namen, Namensgruppen oder Jahreszahlen.
- Kein LLM-Schritt (eigenes Vorhaben danach).
- Keine Änderung am Kartenprojekt; die Konkordanz wird nur neu erzeugt.
