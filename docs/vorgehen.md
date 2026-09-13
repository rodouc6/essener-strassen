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
Namenskette sank von 84 auf 10; jeder Verlust eines Stadiums, jede Umdatierung und
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
(`seitenende_ausgelassen`: 340 bei `mistral`, 334 bei `qwen`). Der Preis ist eine höhere
Zahl gekennzeichneter Einträge (`unsicher` 271 → 375): die bisher stille Anker-Toleranz
wird jetzt sichtbar gemacht. Jede Rückstufung ist einzeln geprüft im Differenzbericht
[`docs/regression/2026-09-13-parser-runde-2.md`](regression/2026-09-13-parser-runde-2.md).

## Was als Nächstes offen ist

Aus der Parser-Runde 2 bleiben Einzelfälle übrig, die kein automatisches Regelmuster
tragen und einzeln gegen den Scan geprüft werden müssen (Sichtung über die Prüfbilder,
Übernahme via Korrektur-Overlay). Langfristig geplant ist die Veröffentlichung des
Datensatzes auf Zenodo mit DOI, sobald der Datenstand als hinreichend stabil gilt.
