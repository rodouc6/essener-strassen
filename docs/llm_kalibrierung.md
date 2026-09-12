# Kalibrierung der LLM-Lesung an Entwicklungsseiten

Der Prompt der unabhängigen LLM-Lesung (`strassen/llm_prompt.md`) wurde an acht
**Entwicklungsseiten** entwickelt, die **keinen** Goldstandard-Eintrag enthalten — die
Goldstandard-Messung (Task 12/13) bleibt dadurch eine Messung an ungesehenem Material.

- Entwicklungsseiten: **30, 60, 100, 150** (Band 1) und **220, 260, 300, 340** (Band 2),
  zusammen 84 Parser-Einträge.
- Modelle: `inferenz-qwen3-8-27b` (im Folgenden *qwen*) und
  `inferenz-mistral-small-4-119b` (*mistral*), je Seite nur das Seitenbild, `temperature 0`.
- Endstand des Prompts: **`638b38acd4b2`** (`prompt_hash`; alle 16 ausgewerteten Antworten
  stammen aus diesem Stand).
- Vergleichsbasis: `daten/strassen.csv` / `daten/namen.csv`, ausgewertet mit
  `python3 -m strassen.llm_vergleich pruefliste`. Die Kalibrierungs-Prüfliste ist
  bewusst **nicht** versioniert; sie entsteht in Task 12 neu.

Die Modelle sind zweite Leser. Kalibriert wurde ausschließlich die **Lesbarkeit und
formale Robustheit** ihrer Antworten (Feldgrenzen, Vollständigkeit der Kette, JSON-Form) —
nie die inhaltliche Annäherung an Parser-Werte.

## Runde 1 — Feldgrenzen, Verweise, Kettenumfang

Beobachtungen an den acht Seiten (145 Prüfzeilen; 30 × `einig=beide`, 113 × `eines`,
2 × `unlesbar`):

| Beobachtung | Umfang | Seiten |
|---|---|---|
| `verweis_auf` blieb leer, wenn der `Siehe`-Verweis erst **nach** dem Erläuterungstext steht | 6 von 6 Fällen, **beide** Modelle | 30, 100, 150 (2×), 220, 260 |
| mistral ließ datumslose `urspr.:`-Stadien aus; dadurch rutschte die ganze Kette um eins | 8 Einträge | 150, 220, 260, 300 |
| mistral transkribierte Erläuterungsprosa als Stadium (Lebensdaten, Quellenangaben) | 9 Einträge | 100 (8×), 220 |
| `namensgruppe` an der falschen Stelle abgeschnitten, wenn sie selbst ein Komma enthält (`Lagebezeichnung, Platz`) | 4 Einträge, beide Modelle | 30, 150, 220, 300 |
| mistral zählte `schl_nr` fortlaufend weiter, statt sie im Kopf abzulesen — nach einem übersehenen Eintrag waren alle folgenden Nummern um eins verschoben | 6 Einträge | 100 |

Änderungen im Prompt:

1. Abschnitt über die **Feldgrenzen** ergänzt: `Str.-Gr.:` kann selbst eine Komma-Liste
   sein und reicht bis zum Beginn der Namenskette (erstes Datum oder `urspr.`).
2. `verweis_auf` neu definiert: der Name aus `Siehe <Name>` **an beliebiger Stelle** des
   Eintrags, auch nach der Erläuterung; nicht bei `Siehe auch …` / `Vgl. …`.
3. Beim Feld `stadien` ergänzt: das `urspr.:`-Stadium steht direkt hinter der
   Namensgruppe, hat oft kein Datum und darf nie ausgelassen werden; jeder `name` ist ein
   kurzer Straßenname, nie ein Satz; Lebensdaten und Jahreszahlen im Erläuterungstext sind
   keine Stadien.
4. Regel 5 korrigiert: die Schlüsselnummern sind **nicht** fortlaufend (auf einer Seite
   stehen z. B. 00046, 00252, 00054 nebeneinander) — jede `schl_nr` wird im Kopf ihres
   eigenen Eintrags abgelesen. (Die alte Formulierung „laufen auf der Seite fortlaufend"
   war schlicht falsch und hat den Nummernversatz begünstigt.)

**Wirkung:** 145 → 96 Prüfzeilen. `verweis_auf` 93,7 % → 98,7 % (qwen) bzw. 94,7 % → 98,7 %
(mistral); qwen `stadium_datum` 98,5 % → 100 %, `stadium_urspruenglich` 99,2 % → 100 %;
beim Parser vorhandene, im Modell fehlende Einträge (mistral) 5 → 1.

## Runde 2 — leere Antwort des Inferenzservers (Code)

