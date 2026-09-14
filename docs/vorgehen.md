# Vorgehen — Chronik der Entscheidungen

Diese Seite fasst die Entwicklung des Datensatzes chronologisch zusammen: was an
welchem Datum entschieden wurde, mit welcher Begründung und mit Verweis auf die
Spezifikation bzw. den Bericht, der die Details trägt. Sie ersetzt keine der
verlinkten Dokumente, sondern gibt den roten Faden zwischen ihnen.

## 1. 2026-08-20 — Datensatz-Design

Als Quelle wurde Erwin Dickhoffs *Essener Straßen* (Klartext-Verlag, Essen 2015)
gewählt, weil die bislang genutzte Konkordanz selbst nur eine zweifach abgeleitete,
lückenhafte Form desselben Werks war. Die beiden Scan-Bände werden bei 300 dpi
gelesen, am Bundsteg in Buchseiten geteilt und mit Tesseract OCR erschlossen; ein
regelbasierter, deterministischer Parser (bewusst kein Sprachmodell) zerlegt jede
Buchseite in Straßen mit datierten Namensstadien. Rechtlich beschränkt sich der
veröffentlichte Datensatz auf nicht schutzfähige Fakten — Erläuterungstexte bleiben
lokal. Siehe Spec
[`docs/specs/2026-08-20-strassenverzeichnis-datensatz-design.md`](specs/2026-08-20-strassenverzeichnis-datensatz-design.md).

## 2. 2026-09-11 — Goldstandard-Stichprobe

Eine geschichtete Stichprobe von 50 Einträgen wurde Zeichen für Zeichen gegen den
Original-Scan geprüft und fand 17 Feldfehler, alle auf systematische Parser-/OCR-Muster
zurückführbar, keiner zufällig. Weil dieselbe Stichprobe zur Fehlersuche diente, mit der
sie anschließend behoben werden, ist sie als unabhängiges Qualitätsmaß des reparierten
Datensatzes verbraucht: Sie wird als **Entwicklungs-Stichprobe** ausgewiesen, eine neue
Ziehung fand bewusst nicht statt. Ergebnis in
[`docs/goldstandard/ergebnis.md`](goldstandard/ergebnis.md).

## 3. 2026-09-11/12 — Parser-Reparatur

