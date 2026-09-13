# Parser-Runde 2 nach der LLM-Lesung — Design

Stand: 2026-09-13. Baut auf der Parser-Reparatur (Spec 2026-09-11) und der LLM-Lesung
(Spec 2026-09-12) auf. Nur Standardbibliothek, Bezeichner und Doku deutsch.

## 1. Anlass

Die unabhängige LLM-Lesung liefert in `daten/pruefung_llm.csv` 712 Zeilen, in denen beide
Modelle übereinstimmend vom Parser abweichen (`einig=beide`), bei 583 Einträgen, davon 502
Zeilen bei `status=automatisch`. Die Sichtung vom 2026-09-13 ordnet sie so ein:

| Klasse | Zeilen | Befund |
|---|--:|---|
| Trennstrich am Zeilenende vor Großbuchstabe bleibt als „- " stehen | 184 | Parser-Regel fehlt (`aufbereitung._TRENNUNG` löst nur vor Kleinbuchstaben auf); 562 Stellen im Korpus |
| Klammerzusatz OCR-verunreinigt oder abgeschnitten (`(tiw.)`, `(Verl)`, `(Umb))`, `{tlw.)`, `(tiw`) | 147 | Parser übernimmt OCR wörtlich |
| Großumlaut am Wortanfang fehlt (`Ortlichkeit`, `Abtissin`) | 38 | OCR liest Ö/Ä/Ü als O/A/U |
| Römischer Präfix `I.`/`II.`/`III.` im Lemma verloren | 24 | `segmentierung._LEMMA` wertet den Punkt nach der Ziffer als Satzende |
| Rauschzeichen vor dem Wert (`„ `, `) `, `” `, `nn `), „`; _`" am Feldende | 13 | Kopffeld-Ränder |
| Eintrag fehlt beim Parser | 15 | 9 durch OCR-Varianten des Ankers/Lemma-Trenners, 6 Layout-Zerfall |
| Stadium fehlt bei beiden Modellen, Eintrag `automatisch` | 12 | **kein Parser-Fehler**: Eintrag am Seitenende, Kette läuft auf der Folgeseite weiter, die Modelle sehen nur eine Seite |
| Einzelfälle (ein Zeichen verlesen, Feld leer, Datum) | ~130 | Overlay nach Sichtung am Scan |
| Verunreinigte Lemmata/Namensgruppen, meist schon `unsicher` | 111 | bekannte Segmentierungsschwäche, Overlay |

Ziel dieser Runde: die Musterklassen im Parser beheben, die Prüflisten-Phantome beseitigen,
und dem Menschen die Sichtung der Einzelfälle erleichtern. Der Goldstandard bleibt
Entwicklungs-Stichprobe.

## 2. Regeln

Alle Regeln folgen precision-first: eine Regel greift nur bei eindeutiger Form; Toleranz-
Erkennungen übernehmen den Wert **und** kennzeichnen (`status=unsicher` über einen Hinweis),
wie in Spec 2026-09-11 eingeführt.

### R1 Trennstrich vor Großbuchstabe (`aufbereitung`)

