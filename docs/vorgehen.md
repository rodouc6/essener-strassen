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
Die Prüfliste wurde danach neu erzeugt: 3.355 Zeilen, `einig=beide` 288 → **57**.

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

## Was als Nächstes offen ist

Langfristig geplant ist die Veröffentlichung des Datensatzes auf Zenodo mit DOI, sobald
der Datenstand als hinreichend stabil gilt. Aus der Sichtung ergeben sich Kandidaten für
eine **Parser-Runde 3** (Testfälle jeweils mit Schlüsselnummer):

- **Seitenendrest klebt am Lemma der Folgeseite**, Seitenzahl um eins zu niedrig:
  Bildunterschriften und OCR-Müll am Fuß einer Seite werden dem nächsten Eintrag
  vorangestellt (00085, 00207, 00331, 00366, 00573, 00692, 02023, 03240). Die Lemmata sind
  per Overlay korrigiert, die `buchseite` bleibt falsch, weil sie kein Overlay-Feld ist.
- **Bildunterschrift innerhalb eines Eintrags** (am Seitenanfang): im Kopffeld (02393,
  03014), im Datum (01392, 03425, 01104 — Datum über den Umbruch geteilt) oder mitten auf
  der Seite (00720 „Tas", 02681). Der Parser verliert dann ein Stadium oder zieht die
  Bildunterschrift in die Namensgruppe.
- **Umbruch mit Seitenkopf**: R1 (Trennstrich vor Großbuchstabe) greift nicht über den
  Seitenwechsel, weil „Essener Straßen" und die Seitenzahl dazwischenstehen (02425
  „Malerviertel- Holsterhausen"). Seitenkopf und -zahl vor dem Zusammenfügen entfernen.
- **R7 auf Kopffelder ausdehnen**: beim letzten Eintrag einer Seite ist eine
  Modellabweichung in Kopffeldern fast immer ein Umbruch-Artefakt (00303, 02611, 02681).
- **R4-Rest**: OCR liest römische Präfixe als `!`, `Il`, `IH`, `IN`, `1.` (02681, 02874,
  00334, 00503, 00613/00614, 01162/01163, 01783, 02262, 02669/02670, 02760/02761,
  02796/02797, 02803/02804, 02960–02962, 03106/03107); per Overlay korrigiert.
- **Parser-Auslassungen** (Eintrag fehlt ganz, nicht per Overlay behebbar): 01603
  (OCR-Zeilenfolge vertauscht: Anker vor Lemma), 01655, 02566 (Folge der
  Schlüsselnummer-Dublette 02568), 02655, 02906; 001321 ist eine Fehllesung der Modelle.
- **`vorm.:`-Stadien** ohne Datum gehen verloren (02512 Bolsterbaum, 02513 Bonifaciusstraße,
  4 Vorkommen im Korpus); die Namensgruppe ist bereinigt, das Stadium fehlt.
- **Anführungszeichen/Satzreste vor dem Lemma** (03448 „Wendin“ Wangeroogeweg").
- **Overlay-Feld `schl_nr`** für OCR-Fehler in Schlüsselnummern (02568 → 02566).
- Die 37 Prosa-Lemmata (Lemmata mit mehr als vier Wörtern) sind großteils durch die
  Sichtung korrigiert; der Rest steht in `daten/pruefung_validierung.csv` (grund=Alphabet).