Aus den 17 Goldstandard-Fehlern und einer Nachmessung auf dem Gesamtmaterial entstand
ein Katalog von 21 Regeln (u. a. eine eigene Datumslogik, Behandlung leerer Kopffelder
als Prüfgrund, Präzisionsstufe „jahrhundert"). Die Zahl der Straßen ohne erkannte
Namenskette sank von 84 auf 10 (Endstand; der Differenzbericht
`docs/regression/2026-09-parser-reparatur.md` dokumentiert den Zwischenstand 11); jeder
Verlust eines Stadiums, jede Umdatierung und
jede Statusrückstufung wurde einzeln am Drucktext geprüft und belegt. Differenzbericht:
[`docs/regression/2026-09-parser-reparatur.md`](regression/2026-09-parser-reparatur.md).

## 4. 2026-09-12/13 — LLM-Lesung

Zwei Bildmodelle lesen die Seiten unabhängig als zweite Leser, um Parser-Fehler
aufzuspüren, die der Parser selbst nicht erkennen kann. Entschieden wurde **Option A**:
Die Modelle ändern keinen Status — nur ein Mensch kann über das Korrektur-Overlay einen
Eintrag auf `status=geprueft` heben. Die Goldstandard-Messung, an ungesehenem Material
gemessen, ergab eine Fehlerquote von 6,1 % für `qwen` und 22,4 % für `mistral` — deutlich
höher als der Datensatz selbst; die Modelle taugen also als Hinweisgeber, nicht als
Korrekturinstanz. Aus dem Abgleich entstand die Prüfliste `daten/pruefung_llm.csv`, aus
der bestätigte Funde über das Korrektur-Overlay (`status=geprueft`) in den Datensatz
übernommen werden. Siehe
[`docs/llm_kalibrierung.md`](llm_kalibrierung.md), [`docs/llm_lesung.md`](llm_lesung.md)
und [`docs/goldstandard/ergebnis_llm.md`](goldstandard/ergebnis_llm.md).

## 5. 2026-09-13 — Parser-Runde 2

Die Sichtung der 712 Prüflisten-Zeilen mit `einig=beide` (beide Modelle stimmen
überein, aber weichen vom Parser ab) legte weitere systematische Muster offen, u. a.
unaufgelöste Trennstriche vor Großbuchstaben und OCR-verunreinigte Klammerzusätze.
Daraus entstanden sieben weitere Parser-Regeln sowie ein Werkzeug für Prüfbilder
(`strassen/pruefbilder.py`), das die verbleibenden Einzelfälle für die manuelle Sichtung
aufbereitet. Spec:
[`docs/specs/2026-09-13-parser-runde-2-design.md`](specs/2026-09-13-parser-runde-2-design.md).
Ergebnis der Regeneration: **+11 Straßeneinträge** (3.338 → 3.349) und **+16 Namensstadien**
(5.457 → 5.473), 379 korrigierte Namensschreibungen und 294 korrigierte Kopfwerte; die
Prüflisten-Zeilen mit `einig=beide` sinken von **712 auf 288** (Prüfliste insgesamt 4.317 →
3.585), weil R7 zusätzlich den letzten Eintrag jeder Buchseite nur im Kopf vergleicht
(`seitenende_ausgelassen`: 340 bei `mistral`, 334 bei `qwen`). Die Zahl gekennzeichneter
Einträge sinkt dabei (`unsicher` 271 → 256) und die Konkordanz geht von 426 auf 421 Paare
zurück: 15 der weggefallenen Paare waren keine Umbenennungen, sondern Trennstrich-Artefakte
(R1), 6 Einträge sind neu `unsicher` (Klammerzusatz ergänzt), 16 Paare kommen durch
normalisierte Klammerzusätze hinzu. Eine erste Regeneration hatte den Hinweis
`Anker OCR-korrigiert` zu weit gefasst und 102 inhaltlich unveränderte Einträge auf
`unsicher` gestuft; das wurde vor der Veröffentlichung korrigiert. Jede der verbliebenen
zwölf Rückstufungen ist einzeln geprüft im Differenzbericht
[`docs/regression/2026-09-13-parser-runde-2.md`](regression/2026-09-13-parser-runde-2.md).

## 6. 2026-09-13 — Manuelle Sichtung der Prüfliste

Alle 288 Prüflisten-Zeilen mit `einig=beide` (234 Einträge) wurden am Scan-Ausschnitt
(`strassen/pruefbilder.py`) gegen den Druck geprüft. Für Einträge, deren Text erst auf der
Folgeseite beginnt oder dort weiterläuft, wurde zusätzlich die Folgeseite gerendert.
Ergebnis: 245 Korrekturzeilen und 7 Bestätigungen des Parser-Werts, per
`llm_vergleich uebernehmen` in `daten/korrekturen.csv` übertragen (`quelle=llm-lauf`,
insgesamt 252 Zeilen), angewandt durch `erschliessen`. **201 Einträge** tragen jetzt
`status=geprueft`, `unsicher` sinkt von 256 auf **168**. Die Konkordanz wächst von 421 auf
**442** Paare, der Abgleich mit dem amtlichen Straßenverzeichnis von 3.237 auf **3.319**
Treffer (nicht im Verzeichnis: 112 → 30), die Alphabetprüfung meldet 37 statt 70 Auffällige.
Die Prüfliste wurde danach neu erzeugt: 3.355 Zeilen, `einig=beide` 288 → **57** (nach der
Overlay-Erweiterung in Abschnitt 7: 3.351 Zeilen, 53).

Bei der Übernahme wurden mechanisch vereinheitlicht: ISO-Datumsangaben in der
`korrektur`-Spalte in die Overlay-Form `TT.MM.JJJJ`, Nachträge ganzer Stadien in die Form
`DATUM | NAME`; Zeilen mit `korrektur = wert_parser` wurden als Bestätigung (`feld=eintrag`)
übernommen; ein `[sic!]` aus dem Wert in den Beleg verschoben. Drei Fälle brauchten Zeilen
direkt im Overlay: 00720 (Stadium 1 nachgetragen, das vorhandene rückt auf 2) und 01104
(Datum über Seitenumbruch geteilt, Name aus der Folgeseite ergänzt). Die Sichtungsfassung
der Prüfliste liegt unter `llm/pruefung_llm_sichtung_2026-09-13.csv` (nicht veröffentlicht).

Mit der Sichtung sind zwei Verunreinigungen im Druck selbst dokumentiert (Belege im
Overlay): 00621 De-Wolff-Straße („Str.-Gr." zweimal statt „Str.-Kl."), 02938/03014
„Familiename". Schlüsselnummern-Dubletten im Buch: 02402 (Peenestraße/Porscheplatz, nur
OCR-geprüft) und 03448 (Wangeroogeweg/Wieselweg, am Scan geprüft); 02568 ist dagegen ein
OCR-Fehler (Rebenranke ist gedruckt 02566) und wartet auf ein Overlay-Feld `schl_nr`.

## 7. 2026-09-13 — Overlay-Erweiterung statt Parser-Runde 3