`-\n` gefolgt von optionalem Leerraum und Großbuchstabe → `-` ohne Leerzeichen
(„Adolf-\nRath-Straße" → „Adolf-Rath-Straße", „Überruhr-\nHinsel" → „Überruhr-Hinsel").
Begründung: Ein Bindestrich mit folgendem Leerzeichen existiert im Deutschen nicht; am
Zeilenende vor Großbuchstabe ist der Strich stets Namensbestandteil. Kein Hinweis.
Nebenwirkung erwünscht: bisherige „- "-Formen in `stadtteile`, `lemma`, `name` verschwinden
(355 Stellen im Datensatz). Die bestehende Regel `_TRENNUNG` (vor Kleinbuchstabe → „") bleibt.

### R2 Klammerzusätze (`namen`)

Dickhoff verwendet am Namensende genau drei Vermerke: `(tlw.)`, `(Verl.)`, `(Umb.)`, auch
kombiniert `(tlw. Umb.)`. Normalisierung eines Klammerzusatzes am Ende eines Stadiennamens:

- Klammertyp: `{`, `[` → `(`; `}`, `]` → `)`; doppelte schließende Klammer `))` → `)`.
- Inhalt wortweise gegen die Tabelle: `tlw|tiw|tIw|t!w|tw|tl|tlw` → `tlw.`; `Verl|verl|Ver1` → `Verl.`;
  `Umb|Umb.` → `Umb.`; fehlender Punkt wird gesetzt. Unbekannte Wörter bleiben unverändert
  (Ortsklammern wie `(Essen)` sind legitim).
- **Abgeschnittener Zusatz** (öffnende Klammer ohne schließende am Kettenende, z. B.
  `Thomaestraße (tiw`): Wort normalisieren, `)` ergänzen, Hinweis `Klammerzusatz ergänzt`
  → `unsicher`, weil ein zweites Wort (`Umb.`) fehlen kann.
- Korrekturen der Schreibung (`tiw` → `tlw`) gelten als eindeutig und erzeugen keinen Hinweis;
  `stichtag._ZUSATZ_MUSTER`/`_TEIL_ZUSATZ_MUSTER` bleiben unverändert (sie tolerieren die
  Varianten weiterhin, treffen aber künftig nur noch saubere Formen).

### R3 Großumlaut am Wortanfang (`aufbereitung`)

Wörterbuch exakter Wortformen aus den Funden: `Ortlichkeit` → `Örtlichkeit`, `Abtissin` →
`Äbtissin`, `Agyptologe` → `Ägyptologe`, `Agirstraße` → `Ägirstraße`, `Uckendorfer` →
`Ückendorfer`, `Ostviertel` bleibt (ist korrekt; das OCR-`Östviertel` wird umgekehrt zu
`Ostviertel`). Nur ganze Wörter (Wortgrenzen), nur diese Liste; kein Hinweis. Die Liste
steht als Konstante mit Fundstellen-Kommentar in `aufbereitung`.

### R4 Römischer Präfix im Lemma (`segmentierung`)

`_LEMMA` behandelt den Punkt nach `I`, `II`, `III`, `IV` nicht als Satzende (Lookbehinds wie
`datum._KEIN_ABKUERZUNGSPUNKT`). Damit bleibt „I. Buschlandweg" vollständig. Erwartete Wirkung:
die 24 Lemmata `I./II./III. <Name>` (Buschlandweg, Dellbrügge, Fließstraße, Hagen, Ruschenfeld,
Schichtstraße, Schnieringstraße, Schockenhecke, Stiege, Terwestenweg, Weberstraße) erhalten ihren
Präfix; die entsprechenden Lemma-Dubletten in `pruefung_validierung.csv` verschwinden.

### R5 Kopffeld-Ränder (`kopf`)

- Führende Nicht-Buchstaben vor `lemma` und `strassenklasse` (`„ `, `) `, `” `, `nn `) werden
  entfernt, wenn der Rest mit einem Großbuchstaben beginnt. Für `lemma` gilt: nur Zeichen aus
  `„”")]}|` und Kleinbuchstabenfolgen ≤ 3 Zeichen mit Leerzeichen, damit „nn Hattenheimer" und
  „) Am Richtenberg" bereinigt werden, „Am Handelshof" aber unangetastet bleibt. Hinweis
  `Randzeichen entfernt` → `unsicher` (der Rest kann weiter verunreinigt sein).
- `; _` bzw. `; _`-artige Reste (`;` + Unterstriche/Leerraum) am Ende von `stadtteile` und
  `strassenklasse` werden entfernt, kein Hinweis.

### R6 Anker- und Lemma-Trenner-Toleranz (`segmentierung`)

- `ANKER` erkennt zusätzlich `Sch}`, `Sch)` (`Sch[a-zA-Z!|}\)]{0,3}`), `N.` statt `Nr.`
  (`N(?:r)?\.?`), führenden Bindestrich (`-Schl.-Nr.`) und `;` statt `:` nach `Nr`.
- `_LEMMA` akzeptiert als Trenner `:`, `;`, `:;` (`\s*[:;]+\s*$`).
- Erwartete Wirkung: 9 der 15 fehlenden Einträge (00465 Brunhildenstraße, 03297 Waldblick,
  00710 Am Schloss Schellenberg, 01067 Graitengraben, 02599 Riegelweg, 02821 Schraeplerstraße,
  02086 Marreweg, 02070 Malmedystraße, 02834 Schulte-Hinsel-Straße) werden Einträge; Anker-
  Varianten erzeugen den Hinweis `Anker OCR-korrigiert` → `unsicher`. Die übrigen sechs
  (Layout-Zerfall 01603, 02655; fehlender Anker 01655; falsch gelesene Nummern 001321, 02566,
  02906) bleiben in `pruefung.csv`.