Bei Seite 300 lieferte der Server für qwen `"content": null`. `extrahiere_json` bekam
dadurch `None` und der ganze Lauf brach mit einem `TypeError` ab (die schon gelesenen
Seiten blieben erhalten, die folgenden wurden nicht mehr gelesen).

Änderung (TDD, `tests/test_llm_leser.py`): `sende()` gibt für ein nicht-textliches
`content` einen leeren Text zurück, `extrahiere_json()` meldet Nicht-Text als `JsonFehler`.
Eine leere Antwort ist damit das, was sie ist — eine **leere**, keine kaputte Antwort: sie
läuft in die reguläre JSON-Wiederholung und die Seite wird notfalls als `unlesbar`
verbucht, ohne den Lauf zu beenden.

**Wirkung:** im Lauf der Runde 3 trat derselbe Fall erneut auf (qwen, Seite 300, dreimal
leer → `unlesbar`); der Lauf lief durch, ein Einzelaufruf `--seiten 300 --neu` lieferte die
Seite anschließend vollständig. Der Fehler ist offenbar sporadisch (Serverseite), nicht
seitenspezifisch.

## Runde 3 — Marker im falschen Feld, Trennstriche, Modernisierung

Beobachtungen im Stand nach Runde 1:

| Beobachtung | Umfang | Seiten |
|---|---|---|
| mistral schrieb den Marker samt Namen ins Datumsfeld (`datum: "urspr.: Fischerstraße"`) | 4 Stadien | 150, 220 (2×), 260 |
| mistral gab ein am Zeilenende getrenntes Wort mit Weichtrennstrich U+00AD zurück (`Kriegs¬erinnerung`) | 1 Feld | 100 |
| qwen modernisierte die Schreibung (`Phoenixhütte` → `Phönixhütte`) | 1 Eintrag (2 Felder) | 260 |
| mistral gab weiterhin Erläuterungsprosa als Stadium aus | 8 Einträge | 100, 220 |

Änderungen:

5. Prompt, Regel 1: nicht modernisieren, mit Beispiel `Phoenixhütte`; am Zeilenende
   getrennte Wörter zusammensetzen, kein Wert endet mit einem Trennstrich, echte
   Bindestriche bleiben.
6. Prompt, Feld `stadien`: der Marker `urspr.` gehört **nie** ins Datums- oder Namensfeld,
   sondern allein in `urspruenglich`; die Kette endet beim ersten Satz, der keine
   `Datum: Name`-Angabe mehr ist; ein datumsloses Stadium gibt es nur mit `urspr.`.
7. Code (`llm_vergleich._text`, TDD): Weichtrennstriche U+00AD werden beim Normalisieren
   entfernt — Drucksatz, kein gelesenes Zeichen.
8. Code (`llm_vergleich.normalisiere_antwort`, TDD): ein Datumsfeld, das **nur** aus dem
   Marker `urspr.`/`ursprünglich` besteht, gilt als „kein Datum" statt als nicht
   normalisierbares Datum. Steht daneben noch Text (`urspr.: Fischerstraße`), bleibt es
   eine sichtbare Prüfzeile — precision-first: geraten wird nicht.

**Wirkung:** qwen verbessert sich weiter (`verweis_auf` 100 %, `namensgruppe` 96,2 %,
keine Modernisierungen mehr, 0 nicht normalisierbare Daten). Bei mistral verschwinden die
Prosa-Stadien weitgehend und die Marker-im-Datum-Fälle sinken von 4 auf 3; zugleich trat
auf Seite 100 erneut der Nummernversatz auf, der in Runde 2 dort ausgeblieben war. Diese
Seite ist für mistral instabil (11 statt 12 Einträge) — die Schwankung ist Modellstreuung,
keine Folge der Prompt-Änderung: qwen liest dieselbe Seite in jeder Runde vollständig.

## Endstand (Prompt `638b38acd4b2`)

105 Prüfzeilen über die acht Seiten: **25 `beide`**, **79 `eines`**, **1 `unlesbar`**.

| Kennzahl | qwen | mistral |
|---|--:|--:|
| Seiten gelesen / unlesbar | 8 / 0 | 8 / 0 |
| Einträge beim Modell | 84 | 82 |
| beim Parser vorhanden, im Modell fehlend | 0 | 2 |
| nur beim Modell | 1 | 1 |
| Daten nicht normalisierbar | 0 | 3 |

Übereinstimmung mit dem Parser (Status `automatisch`, 78–79 Kopffelder bzw. 131–135 Stadienfelder):

