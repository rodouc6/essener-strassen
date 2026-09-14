# Essener Straßenverzeichnis: Namen und Umbenennungen

> **Abstract (English).** A structured, dated inventory of Essen's streets and their
> naming history, derived from Erwin Dickhoff's reference work *Essener Straßen*
> (Klartext-Verlag, Essen 2015, ISBN 978-3-8375-1231-1). Each street carries its
> official key number, district(s), road class, and a chronological sequence of name
> stages with dated transitions — enabling the resolution of historical Essen addresses
> to any given cutoff date. Derived by OCR (page-split at the book's gutter) and a
> deterministic, rule-based parser (no language model) from a scanned two-volume copy
> of the source; the pipeline, validation checks, and known limitations are documented
> below. Explanatory text (name origins, biographies) from the source is **not**
> included. Data licensed CC BY 4.0 for the derived structure and code; the underlying
> facts remain attributable to Dickhoff 2015 (see [Lizenz](#lizenz-und-zitierhinweis)).

## Was der Datensatz enthält — und was nicht

Der Datensatz erfasst für jede im Werk aufgeführte Essener Straße:

- die amtliche Schlüsselnummer, den/die Stadtteil(e), die Straßenklasse und die
  Namensgruppe (Flurname, Person, Lagebezeichnung …),
- die vollständige, datierte Kette ihrer Namensstadien (wann welcher Name galt),
- den Beleg (Buchseite bei Dickhoff 2015) je Eintrag,
- eine daraus abgeleitete Konkordanz zum Namensstand des Adressbuchs Essen 1936.

**Ausdrücklich nicht enthalten** sind Dickhoffs Erläuterungstexte — Namensherkunft,
Hofgeschichte, Biographien, Literaturangaben. Diese sind urheberrechtlich geschützter
Fließtext und bleiben lokaler Arbeitsstand außerhalb dieser Veröffentlichung (siehe
[Lizenz](#lizenz-und-zitierhinweis)). Ebenfalls nicht enthalten: Geometrien/Geokodierung
(der Datensatz führt Namen, keine Koordinaten) und die OCR-Rohtexte der Buchseiten
(`ocr/seiten/`, per `.gitignore` von der Veröffentlichung ausgeschlossen — siehe
[Publikationsumfang](#publikationsumfang)).

## Quelle

Erwin Dickhoff: *Essener Straßen.* Klartext-Verlag, Essen 2015.
ISBN 978-3-8375-1231-1.

Vorlage war ein Scan in zwei Bänden (100 + 94 Doppelseiten, Buchseiten 2–201 und
202–388), 300 dpi, ohne Textebene — insgesamt 388 Buchseiten.

## Methode

Die Doppelseiten wurden bei 300 dpi gescannt, am erkannten Bundsteg (weißer
Mittelstreifen, Position variiert zwischen Seiten) in linke und rechte Buchseite
geteilt und je Hälfte mit Tesseract OCR (`deu`) gelesen, um die Buchseitenzahl als
Beleg zu sichern. Ein regelbasierter, deterministischer Parser — bewusst kein
Sprachmodell, damit Fehler sichtbar scheitern statt plausibel falsche Angaben zu
erzeugen — segmentiert die 388 OCR-Seiten in 3.354 Einträge und zerlegt jeden
Eintragskopf in Schlüsselnummer, Stadtteil, Straßenklasse, Namensgruppe und die
datierte Namensstadien-Kette. Dabei markieren Plausibilitäts-Heuristiken der
Erschließung selbst (`strassen/erschliessen.py`: z. B. ein auffällig langes oder
falsch geformtes Lemma, ein nicht erkennbares Namensstadium, eine mehrfach
vergebene Schlüsselnummer) auffällige Einträge unmittelbar beim Parsen als
`status=unsicher`, statt sie stillschweigend durchzulassen — die jeweilige
Begründung landet in `daten/pruefung.csv`.

Davon **unabhängig** laufen anschließend, auf dem fertigen `daten/strassen.csv`,
drei weitere Selbstprüfungen (Schlüsselnummern-Fortlauf, alphabetische Ordnung,
Abgleich mit dem amtlichen Straßenverzeichnis, `strassen/validierung.py`) als
zusätzlicher Gegen-Check. Sie **setzen `status` nicht neu**, sondern erzeugen den
Qualitätsbericht [`docs/qualitaet.md`](docs/qualitaet.md) und die Prüfliste
[`daten/pruefung_validierung.csv`](daten/pruefung_validierung.csv) (nur Lemma,
Schlüsselnummer, Grund — keine Textzitate) und weisen dort aus, welcher Anteil
ihrer Treffer bereits über die Erschließungs-Heuristiken als `unsicher` markiert
war und welcher neu auffällt (d. h. bisher `automatisch` war, s.
[Bezifferte Qualität](#bezifferte-qualität)). Aus den Namensstadien wird
schließlich, für einen historisch begründeten Stichtag, eine Konkordanz zum
Namensstand des Adressbuchs Essen 1936 abgeleitet
(`strassen/veroeffentlichen.py`, s. u.).

### Stufe 5 — Unabhängige LLM-Lesung und Korrektur-Overlay

Zusätzlich zu den drei Selbstprüfungen lesen zwei Sprachmodelle unabhängig voneinander
die Seitenbilder direkt (`strassen/seiten.py` rendert alle Buchseiten als ganzseitige Bilder,
`strassen/llm_leser.py` fragt die Modelle über einen OpenAI-kompatiblen Endpunkt ab) — **ohne**
den OCR-Text zu sehen, damit ein gemeinsamer OCR-Fehler nicht unentdeckt bleibt. Weichen
beide Modell-Lesungen oder eine Modell-Lesung vom Datensatz ab, landet der Fall in
`daten/pruefung_llm.csv` (`strassen/llm_vergleich.py`, Unterbefehl `pruefliste`); ein Mensch
prüft jeden Fund gegen den Scan und trägt bestätigte Korrekturen in `daten/korrekturen.csv`
ein (`strassen/llm_vergleich.py uebernehmen` übernimmt sie aus der geprüften Prüfliste).
Das Korrektur-Overlay wendet `strassen/erschliessen.py` als letzten Schritt auf die
Parser-Ausgabe an (`strassen/korrekturen.py`); jeder betroffene Eintrag erhält
`status=geprueft` — die höchste Stufe, weil sie bedeutet: der ganze Eintrag wurde gegen den
Scan geprüft, nicht nur das korrigierte Feld (s. Data Dictionary). **Wichtig:** Die
Modell-Lesung selbst ändert den Status nie — nur eine von einem Menschen bestätigte
Korrektur tut das (Option A: Modelle liefern Prüfhinweise, keine automatischen
Übernahmen). Ein späterer Schwenk zu automatischer Übernahme würde hier ausdrücklich
ausgewiesen. `daten/pruefung.csv`, das Parser-Protokoll der Erschließung, wird durch
Korrekturen **nicht** bereinigt — seine Einträge bleiben stehen, auch wenn der
zugehörige Datensatz-Eintrag inzwischen `status=geprueft` trägt; maßgeblich für den
aktuellen Stand ist der Status in `strassen.csv`, nicht `pruefung.csv`.

Näheres zur Ankererkennung, zur OCR-Fehlertoleranz und zur Stufenarchitektur:
[`docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md`](docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md),
Abschnitt 3.

### Abhängigkeiten

Der Parser (`strassen/aufbereitung.py`, `segmentierung.py`, `kopf.py`, `namen.py`,
`validierung.py`, `stichtag.py`, `ausgabe.py`, `veroeffentlichen.py`) ist **reine
Standardbibliothek** (`re`, `csv`, `pathlib`, `unicodedata`, `argparse`) — bewusst
ohne Installationshürde, damit er ohne Zusatzaufwand nachvollziehbar bleibt. Nur das
OCR-Skript (`strassen/ocr_lauf.py`, `python3 -m strassen.ocr_lauf <Quellverzeichnis>`,
das die beiden Dickhoff-PDFs in `ocr/seiten/` zerlegt) braucht zusätzlich:

- **numpy**, **Pillow** — Bundsteg-Erkennung und Bildzuschnitt
- **tesseract-ocr** mit dem Sprachpaket **deu** — die eigentliche OCR
- **poppler-utils** (`pdftoppm`) — PDF-Seiten zu PNG rendern

Da die PDFs und `ocr/seiten/` selbst nicht veröffentlicht werden (s.
[Publikationsumfang](#publikationsumfang)), betrifft das ausschließlich die lokale
Neuerstellung des OCR-Rohtexts, nicht die Nachvollziehbarkeit des veröffentlichten
Datensatzes.

Für die **Neuerstellung der LLM-Prüfliste** (`strassen/llm_vergleich.py pruefliste`,
`strassen/llm_leser.py`) braucht es zusätzlich optional Zugang zu einem
OpenAI-kompatiblen Inferenzendpunkt, konfiguriert über die Umgebungsvariablen
`LLM_BASE_URL` und `LLM_API_KEY` (lokal per `.env`, per `.gitignore` von der
Veröffentlichung ausgeschlossen); da der Endpunkt je Modell einen eigenen Schlüssel
verlangt, sticht ein modellspezifischer `LLM_API_KEY_QWEN`/`LLM_API_KEY_MISTRAL` den
allgemeinen `LLM_API_KEY`, falls beide gesetzt sind. Ohne diesen Zugang bleibt die bereits geprüfte
Prüfliste (`daten/pruefung_llm.csv`) unverändert nutzbar; das Korrektur-Overlay
(`daten/korrekturen.csv`, `strassen/erschliessen.py`) braucht ihn nicht.

Die Chronik der Entscheidungen steht in [`docs/vorgehen.md`](docs/vorgehen.md).

## Data Dictionary

Zwei verknüpfte Tabellen statt einer flachen Konkordanz, weil ein Straßeneintrag
Eigenschaften der Straße *und* eine Folge von Namensstadien trägt (1:n) — das
maschinenlesbare Schema liegt zusätzlich in [`datapackage.json`](datapackage.json)
(Frictionless-Format).

### `daten/strassen.csv` (3.349 Zeilen)

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `schl_nr` | amtliche Schlüsselnummer, fünfstellig | Primärschlüssel, eindeutig (3 Dubletten dokumentiert, s. u.) |
| `lemma` | heutiger Straßenname (Stichwort des Eintrags) | Text |
| `stadtteile` | Stadtteil(e) | mehrere durch `; ` getrennt |
| `strassenklasse` | Straßenklasse | Gemeindestraße, Kreisstraße, Landstraße, Bundesstraße, Autobahn, Hauptstraße …; mehrere durch `; ` getrennt; bei `status=unsicher` z. T. OCR-verunreinigt |
| `namensgruppe` | Str.-Gr. der Quelle, wörtlich übernommen | Text (Flurname, Person, Lagebezeichnung, Stadt und Ort …) |
| `verweis_auf` | Ziel-Lemma bei „Siehe X" | Text oder leer (225 von 3.349 Zeilen gefüllt) |
| `buchseite` | Beleg: Seite in Dickhoff 2015 | ganzzahlig, 23–362 (Einträge nur im Lexikonteil; das Buch umfasst die Scan-Seiten 2–388, Titelei/Einleitung/Register enthalten keine Einträge) |
| `status` | Prüfstatus des Eintrags | `automatisch` (Parser ohne Prüfgrund) \| `unsicher` (Parser mit Prüfgrund, Wert übernommen und gekennzeichnet) \| `geprueft` (Eintrag vollständig gegen den Scan geprüft, Korrekturen über `daten/korrekturen.csv` angewandt — höchste Stufe) |

### `daten/namen.csv` (5.513 Zeilen)

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `schl_nr` | Fremdschlüssel auf `strassen.csv` | siehe oben |
| `stadium` | laufende Nummer der Namensstufe | ganzzahlig, 1 = älteste |
| `gueltig_ab` | Datum, ab dem der Name in diesem Stadium galt | ISO-Datum, Jahr, erstes Jahr eines Jahrhunderts bei `jahrhundert`, oder leer bei `unbekannt` |
| `datum_praezision` | Genauigkeit der Datierung | `tag` \| `monat` \| `jahr` \| `jahrhundert` (nur Jahrhundert bekannt; `gueltig_ab` = erstes Jahr, z. B. 16. Jh. → 1501) \| `vor` \| `nach` \| `unbekannt` |
| `name` | Straßenname in diesem Stadium | Text |
| `ist_urspruenglich` | Angabe stammt aus Dickhoffs `urspr.:`-Vermerk ohne Datum | `wahr` \| `falsch` |

Primärschlüssel: (`schl_nr`, `stadium`). Beispiel (Schl.-Nr. 01838, Buchseite 211):

```
01838, 1, 1904-11-18, tag, Kirchstraße,    falsch
01838, 2, 1926-06-01, tag, Klosterstraße,  falsch
01838, 3, 1937-11-20, tag, Kütings Garten, falsch
```

Damit lässt sich der Name der Straße zu jedem beliebigen Stichtag ableiten — nicht nur
zum Erhebungsstand 1936.

### `daten/konkordanz_1936.csv` (473 Zeilen)

Abgeleitet aus `namen.csv`: für jede Straße mit `status=automatisch` das Namensstadium,
das zum Erhebungsstand des Adressbuchs Essen 1936 galt (Arbeitsstichtag **1936-06-30**,
begründet in [`docs/erhebungsstand.md`](docs/erhebungsstand.md)), verknüpft mit dem
heutigen Namen.

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `stadtteil` | Stadtteil der Straße | Text |
| `ehemalig` | Name zum Erhebungsstand 1936, Klammerzusatz bereits abgetrennt | Text |
| `heutig` | heutiger Name (`lemma` aus `strassen.csv`) | Text |
| `schl_nr` | amtliche Schlüsselnummer | siehe oben |
| `datum_praezision` | Genauigkeit der zugrunde liegenden Datierung | wie in `namen.csv` |
| `quelle` | Herkunft der Angabe | wörtlich „Dickhoff 2015" |
| `zusatz` | abgetrennter Klammerzusatz aus der Quelle | z. B. „(tlw.)", „(Verl.)"; leer wenn keiner vorlag (173 von 473 Zeilen gefüllt) |
| `eindeutig` | ob `(stadtteil, ehemalig)` auf genau eine `schl_nr` trifft | `ja` (386) \| `nein` (39, Kollisionen) |

Straßen mit `status=unsicher` gehen **nicht** in die Konkordanz ein, da ihr heutiger
Name selbst nicht belastbar ist. Einträge, deren Namenskette intern widersprüchlich ist
(letztes Stadium ≠ Lemma), werden nicht in die Konkordanz aufgenommen, sondern als
Prüffall geführt (s. [Bekannte Grenzen](#bekannte-grenzen)).

### `daten/korrekturen.csv`

Korrektur-Overlay (Stufe 5, s. o.): manuell gegen den Scan geprüfte Korrekturen, die
`strassen/erschliessen.py` als letzten Schritt auf die Parser-Ausgabe anwendet. Jede
Zeile bestätigt oder korrigiert **ein Feld eines Eintrags** — wer eine Zeile einträgt,
hat den ganzen Eintrag (Kopf und Namensstadien-Kette) gegen den Scan geprüft, deshalb
erhält der betroffene Eintrag `status=geprueft`, auch wenn nur ein Feld tatsächlich
abweicht.

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `schl_nr` | Fremdschlüssel auf `strassen.csv` | siehe oben |
| `feld` | geprüftes Feld | `lemma` \| `stadtteile` \| `strassenklasse` \| `namensgruppe` \| `verweis_auf` \| `buchseite` \| `schl_nr` (`wert_alt` = Lemma des Eintrags, `wert_neu` = neue Nummer) \| `stadium_N_datum` \| `stadium_N_name` \| `stadium_N_urspruenglich` \| `eintrag` (`wert_alt`/`wert_neu` leer: Bestätigung ohne Wertänderung; `wert_neu` = Lemma: Neuanlage eines vom Parser ausgelassenen Eintrags, gefüllt durch die weiteren Zeilen derselben Nummer). Ein Nachtrag mit `wert_neu = vorm.`, `zuvor` bzw. `urspr.` im Datumsfeld legt ein undatiertes Stadium an (`datum_praezision=unbekannt`; `ist_urspruenglich` `falsch` bzw. `wahr`) |
| `wert_alt` | Parser-Wert zum Prüfzeitpunkt, in Stichprobenform (z. B. `vor 1898`) | Text; leer = Stadium an Position N wird nachgetragen; weicht der Wert beim Anwenden vom aktuellen Parser-Ergebnis ab, bricht der Lauf ab — die Stelle muss neu geprüft werden |
| `wert_neu` | korrigierter Wert | Text; bei Daten der **gedruckte** Text (z. B. `29.08.1927`), nicht die ISO-Form; leer bei beiden Feldern eines Stadiums (`stadium_N_datum` und `stadium_N_name`) = Stadium wird gestrichen |
| `beleg` | gedruckter Wortlaut der geprüften Stelle | Text, ≤ 200 Zeichen |
| `quelle` | Herkunft der Korrektur | `goldstandard` \| `llm-lauf` |
| `datum` | Tag der Prüfung | ISO-Datum |

Diese Datei ist **Eingabe** von `strassen/erschliessen.py`, nicht dessen Protokoll —
das bleibt `daten/pruefung.csv` (s. u.), das durch Korrekturen **nicht** bereinigt
wird; wirksam wird eine Korrektur im Datensatz über `status=geprueft` und die
korrigierten Werte selbst, nicht über eine Änderung an `pruefung.csv`.

## Bezifferte Qualität

- **388** OCR-Buchseiten → **3.354** vom Parser segmentierte Einträge.
- `daten/strassen.csv`: **3.354** Zeilen (3.349 vom Parser, 5 per Overlay nachgetragen), davon
  **4** mit `status=unsicher` (**2.980** `automatisch`, **370** `geprueft`).
- `daten/namen.csv`: **5.513** Namensstadien (Datierungsgenauigkeit: **4.777** `tag`,
  **334** `unbekannt`, **211** `jahr`, **182** `vor`, **9** `jahrhundert`).
- `daten/konkordanz_1936.csv`: **473** Zeilen (**424** `eindeutig=ja`, 49 `eindeutig=nein`;
  **173** mit Klammerzusatz).

### Drei unabhängige Selbstprüfungen

| Prüfung | Ergebnis |
|---|---|
| Schlüsselnummern (amtlich, 1–3771 erwartet) | 3.349 erfasst, 425 Lücken, **3 Dubletten** |
| alphabetische Ordnung der Lemmata | **31** aus der Sortierung fallende Lemmata (0 bereits als `unsicher` markiert, 31 neu auffällig) |
| Abgleich mit dem amtlichen Straßenverzeichnis (`strassen_aktuell.csv`) | **3.339** bestätigt, 15 nicht im Verzeichnis (erwartbar bei aufgehobenen Straßen) |

Details, Methodik und Interpretation: [`docs/qualitaet.md`](docs/qualitaet.md); die
konkreten Treffer (Lemma, Schlüsselnummer, Grund): `daten/pruefung_validierung.csv`.

### Unabhängige LLM-Lesung

Zwei Sprachmodelle lesen die ganzseitigen Seitenbilder unabhängig voneinander und ohne
Kenntnis des OCR-Texts (s. [Methode, Stufe 5](#stufe-5--unabhängige-llm-lesung-und-korrektur-overlay)).
Volllauf vom 2026-09-12/13, Prompt-Stand `530d5c9e77b5`:

- Gelesene Buchseiten: **387** bei `mistral` (0 unlesbar) und **381** bei `qwen`; dort sind
  nach einmaligem Nachfassen **6** Seiten unlesbar geblieben (122, 171, 199, 206, 225, 355).
- Eigene Fehlerquote gegen die menschlich geprüfte Goldstandard-Stichprobe (478 Prüffelder):
  **6,1 %** (`qwen`, 449 korrekt) und **22,4 %** (`mistral`, 371 korrekt) —
  [`docs/goldstandard/ergebnis_llm.md`](docs/goldstandard/ergebnis_llm.md). Die Modelle
  lesen also deutlich fehlerhafter als der Datensatz selbst; sie taugen als Hinweisgeber,
  nicht als Korrekturinstanz.
- Prüfliste `daten/pruefung_llm.csv`: **3.326** Zeilen — **55** mit `einig=beide` (beide
  Modelle lesen dasselbe, aber anders als der Datensatz), **3.199** mit `einig=eines`,
  **72** mit `einig=unlesbar` (ein Modell hat die Seite nicht gelesen). Modellwerte über
  120 Zeichen sind Fließtext der Vorlage und werden verworfen (nur Länge vermerkt).
  Stand nach Parser-Runde 2: vorher 4.317 Zeilen mit 712 × `einig=beide`. Der Rückgang
  hat zwei Ursachen — die Parser-Regeln R1–R6 beheben die systematischen Muster, und
  Regel R7 vergleicht beim **jeweils letzten Eintrag einer Buchseite** nur noch den Kopf,
  weil dessen Namenskette auf der Folgeseite weiterlaufen kann und die Modelle sie dort
  nicht sehen. Ausgelassene Ketten: **340** (`mistral`) bzw. **334** (`qwen`),
  in [`docs/llm_lesung.md`](docs/llm_lesung.md) als `seitenende_ausgelassen` beziffert.
- Daraus menschlich geprüft und angewandt: **370** Einträge mit `status=geprueft` —
  200 aus der Sichtung aller 288 `einig=beide`-Zeilen am 2026-09-13 (jede Zeile am
  Scan-Ausschnitt geprüft; 245 Zeilen als Korrektur, 7 Einträge als Bestätigung des
  Parser-Werts), 1 aus der Goldstandard-Stichprobe, dazu 5 vom Parser ausgelassene und
  per Overlay nachgetragene Einträge sowie 2 Einträge einer aufgelösten
  Schlüsselnummern-Dublette (OCR-Fehler), 2 Nachzügler aus der Sichtung, und **52** Einträge
  aus der Sichtung der `unsicher`-Einträge am 2026-09-14 (vollständige Prüfliste
  `daten/pruefung_unsicher.csv`, alle Felder je Eintrag am Scan-Ausschnitt geprüft, 84 Zellen
  korrigiert) sowie **108** in derselben Sichtung als korrekt bestätigte Einträge
  (`feld=eintrag`). Das Overlay `daten/korrekturen.csv` hat **523** Zeilen. Nach Sichtung und Overlay-Erweiterung verbleiben 55 `einig=beide`-Zeilen, davon
  25 bei bereits geprüften Einträgen (die Modelle lesen dort falsch) und 30 mit korrektem
  Parser-Wert; keine davon braucht eine Korrektur.

Die Modelle verändern den Status nicht; alle `geprueft`-Einträge gehen auf manuelle
Prüfung zurück. Übereinstimmungsquoten je Feldtyp und Modell:
[`docs/llm_lesung.md`](docs/llm_lesung.md).

### Goldstandard-Stichprobe (Entwicklungs-Stichprobe, Stand 2026-09-11)

50 zufällig gezogene Einträge (40 `automatisch`, 10 `unsicher`, Seed 1936) wurden
Zeichen für Zeichen gegen den Original-Scan geprüft — 478 Prüffelder, davon 10
nachgetragen (Feld im Scan gedruckt, im Datensatz nicht vorhanden). Ergebnis je Schicht:

| Schicht | Einträge | davon mit Fehler | Prüffelder | Fehlerquote |
|---|--:|--:|--:|--:|
| `automatisch` | 40 | 1 | 388 | **0,3 %** |
| `unsicher` | 10 | 7 | 90 | **17,8 %** |

Die Selbstmarkierung des Parsers trifft: 7 der 8 fehlerhaften Einträge waren bereits als
`unsicher` gekennzeichnet. Alle 17 Einzelfehler gehen auf **systematische** Parser- und
OCR-Muster zurück (Punkt nach „St." oder „II." beendet die Namenskette, numerisches Datum
„29.08.1927", Seitenumbruch im Eintragskopf, „Str.-Kl.;", getrenntes „Stadt-teile",
Abschnittsbuchstabe im Lemma). Sie werden im Parser behoben; da die Fehler am selben
Sample gefunden und behoben werden, ist diese Ziehung als **Entwicklungs-Stichprobe**
zu lesen, nicht als unabhängige Fehlerquote des Endstands. Vollständige Fehlerliste mit
Korrekturen: [`docs/goldstandard/ergebnis.md`](docs/goldstandard/ergebnis.md);
Prüfverfahren: [`docs/goldstandard/ANLEITUNG.md`](docs/goldstandard/ANLEITUNG.md). Die
drei Befunde, die die Parser-Reparatur nicht auflösen konnte (Eintrag 02949
Spervogelweg: Namensgruppe und ein ganz fehlendes Namensstadium), stehen seit dem
2026-09-13 als Korrekturzeilen in `daten/korrekturen.csv` (`quelle=goldstandard`); der
Eintrag trägt dadurch `status=geprueft`. Die 21
Regeln der Reparatur sind in
[`docs/specs/2026-09-11-parser-reparatur-design.md`](docs/specs/2026-09-11-parser-reparatur-design.md)
beschrieben, der Nachweis jeder Änderung in
[`docs/regression/2026-09-parser-reparatur.md`](docs/regression/2026-09-parser-reparatur.md).
Dass der Endstand mehr unsichere Einträge zählt als der Prototyp der Spec (256 nach Parser-Runde 2 statt 202; nach den manuellen Sichtungen 4),
ist gewollt und keine Regression: leere Kopffelder, Toleranz-Hinweise und unvollständig
gelesene Namensketten sind seither eigene Prüfgründe — der Prototyp las diese Fälle still.

### Erhebungsstand des Adressbuchs Essen 1936

Der Namensstand, den das Adressbuch tatsächlich abbildet, wurde nicht angenommen,
sondern an den 368 tagesgenau datierten Namensstadien-Übergängen im Zeitraum 1935–1937
gemessen, von denen sich 247 anhand des Adressbuchtexts eindeutig einer Namensform
zuordnen lassen (219 „alt", 28 „neu" — die übrigen 121 bleiben unentschieden, weil im
Adressbuch entweder beide oder keine der beiden Namensformen auftauchen): Ab Namensänderungen ab Februar
1936 reflektiert das Adressbuch keine einzige mehr. Das grenzt den tatsächlichen
Erhebungsschluss auf etwa **Ende 1935 bis Januar
1936** ein. Als Arbeitswert für die Konkordanz dient der Stichtag **1936-06-30** — er
liegt komfortabel im gesamten Zeitfenster (Februar 1936 bis Januar 1937), in dem keine
weitere Umbenennung mehr auf den Datensatz einwirkt, eine engere Festlegung wäre durch
die Daten nicht gedeckt. Details: [`docs/erhebungsstand.md`](docs/erhebungsstand.md).

## Externe Eingaben

Stufe 3+4 (`strassen/veroeffentlichen.py`) brauchen zwei Referenzquellen des
Essener Kartenprojekts (Schwesterprojekt, **nicht Teil dieses Repos**):

- `data/essen1936.csv` — der Adressbuch-Datensatz Essen 1936, liefert die
  Straßennamen für die Erhebungsstand-Messung (`docs/erhebungsstand.md`).
- `shared/strassen_aktuell.csv` — das amtliche Straßenverzeichnis, liefert den
  Abgleich in der dritten Selbstprüfung (`docs/qualitaet.md`, Abschnitt 3).

Beide Pfade sind Modulkonstanten in `strassen/veroeffentlichen.py`
(`ADRESSBUCH_PFAD`, `AMTLICHES_VERZEICHNIS_PFAD`), per `--adressbuch` bzw.
`--amtliches-verzeichnis` überschreibbar. Ohne diese beiden Dateien lassen sich
nur Stufe 1+2 (`strassen/erschliessen.py`) ausführen; `daten/strassen.csv` und
`daten/namen.csv` sind davon unabhängig.

## Bekannte Grenzen

Ehrlichkeit über die Grenzen dieses Datensatzes ist Teil seines Qualitätsanspruchs —
nichts hier ist verschwiegen, um sauberer zu wirken:

- **4 unsichere Einträge** (`status=unsicher` in `strassen.csv`): die beiden
  Schlüsselnummern-Dubletten der Vorlage (02402 Peenestraße/Porscheplatz, 03448
  Wangeroogeweg/Wieselweg). Alle anderen Einträge sind entweder vom Parser ohne Prüfgrund
  gelesen (`automatisch`) oder gegen den Scan geprüft (`geprueft`). Die Dubletten gehen
  bewusst nicht in die Konkordanz ein.
- **34 Konkordanz-Prüffälle** (`daten/pruefung_konkordanz.csv`, nicht Teil des
  Publikationsumfangs, s. u.): Straßen, deren letztes Namensstadium vom aktuellen Lemma
  abweicht (unvollständige oder korrupte Namenskette in der Quelle). Sie erscheinen
  **nicht** in `konkordanz_1936.csv`, sondern werden gekennzeichnet statt geraten.
- **Ketten-Blindspot der Alphabetprüfung:** Die Prüfung vergleicht nur direkte
  Nachbarn in der Sortierung. Zwei aufeinanderfolgende, gleichsinnig falsch sortierte
  Lemmata blieben dadurch unentdeckt.
- **„(tlw.)"-Semantik:** Klammerzusätze wie „(tlw.)" (teilweise) markieren
  Teil-Umbenennungen — nur ein Abschnitt der Straße trug 1936 diesen Namen. Diese
  Information bleibt im Feld `zusatz` erhalten, wird aber nicht weiter strukturiert
  ausgewertet (kein separates Feld für „welcher Teil"). Die Erkennung von
  Teil-Indikatoren toleriert bekannte OCR-Varianten von „teilweise"
  (`tlw.`, `tiw.`, `t!w.`, `{tlw.)`, `(tlw.}` …) und ergänzt abgeschnittene Formen
  (`(Verl` → `(Verl.)`) — jede *Ergänzung* wird gekennzeichnet und der Eintrag auf
  `unsicher` gestuft. Sie deckt aber nicht jede denkbare Schreibvariante ab; im
  Zweifel wird ein Zusatz konservativ als rein administrativ behandelt und die Zeile
  bei unveränderten Namen verworfen, statt Information zu erfinden.
- **Römische Ordnungspunkte im Lemma:** Doppelt vergebene Straßennamen trägt die Quelle
  als `I. <Name>` / `II. <Name>`. Der Parser hält den Punkt nach `I`, `II`, `III`, `IV`
  und `Ill` fest und gewinnt so **11 der 24** erwarteten Lemmata zurück; die OCR schreibt `II.` aber
  häufig als `Il.` oder `ll.` und `I.` als `l.` oder `1.` — diese Lesarten bleiben
  unbehandelt und die betroffenen Lemmata daher als Dublette in
  `daten/pruefung_validierung.csv` sichtbar (gekennzeichnet statt geraten). Als
  Nebenwirkung ziehen zwei Lemmata einen vorangehenden Satz mit, der auf „I." bzw. „II."
  endet (schl_nr 00601, 02318); beide sind `unsicher` und im Differenzbericht
  [`docs/regression/2026-09-13-parser-runde-2.md`](docs/regression/2026-09-13-parser-runde-2.md)
  einzeln belegt.
- **3 echte Schlüsselnummer-Dubletten**: Bei drei Schlüsselnummern liegen zwei
  Einträge vor. Ursache nicht abschließend geklärt (OCR-Doppellesung vs. tatsächliche
  Dublette in der Quelle); beide Vorkommen sind im Datensatz erhalten.
- **15 von 223 `verweis_auf`-Werten lösen nicht auf ein Lemma in `strassen.csv`
  auf** — überwiegend OCR-Bindestrich-Artefakte im Zielnamen (Leerzeichen um
  den Bindestrich, z. B. „Elsa- Brändström-Straße" statt korrekt
  „Elsa-Brändström-Straße") oder Doppelziele („Porscheplatz und Am
  Porscheplatz"), die das einfache Lemma-Muster nicht auflöst. Der Verweis
  selbst bleibt roh erhalten, statt ihn zu erraten oder stillschweigend zu
  bereinigen.
- **Goldstandard-Stichprobe noch ausstehend:** Eine Zeichen-für-Zeichen-Prüfung von 50
  zufällig gezogenen Einträgen gegen den Original-Scan zur Ermittlung einer bezifferten
  Feldfehlerquote ist geplant, aber noch nicht durchgeführt (siehe
  [`docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md`](docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md),
  Abschnitt 3, Stufe 3). Bis dahin stützt sich die Qualitätsaussage auf die drei
  Selbstprüfungen oben, nicht auf eine unabhängige Fehlerquote.

## Publikationsumfang

Zum veröffentlichten (Zenodo-)Stand gehören:

- `daten/strassen.csv`, `daten/namen.csv`, `daten/konkordanz_1936.csv`,
  `daten/pruefung_validierung.csv` (nur Lemma/Schlüsselnummer/Grund, keine Zitate)
- `daten/korrekturen.csv` und `daten/pruefung_llm.csv` — nur Kopffeld- bzw.
  Namensinhalte (Feldnamen, Werte, Belegtext ≤ 200 Zeichen, Datum, Quelle), keine
  Bild- oder Modell-Rohdaten
- der Code (`strassen/`, inkl. `strassen/ocr_lauf.py`)
- diese Dokumentation (README, LICENSE, CITATION.cff, `datapackage.json`, `docs/`)

**Nicht** Teil des Publikationsumfangs:

- `ocr/seiten/` — die OCR-Rohtexte der Buchseiten enthalten den urheberrechtlich
  geschützten Volltext Dickhoffs und sind per `.gitignore` von der Veröffentlichung
  ausgeschlossen.
- `daten/pruefung.csv` und `daten/pruefung_konkordanz.csv` — beides
  **Kuratierungs-Arbeitsdateien** mit kurzen Quellzitaten (Belegfunktion, jeweils
  ≤ 200 Zeichen roher OCR-Ausschnitt) zur manuellen Klärung auffälliger Fälle. Sie
  dienen dem internen Workflow (Round-Trip: sichten → korrigieren → Lauf wiederholen),
  nicht der Weitergabe.
- `llm/` — die für die LLM-Lesung erzeugten Seitenbilder und die rohen
  Modellantworten; per `.gitignore` von der Veröffentlichung ausgeschlossen.
- `.env` — lokale Zugangsdaten (`LLM_BASE_URL`, `LLM_API_KEY`) für den
  Inferenzendpunkt; per `.gitignore` ausgeschlossen.

## Lizenz und Zitierhinweis

Der Code und die Datenstruktur/-zusammenstellung stehen unter **CC BY 4.0** (Volltext:
[`LICENSE`](LICENSE), mit vorangestellter Klarstellung zum Geltungsbereich). Die
zugrunde liegenden Sachangaben (Straßennamen, Daten, Schlüsselnummern) sind als Fakten
nicht eigenständig schutzfähig, bleiben aber Dickhoff 2015 zuzuschreiben.

**Diesen Datensatz zitieren:** siehe [`CITATION.cff`](CITATION.cff) (maschinenlesbar,
GitHub/Zenodo-kompatibel).

**Dickhoff als Primärquelle zitieren:**

> Dickhoff, Erwin: *Essener Straßen.* Klartext-Verlag, Essen 2015.
> ISBN 978-3-8375-1231-1.

Für aus diesem Datensatz **abgeleitete Arbeiten** (z. B. Auswertungen der
Namensgeschichte, Kartendarstellungen einzelner Umbenennungen) ist zusätzlich zum
Datensatz **Dickhoff 2015 als Sachquelle zu zitieren** — die im Datensatz erfassten
Fakten stammen aus seiner Forschung, nicht aus dieser Erschließung.
