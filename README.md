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
erzeugen — segmentiert die 388 OCR-Seiten in 3.343 Einträge und zerlegt jeden
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

## Data Dictionary

Zwei verknüpfte Tabellen statt einer flachen Konkordanz, weil ein Straßeneintrag
Eigenschaften der Straße *und* eine Folge von Namensstadien trägt (1:n) — das
maschinenlesbare Schema liegt zusätzlich in [`datapackage.json`](datapackage.json)
(Frictionless-Format).

### `daten/strassen.csv` (3.338 Zeilen)

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `schl_nr` | amtliche Schlüsselnummer, fünfstellig | Primärschlüssel, eindeutig (3 Dubletten dokumentiert, s. u.) |
| `lemma` | heutiger Straßenname (Stichwort des Eintrags) | Text |
| `stadtteile` | Stadtteil(e) | mehrere durch `; ` getrennt |
| `strassenklasse` | Straßenklasse | Gemeindestraße, Kreisstraße, Landstraße, Bundesstraße, Autobahn, Hauptstraße …; mehrere durch `; ` getrennt; bei `status=unsicher` z. T. OCR-verunreinigt |
| `namensgruppe` | Str.-Gr. der Quelle, wörtlich übernommen | Text (Flurname, Person, Lagebezeichnung, Stadt und Ort …) |
| `verweis_auf` | Ziel-Lemma bei „Siehe X" | Text oder leer (223 von 3.338 Zeilen gefüllt) |
| `buchseite` | Beleg: Seite in Dickhoff 2015 | ganzzahlig, 23–362 (Einträge nur im Lexikonteil; das Buch umfasst die Scan-Seiten 2–388, Titelei/Einleitung/Register enthalten keine Einträge) |
| `status` | Prüfstatus des Eintrags | `automatisch` \| `geprueft` \| `unsicher` |

### `daten/namen.csv` (5.286 Zeilen)

| Feld | Beschreibung | Wertebereich |
|---|---|---|
| `schl_nr` | Fremdschlüssel auf `strassen.csv` | siehe oben |
| `stadium` | laufende Nummer der Namensstufe | ganzzahlig, 1 = älteste |
| `gueltig_ab` | Datum, ab dem der Name in diesem Stadium galt | ISO-Datum, Jahr, oder leer bei `unbekannt` |
| `datum_praezision` | Genauigkeit der Datierung | `tag` \| `monat` \| `jahr` \| `vor` \| `nach` \| `unbekannt` |
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

### `daten/konkordanz_1936.csv` (425 Zeilen)

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
| `zusatz` | abgetrennter Klammerzusatz aus der Quelle | z. B. „(tlw.)", „(Verl.)"; leer wenn keiner vorlag (134 von 425 Zeilen gefüllt) |
| `eindeutig` | ob `(stadtteil, ehemalig)` auf genau eine `schl_nr` trifft | `ja` (386) \| `nein` (39, Kollisionen) |

Straßen mit `status=unsicher` gehen **nicht** in die Konkordanz ein, da ihr heutiger
Name selbst nicht belastbar ist. Einträge, deren Namenskette intern widersprüchlich ist
(letztes Stadium ≠ Lemma), werden nicht in die Konkordanz aufgenommen, sondern als
Prüffall geführt (s. [Bekannte Grenzen](#bekannte-grenzen)).

## Bezifferte Qualität

- **388** OCR-Buchseiten → **3.343** vom Parser segmentierte Einträge.
- `daten/strassen.csv`: **3.338** Zeilen, davon **241** mit `status=unsicher`
  (**3.097** `automatisch`).
- `daten/namen.csv`: **5.286** Namensstadien (Datierungsgenauigkeit: **4.579** `tag`,
  **314** `unbekannt`, **215** `jahr`, **178** `vor`).
- `daten/konkordanz_1936.csv`: **425** Zeilen (**386** `eindeutig=ja`, 39 `eindeutig=nein`;
  **134** mit Klammerzusatz).

### Drei unabhängige Selbstprüfungen

| Prüfung | Ergebnis |
|---|---|
| Schlüsselnummern (amtlich, 1–3771 erwartet) | 3.338 erfasst, 436 Lücken, **3 Dubletten** |
| alphabetische Ordnung der Lemmata | **73** aus der Sortierung fallende Lemmata (38 bereits als `unsicher` markiert, 35 neu auffällig) |
| Abgleich mit dem amtlichen Straßenverzeichnis (`strassen_aktuell.csv`) | **3.196** bestätigt, 142 nicht im Verzeichnis (erwartbar bei aufgehobenen Straßen) |

Details, Methodik und Interpretation: [`docs/qualitaet.md`](docs/qualitaet.md); die
konkreten Treffer (Lemma, Schlüsselnummer, Grund): `daten/pruefung_validierung.csv`.

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
Prüfverfahren: [`docs/goldstandard/ANLEITUNG.md`](docs/goldstandard/ANLEITUNG.md).

### Erhebungsstand des Adressbuchs Essen 1936

Der Namensstand, den das Adressbuch tatsächlich abbildet, wurde nicht angenommen,
sondern an den 363 tagesgenau datierten Umbenennungs-Übergängen im Zeitraum 1935–1937
gemessen: Ab Namensänderungen ab Februar 1936 reflektiert das Adressbuch keine einzige
mehr. Das grenzt den tatsächlichen Erhebungsschluss auf etwa **Ende 1935 bis Januar
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

- **241 unsichere Einträge** (`status=unsicher` in `strassen.csv`) sind vom Parser nicht
  sicher erschlossen; ihre Felder (insbesondere `strassenklasse`) können OCR-Rauschen
  enthalten. Sie gehen bewusst nicht in die Konkordanz ein.
- **69 Konkordanz-Prüffälle** (`daten/pruefung_konkordanz.csv`, nicht Teil des
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
  (`tlw.`, `tiw.`, `t!w.` …), deckt aber nicht jede denkbare Schreibvariante ab; im
  Zweifel wird ein Zusatz konservativ als rein administrativ behandelt und die Zeile
  bei unveränderten Namen verworfen, statt Information zu erfinden.
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