Nach der Sichtung blieben 16 Fälle, die das Overlay nicht ausdrücken konnte: acht Einträge mit
falscher `buchseite` (Seitenendrest der Vorseite am Lemma), eine OCR-verlesene Schlüsselnummer
(Rebenranke 02568 → 02566, Dublette mit Reckhammerweg), fünf vom Parser ganz ausgelassene
Einträge (001321 Am Stadtgarten — im Druck sechsstellig —, 01603 Luxemburger Straße, 01655
Kappertsiepen, 02655 Rüttenscheider Platz, 02906 Spichernstraße) und zwei undatierte
`vorm.:`-Stadien (02512, 02513). Entscheidung (Nutzer, 2026-09-13): **kein Parser-Umbau**,
sondern eine kleine Overlay-Erweiterung — eine Parser-Änderung würde die `wert_alt`-Anker der
245 geprüften Korrekturen verschieben, und der verbleibende, von beiden Modellen nicht
angezeigte Fehleranteil rechtfertigt den Umbau nicht (Goldstandard: 0,3 % bei `automatisch`).
Das Overlay kennt seither die Felder `buchseite` und `schl_nr` (adressiert über das Lemma,
damit Dubletten eindeutig sind), die Neuanlage eines Eintrags über `feld=eintrag` mit
`wert_neu = Lemma` und den Nachtrag undatierter Stadien (`vorm.`); die Ausgabe wird nach dem
Overlay wieder in Buchreihenfolge gebracht. Alle 16 Fälle sind mit Beleg eingetragen
(Overlay 252 → 320 Zeilen). Ergebnis: Straßen 3.349 → **3.354**, `geprueft` 201 → **208**,
`unsicher` 168 → **166**, Stadien 5.480 → 5.495, Konkordanz 442 → **444**, amtlich bestätigt
3.319 → 3.324. Die Schlüsselnummern-Dubletten 02402 und 03448 stehen so im Buch und bleiben.
Nachtrag am selben Tag: zwei Hinweise aus der Sichtung waren nicht ins Overlay gelangt
(02681 Stadium „!" → „I. Siedlerweg"; 02874 stand bereits auf `geprueft` mit Stadium „Il" →
„III. Siedlerweg", Scan S. 304), dazu 03203 Velberter Sträßchen mit undatiertem
`urspr.`-Stadium (neues Schlüsselwort `urspr.` im Overlay). Stand danach: `geprueft` **210**,
`unsicher` **164**, Overlay 324 Zeilen. Von den 164 unsicheren Einträgen waren nur 5 Teil der
Sichtung; die übrigen 159 hat noch niemand gegen den Scan gesehen — sie sind der eigentliche
verbleibende Prüfbestand (Prüfgründe: auffälliges Lemma, Namenskette unvollständig, Datum
ohne Doppelpunkt, Straßenklasse fehlt), zusätzlich 33 Konkordanz-Prüffälle und 69
Validierungshinweise (überschneiden sich weitgehend).

## 8. 2026-09-14 — Sichtung der unsicheren Einträge

Für alle Einträge mit `status=unsicher` wurde eine **vollständige** Prüfliste erzeugt
(`llm_vergleich unsicher` → `daten/pruefung_unsicher.csv`: alle Kopffelder und Stadien je
Eintrag mit Parser- und Modellwerten, Spalte `grund` mit den Prüfgründen des Parsers,
`einig` zusätzlich `keines`), dazu Prüfbilder unter `llm/pruefbilder_unsicher/` und ein
Trockenlauf `llm_vergleich pruefen`, der vor der Übernahme meldet, was das Overlay ablehnen
würde. Der Nutzer sichtete die 162 Einträge (1.516 Zeilen) am Scan; 84 Zellen bei 52
Einträgen wurden korrigiert, per `uebernehmen --pruefliste` übernommen (91 Overlay-Zeilen,
Overlay 324 → **415**) und angewandt. Für Fälle, die dabei auftraten, wurde das Overlay
erweitert: Schlüsselwörter `zuvor` (wie `vorm.`) und `urspr.` für undatierte Stadien,
ISO-Datum `JJJJ-MM-TT` in `wert_neu`; ein aufgehobener Straßenname (00718 Siebrechtweg,
„04. April 1986 aufgehoben") ist als Stadium mit Klammerzusatz „(aufgehoben)" erfasst, eine
Doppelangabe „10./13. April 1905" (00595) precision-first auf das Jahr zurückgestuft.
Ergebnis: `geprueft` 210 → **262**, `unsicher` 164 → **112**, Stadien 5.496 → 5.513,
Konkordanz 444 → **455**, amtlich bestätigt 3.324 → **3.339** (nicht im Verzeichnis 30 → 15),
Alphabet-Auffällige 39 → 31, LLM-Prüfliste `einig=beide` 52 → 55 (keine braucht Korrektur).
Die Sichtungsfassung liegt unter `llm/pruefung_unsicher_sichtung_2026-09-14.csv`.

Die verbleibenden 112 unsicheren Einträge wurden in derselben Sichtung angesehen, aber nicht
als Bestätigung eingetragen; sie behalten `unsicher`, bis eine Bestätigungszeile vorliegt
(darunter die Buchdubletten 02402 und 03448, die das Overlay nicht adressieren kann).

## Was als Nächstes offen ist

Der Datenstand gilt als veröffentlichungsreif; nächster Schritt ist der Zenodo-Release mit
DOI. Eine **Parser-Runde 3** ist bewusst nicht geplant (Abschnitt 7). Sollte je ein neuer
Volllauf nötig werden — etwa mit besserer OCR —, sind die aus der Sichtung bekannten Muster
mit Testfällen hier festgehalten; alle Fälle sind heute per Overlay korrigiert:

- **Seitenendrest klebt am Lemma der Folgeseite**, Seitenzahl um eins zu niedrig
  (00085, 00207, 00331, 00366, 00573, 00692, 02023, 03240).
- **Bildunterschrift innerhalb eines Eintrags**: im Kopffeld (02393, 03014), im Datum (01392,
  03425, 01104), mitten auf der Seite (00720, 02681). Bildunterschriften sind als
  alleinstehende Zeile „Lemma - Beschreibung [Jahr]" erkennbar, zuverlässig aber nur, wenn
  der linke Teil ein bekanntes Lemma ist (145 Kandidatenzeilen, davon viele Fließtext).
- **Umbruch mit Seitenkopf**: R1 greift nicht über den Seitenwechsel (02425).
- **R7 auf Kopffelder ausdehnen** (00303, 02611, 02681).
- **R4-Rest**: OCR liest römische Präfixe als `!`, `Il`, `IH`, `IN`, `1.` (02681, 02874, 00334,
  00503, 00613/00614, 01162/01163, 01783, 02262, 02669/02670, 02760/02761, 02796/02797,
  02803/02804, 02960–02962, 03106/03107).
- **Parser-Auslassungen**: sechsstellige Nummer (001321), Anker vor dem Lemma (01603, 02655),
  Anker ohne Nummer in der OCR (01655), Nummer mit Ziffer zu viel (02906 „029086").
- **`vorm.:`-Stadien** ohne Datum (02512, 02513; 4 Vorkommen im Korpus).
- **Anführungszeichen/Satzreste vor dem Lemma** (03448 „Wendin“ Wangeroogeweg").
- **Verweise (`verweis_auf`)** erkennen weder Parser noch Modelle zuverlässig (Beobachtung
  des Nutzers bei der Sichtung der unsicheren Einträge, 2026-09-14). Der Parser liest heute
  nur „Siehe X" (`_VERWEIS` in `erschliessen.py`); Dickhoff verwendet aber auch „Vgl. auch X",
  „Siehe auch X" und Verweise mitten in der Erläuterung (297 Fundstellen von „Siehe …"/„Vgl.
  auch …" im OCR-Text, gefüllt sind nur 230 `verweis_auf`). Denkbar ist eine eigene, nachgeschaltete
  Stufe, die gezielt nach solchen einleitenden Markern sucht und die Ziele gegen die Lemmata
  des Datensatzes abgleicht.

**Für die Zenodo-Beschreibung** (Notiz des Nutzers, 2026-09-14): vor dem Release eine kleine
Beispielsammlung zusammenstellen, wie die Daten überarbeitet wurden, getrennt nach Ursache —
Druckfehler der Vorlage (fehlendes „r" in „-staße", „Gemeindstraße", „Familiename", fehlender
oder doppelter Marker „Str.-Kl."/„Str.-Gr.", sechsstellige Schlüsselnummer 001321,
Schlüsselnummern-Dubletten 02402/03448), OCR-Rauschen (Bildunterschriften und Randzeichen
am Lemma, „Il"/„!" für römische Präfixe, „tiw." für „tlw.", vertauschte Zeilenfolge) und
Parser-Grenzen (Umbruch mitten im Datum, undatierte Stadien „vorm.:"/„zuvor:"). Quelle dafür
sind die Belege in `daten/korrekturen.csv` (Belege mit „[sic!]" oder „Druckfehler" markieren
Fehler der Vorlage) und die Differenzberichte unter `docs/regression/`.

Ältere Restposten: `daten/pruefung.csv` führt 02568 weiterhin als „Schlüsselnummer mehrfach",
weil die Dubletten-Prüfung vor dem Overlay läuft; `pruefung_validierung.csv` zählt
Lemma-Dubletten; der `goldstandard`-Befehl überschreibt den handgeschriebenen Abschnitt
„Messgrundlage" in `ergebnis_llm.md`.