| Feldtyp | qwen | mistral |
|---|--:|--:|
| lemma | 89,9 % | 89,7 % |
| stadtteile | 88,6 % | 83,3 % |
| strassenklasse | 100,0 % | 100,0 % |
| namensgruppe | 96,2 % | 85,9 % |
| verweis_auf | 100,0 % | 94,9 % |
| stadium_datum | 100,0 % | 88,1 % |
| stadium_name | 84,7 % | 79,3 % |
| stadium_urspruenglich | 100,0 % | 95,6 % |

Die Quoten sind **keine** Fehlerquoten der Modelle: alle 25 `einig=beide`-Zeilen — die
Fälle, in denen beide Modelle unabhängig denselben, vom Parser abweichenden Wert lesen —
sind nach Prüfung am Seitenbild **Parser-Defekte**, keine Modellfehler. Sie sind damit
Kandidaten für `daten/korrekturen.csv` (hier nur notiert, nicht übernommen):

- OCR-Verstümmelungen in Namenszusätzen: `(tlw. Umb.)` als `(tiw`/`(tw`, `(Verl.)` als
  `(Verl)`, `(Umb.)` als `(Umb))`, `Im Bungert (tlw.)` als `Im Bungert ftiw.)`
  (Seiten 30, 220, 300).
- Fehlende Umlaute in der Namensgruppe: `Essener Geschichte und Ortlichkeit`
  (Seiten 30, 300).
- Über den Zeilenumbruch getrennte Werte mit stehengebliebenem Leerzeichen:
  `Altenessen- Süd`, `Borbeck- Mitte`, `Schwarze-Lenen- Straße`, `Walter- Sachsse-Weg`
  (Seiten 150, 220, 260, 300, 340).
- Verunreinigte Lemmata, in die Nachbartext geraten ist: `43 ff Bahnstraße` (S. 60),
  `BDudenstraße` (S. 100), `Phoenixhütte Pflanzstraße` (S. 260 — die Bildunterschrift der
  Abbildung über dem Eintrag), `Helmholtz- Heiligenhauser Straße` (S. 150).
- Ein als `|` gelesenes Namensstadium (`I. Hagenstraße`, S. 300) und ein Stadium, das nur
  aus OCR-Rauschen besteht (S. 220).

## Bekannte Modellschwächen (Endstand)

**Beide Modelle**

- Einzelne Buchstabenverwechslungen in Eigennamen bleiben (qwen: `Baedeckerstraße`,
  `Heimatkank`, `Lentorstraße`, `Bredenei`; mistral: `Bergebausen`, `Friesenbruch`,
  `Wasserschneppe`, `Altessen-Süd`). Sie treten **nicht** bei beiden gleichzeitig auf —
  darum ist die Zwei-Modell-Anlage sinnvoll: `einig=beide` ist das belastbare Signal,
  `einig=eines` verlangt den Blick ins Bild.
- Ein am Seitenende abgeschnittenes Wort (S. 260, `Malerviertel-`) kann kein Modell
  vervollständigen — der Eintrag läuft auf die Folgeseite weiter. Kein Modellfehler,
  sondern eine Grenze der seitenweisen Lesung.

**qwen** (der insgesamt stabilere Leser)

- Liest auf allen acht Seiten alle Einträge, Daten und `urspr.`-Marker vollständig
  (100 % bei `stadium_datum`, `stadium_urspruenglich`, `verweis_auf`, `strassenklasse`).
- Gelegentlich leere Antworten des Servers (`content: null`), s. Runde 2 — beim vollen
  Lauf einfach den Befehl wiederholen.

**mistral**

- Übersieht einzelne Einträge (hier 2 von 84) und zählt dann gelegentlich die `schl_nr`
  der Folgeeinträge weiter, statt sie abzulesen — der Versatz betrifft dann eine ganze
  Seitenhälfte. Auf dicht gesetzten Seiten (S. 100: 12 Einträge) tritt das reproduzierbar
  auf.
- Zieht vereinzelt noch Erläuterungstext in die Namenskette (Lebensdaten, Ortsangaben).
- Schreibt vereinzelt den Marker `urspr.` samt Namen ins Datumsfeld (3 Fälle); diese
  Zeilen sind in der Prüfliste als `(nicht normalisierbar)` gekennzeichnet.
- Verwechselt Kategorien der Namensgruppe (`Wirtin` → `Wirtshaus`, `Lehngut` → `Lehnsgut`).

Konsequenz für die Auswertung: die Prüfliste sortiert `einig=beide` nach oben. Diese
Zeilen sind fast durchweg Parser-Defekte und lohnen die manuelle Prüfung zuerst; bei
`einig=eines` ist in aller Regel qwen der verlässlichere der beiden Leser.
