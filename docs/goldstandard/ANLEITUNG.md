# Goldstandard-Stichprobe: Prüfanleitung

Diese Stichprobe misst die tatsächliche Feldfehlerquote des Datensatzes, indem 50
zufällig gezogene Einträge (40 mit `status=automatisch`, 10 mit `status=unsicher`)
Zeichen für Zeichen gegen den Original-Scan geprüft werden. Die Prüfung ist ein
manueller Schritt — dieses Dokument beschreibt ihn.

## Ablauf

1. `python3 -m strassen.goldstandard ziehen` wurde bereits ausgeführt (oder erneut
   ausführen, falls sich `daten/strassen.csv`/`daten/namen.csv` geändert haben — die
   Ziehung ist deterministisch, dieselbe Stichprobe kommt bei unveränderten Eingaben
   wieder heraus). Ergebnis: `docs/goldstandard/stichprobe.csv` (eine Zeile je
   Prüffeld) und `docs/goldstandard/scans/` (ein PNG-Ausschnitt je geprüftem Eintrag,
   **nur lokal**, nicht versioniert).

2. `stichprobe.csv` öffnen (z. B. in LibreOffice Calc oder einem Editor mit
   CSV-Ansicht). Für jede Zeile:
   - Zum passenden Scan-Ausschnitt wechseln: Dateiname
     `docs/goldstandard/scans/schlnr_<schl_nr>_s<buchseite>.png` (steht auch in den
     Spalten `schl_nr`/`buchseite`; `band`, `pdf_seite`, `haelfte` dokumentieren, woher
     der Ausschnitt stammt, werden zur Prüfung selbst aber nicht gebraucht — der Scan
     ist schon zugeschnitten).
   - Im Ausschnitt den Eintrag mit der Schlüsselnummer `schl_nr` suchen (Lemma-Spalte
     hilft beim Auffinden).
   - Den Wert in Spalte `wert` **zeichengenau** mit dem gedruckten Feld vergleichen.
     Die Spalte `feld` sagt, was geprüft wird:
     - `schl_nr`, `lemma`, `stadtteile`, `strassenklasse`, `namensgruppe`: die
       jeweilige Kopfangabe.
     - `verweis_auf`: bei „Siehe X"-Einträgen das Ziel-Lemma — ist die Spalte leer,
       prüfen, ob der Scan tatsächlich keinen Verweis zeigt.
     - `stadium_N_datum` / `stadium_N_name`: Datum bzw. Name des N-ten
       Namensstadiums in der gedruckten Kette (N = 1 ältestes Stadium).
   - Spalte `korrekt`: `ja` eintragen, wenn der Wert exakt dem gedruckten Inhalt
     entspricht, sonst `nein`.
   - Bei `nein` in Spalte `korrektur` den richtigen Wert eintragen (wie er gedruckt
     steht bzw. richtig geparst werden sollte).

3. **OCR-Konventionen gelten als korrekt**, wenn der Sinn exakt erhalten ist —
   maßgeblich ist der **gedruckte Inhalt**, nicht die Zeilenaufteilung der Vorlage.
   Insbesondere:
   - aufgelöste Silbentrennung (Wort über Zeilenumbruch getrennt, im Datensatz als
     ein Wort) zählt als korrekt, solange kein Zeichen fehlt oder falsch ist;
   - normalisierte Leerzeichen um Satzzeichen/Bindestriche zählen als korrekt, wenn
     der Name dadurch nicht verändert wird.
   Tatsächliche OCR-Fehler (falsch erkannte Buchstaben, fehlende/vertauschte
   Zeichen, falsches Datum, falsche Schlüsselnummer) zählen **nicht** als korrekt,
   auch wenn sie plausibel aussehen.

4. Wenn alle Zeilen ausgefüllt sind (oder mindestens 90 % — der Rest kann als „noch
   offen" stehen bleiben, mehr als 10 % offen bricht die Auswertung ab):

   ```bash
   python3 -m strassen.goldstandard auswerten
   ```

   Das schreibt `docs/goldstandard/ergebnis.md` (Fehlerquote je Feldtyp und gesamt)
   und gibt es auch auf der Kommandozeile aus.

## Hinweis zur Stichprobe selbst

Die Ziehung ist geschichtet (40 automatisch, 10 unsicher) und deterministisch
(`random.Random(1936)` — Anspielung auf den Erhebungsstand des Adressbuchs, kein
Bezug zu diesem Projekt). Beide Statusgruppen sind bewusst vertreten, weil sie
unterschiedliche Fehlerprofile haben dürften: `unsicher` markiert Einträge, die der
Parser selbst nicht sicher erschließen konnte (s. README, Abschnitt „Methode").