### R7 Prüfliste: letzter Eintrag je Seite (`llm_vergleich`)

Der letzte Parser-Eintrag jeder Buchseite (höchste Position im Seitentext) kann auf der
Folgeseite weiterlaufen. Für ihn wird nur der Kopf verglichen; Stadienabweichungen entfallen.
Betroffene Zeilen tragen im Feld `einig` weiterhin ihre Klasse, zusätzlich erhält die
Prüfliste keine neue Spalte — stattdessen zählt `kennzahlen[kurz]["seitenende_ausgelassen"]`
die ausgelassenen Einträge, und `docs/llm_lesung.md` nennt die Zahl. Bestimmung „letzter
Eintrag je Seite": über `buchseite` in `strassen.csv` und die Reihenfolge der Zeilen (der
Parser schreibt in Lesereihenfolge).

## 3. Werkzeuge

### W1 Seitenausschnitte je Prüfzeile (`strassen/pruefbilder.py`)

`python3 -m strassen.pruefbilder [--einig beide] [--quelle DIR]` rendert für jede Prüfzeile
der gewählten Klasse den Halbseiten-Ausschnitt der Buchseite nach
`llm/pruefbilder/schlnr_<schl_nr>_s<buchseite>.png` (gitignored; Wiederverwendung von
`goldstandard.rendere_ausschnitt`, 150 dpi reichen zum Lesen, eine Datei je Eintrag, nicht je
Zeile). Zusätzlich schreibt es `llm/pruefbilder/index.md` mit einer Tabelle
`schl_nr | buchseite | Felder | Bild`, damit die Sichtung Eintrag für Eintrag laufen kann.

### W2 Vorgehensseite (`docs/vorgehen.md`)

Eine chronologische Seite, je Schritt drei bis fünf Sätze und der Verweis auf Spec/Bericht:
Datensatz-Design (2026-08-20), Goldstandard-Stichprobe und Entscheidung Entwicklungs-
Stichprobe (2026-09-11), Parser-Reparatur (2026-09-11/12), LLM-Lesung mit Option A und
Korrektur-Overlay (2026-09-12/13), Parser-Runde 2 (2026-09-13). README verlinkt sie im
Abschnitt „Methode".

## 4. Sicherungen und Regeneration

1. TDD je Regel mit realen OCR-Ausschnitten (Kopf/Kette, ohne Erläuterungstext) aus den
   Fundstellen der Sichtung.
2. `python3 -m strassen.differenz <alt> daten --ausgabe docs/regression/2026-09-13-parser-runde-2.md`
   gegen den Stand 54c5e2a; der Bericht wird annotiert (je Kategorie ein Satz, Auffälliges je
   Zeile mit `- Prüfung:`). Sollwerte: keine verlorenen Stadien in `automatisch`-Einträgen
   außer durch R2/R1 umbenannte (Signatur-Änderung), Straßen +9, Lemma-Dubletten −22.
3. `tests/test_goldstandard_regression.py` bleibt grün.
4. `daten/korrekturen.csv` wird gegen die neue Parser-Ausgabe angewandt; ändert R1–R6 einen
   `wert_alt`, bricht der Lauf ab und die Zeile wird von Hand nachgezogen (erwartet: keine, der
   Spervogelweg ist nicht betroffen).
5. Prüfliste neu erzeugen (`llm_vergleich pruefliste`, Antworten aus dem Cache), Kennzahlen,
   README-Zahlen, `docs/llm_lesung.md`; Sollwert: `einig=beide` sinkt von 712 auf unter 250.

## 5. Nicht-Ziele

- Keine Wörterbuch-Korrektur einzelner Namen (`Moitkestraße`, `Akazienaltee`): das ist
  Sichtungsarbeit für das Overlay.
- Keine Übernahme von Modellwerten in den Datensatz (Option A bleibt).
- Keine neue Lesung durch die Modelle; die Prüfliste wird aus dem Cache neu gebaut.
- Keine Behebung des Layout-Zerfalls (Lemma nach dem Anker, S. 227/280).
