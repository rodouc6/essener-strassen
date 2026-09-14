# Goldstandard-Stichprobe: Prüfanleitung

> **Stand 2026-09-11 — Entwicklungs-Stichprobe.** Die erste Ziehung (Seed 1936) ist
> vollständig geprüft; das Ergebnis steht in `ergebnis.md`. Die dort gefundenen Fehler
> sind ausnahmslos *systematische* Parser-/OCR-Muster (Punkt nach „St."/„II." beendet
> die Namenskette, numerisches Datum, Seitenumbruch im Kopf, „Str.-Kl.;", getrenntes
> „Stadt-teile", Abschnittsbuchstabe im Lemma). Sie werden im Parser behoben; die
> Stichprobe dient damit der Entwicklung und ist als unabhängiges Qualitätsmaß für den
> reparierten Datensatz **verbraucht** (Fehler gefunden und behoben am selben Sample).
> Entscheidung: **keine** neue Ziehung — die Zahl wird als Entwicklungs-Stichprobe
> ausgewiesen, nicht als unabhängige Fehlerquote des Endstands.

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
     steht bzw. richtig geparst werden sollte — Daten in der Datensatzform, z. B.
     `1927-08-29` für gedrucktes „29.08.1927").
   - **Fehlt ein Feld ganz** (der Scan zeigt ein Namensstadium, der Datensatz hat es
     nicht — dann gibt es dafür auch keine Prüfzeile): eine Zeile **nachtragen**, mit
     denselben Kopfspalten, `feld` wie üblich benannt (`stadium_1_datum`,
     `stadium_1_name`), `wert` leer, `korrekt=nein`, `korrektur` = gedruckter Wert.
     Nur so zählen Auslassungen des Parsers überhaupt als Fehler.
   - Die Spalte `status` (`automatisch`/`unsicher`) ist vorbelegt und wird nicht
     bearbeitet; die Auswertung weist die Fehlerquote je Schicht getrennt aus.

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

   Das schreibt `docs/goldstandard/ergebnis.md` (Fehlerquote je Schicht, je Feldtyp
   und gesamt, dazu die Liste aller Fehler mit Korrektur) und gibt es auch auf der
   Kommandozeile aus.

   **Achtung:** `ziehen` überschreibt `stichprobe.csv`. Nach einer Prüfung nicht erneut
   ziehen, ohne die ausgefüllte Datei zu sichern. Hinzu kommt: Einträge mit
   `status=geprueft` gehören zu keiner der beiden Schichten, sodass eine neue Ziehung
   mit Seed 1936 die gespeicherte Entwicklungs-Stichprobe nicht mehr reproduziert.

## Korrekturen in den Datensatz bringen

Eine ausgefüllte Prüfzeile mit `korrekt=nein` ist noch keine Korrektur im Datensatz —
sie muss dafür als Zeile in `daten/korrekturen.csv` eingetragen werden. Diese Datei ist
Eingabe von `strassen/erschliessen.py` (Korrektur-Overlay, `strassen/korrekturen.py`),
nicht dessen Protokoll: `daten/pruefung.csv`, das Parser-Protokoll der Erschließung,
wird durch Korrekturen **nicht** bereinigt und bleibt unverändert stehen. Wirksam wird
eine Korrektur im Datensatz über den Status `geprueft` und die korrigierten Werte
selbst — nicht über eine Änderung an `pruefung.csv`.

### Spalten von `korrekturen.csv`

| Spalte | Inhalt |
|---|---|
| `schl_nr` | Schlüsselnummer des Eintrags |
| `feld` | `lemma` \| `stadtteile` \| `strassenklasse` \| `namensgruppe` \| `verweis_auf` \| `stadium_N_datum` \| `stadium_N_name` \| `stadium_N_urspruenglich` \| `eintrag` (Bestätigung ohne Wertänderung) |
| `wert_alt` | aktueller Parser-Wert **in Stichprobenform** (wie er beim Prüfen dastand, z. B. `vor 1898`); leer bei Namensstadien = nachtragen |
| `wert_neu` | korrigierter Wert; bei Daten der **gedruckte Text**, nicht die ISO-Form (z. B. `29.08.1927`, `um 1900`); leer bei beiden Feldern eines Stadiums = streichen |
| `beleg` | gedruckter Wortlaut der Stelle, ≤ 200 Zeichen |
| `quelle` | `goldstandard` \| `llm-lauf` |
| `datum` | Tag der Prüfung, ISO-Datum |

### Konvention „ganzer Eintrag"

Wer eine Zeile einträgt, hat den **ganzen Eintrag** (Kopf und Namensstadien-Kette)
gegen den Scan geprüft — nicht nur das eine korrigierte Feld. Deshalb erhält jeder
Eintrag mit mindestens einer Korrektur- oder Bestätigungszeile `status=geprueft`, die
höchste Stufe, auch wenn tatsächlich nur ein Feld abweicht.

### Datumsform

`wert_alt` bei einem Datumsfeld steht in der **Stichprobenform**, wie der Parser den
Wert aktuell liefert (z. B. `vor 1898`, `1902-05-16`) — weicht der Wert beim Anwenden
vom tatsächlichen Parser-Ergebnis ab, bricht der Lauf ab, weil die Stelle inzwischen
anders gelesen wird und neu geprüft werden muss. `wert_neu` dagegen trägt den
**gedruckten Text** aus dem Scan (`29.08.1927`, `um 1900`), nicht die ISO-Form — die
Normalisierung übernimmt das Overlay selbst (`strassen.datum.lese_text`).

### Nachtragen, Streichen, Bestätigen

- **Nachtragen** (der Scan zeigt ein Namensstadium, das im Datensatz fehlt): Zeilen für
  `stadium_N_datum` und `stadium_N_name` mit **leerem `wert_alt`** eintragen — `N` ist
  die Position, die das Stadium im Ergebnis **nach** dem Einfügen tragen soll. Beide
  Felder (Datum und Name) sind nötig, sonst bricht der Lauf ab. Die Position darf
  höchstens direkt nach dem Ende der bisherigen Kette liegen.
- **Streichen** (ein vom Parser erfasstes Stadium existiert im Scan gar nicht): Zeilen
  für `stadium_N_datum` und `stadium_N_name` mit gefülltem `wert_alt` (dem aktuellen
  Wert) und **beide `wert_neu` leer** eintragen — nur wenn beide Felder eines Stadiums
  so markiert sind, wird gestrichen.
- **Bestätigen** (der ganze Eintrag stimmt, keine Korrektur nötig): eine Zeile mit
  `feld=eintrag` und leeren `wert_alt`/`wert_neu` eintragen. Bewirkt nur den
  Statuswechsel auf `geprueft`.

### Seitenzahl, Schlüsselnummer, Neuanlage, undatiertes Stadium

Seit 2026-09-13 kann das Overlay auch das reparieren, was der Parser strukturell falsch
liest (Parser-Runde 3 wurde zugunsten dieser Erweiterung nicht durchgeführt, Begründung in
`docs/vorgehen.md`):

- `feld=buchseite`: `wert_alt` = bisherige Seite, `wert_neu` = richtige Seite. Nötig, wenn ein
  Eintrag wegen eines Seitenendrests der Vorseite zugeordnet wurde.
- `feld=schl_nr`: die Zeile steht unter der **alten** Nummer, `wert_alt` = **Lemma** des
  Eintrags (so ist auch eine Dublette eindeutig adressiert), `wert_neu` = neue Nummer. Wird vor
  allen anderen Zeilen angewandt; weitere Zeilen zum Eintrag stehen unter der neuen Nummer.
  Bei einer Dublette bleiben die Stadien unter der alten Nummer (welche zu welchem Eintrag
  gehören, ist nicht entscheidbar) und werden per Streichen/Nachtrag zugeordnet.
- **Neuanlage** eines vom Parser ausgelassenen Eintrags: `feld=eintrag`, `wert_alt` leer,
  `wert_neu` = Lemma; dazu unter derselben Nummer `buchseite` (Pflicht), Kopffelder (jeweils
  `wert_alt` leer) und die Stadien als Nachträge. Der Beleg der `eintrag`-Zeile enthält den
  gedruckten Kopf. Eine sechsstellige Nummer im Druck (001321) wird so übernommen, wie sie
  gedruckt ist — nicht auf fünf Stellen geraten.
- **Undatiertes Stadium** („vorm.: Name" in der Vorlage): Nachtrag mit `wert_neu = vorm.` im
  Datumsfeld ergibt `datum_praezision=unbekannt`, `gueltig_ab` leer, `ist_urspruenglich=falsch`.
  Analog `wert_neu = zuvor` für „zuvor: Name" (wie `vorm.`) und `wert_neu = urspr.` für
  „urspr. Name" ohne Datum (`ist_urspruenglich=wahr`), etwa
  wenn der Parser die Kette wegen eines fehlenden Doppelpunkts nicht erkannt hat (03203).

### Anwenden

```bash
python3 -m strassen.erschliessen
```

läuft die Pipeline neu und wendet dabei das Korrektur-Overlay auf die frische
Parser-Ausgabe an. **Abbruch bei abweichendem `wert_alt`:** Stimmt der eingetragene
`wert_alt` nicht mit dem tatsächlichen Parser-Wert überein, bricht der Lauf mit einer
`KorrekturFehler`-Meldung ab (kein stiller Fehlanwendungsversuch) — die betroffene
Stelle muss neu gegen den Scan geprüft und `wert_alt` aktualisiert werden, bevor der
Lauf erneut gestartet wird.

### Sichtung der LLM-Prüfliste

Für die Zeilen mit `einig=beide` (beide Modelle lesen übereinstimmend anders als der
Datensatz) erzeugt

```bash
python3 -m strassen.pruefbilder [--einig beide] [--quelle DIR] [--ziel DIR]
```

je Eintrag genau einen Scan-Ausschnitt nach `llm/pruefbilder/` (gitignored, da die
Seitenbilder urheberrechtlich geschützt sind) sowie eine Übersichtstabelle
`llm/pruefbilder/index.md`. `--einig` ist mehrfach angebbar (Standard: nur `beide`),
`--quelle` und `--ziel` weichen nur bei abweichender Verzeichnisstruktur vom
Vorgabewert ab. Der Lauf ist idempotent — bereits gerenderte Bilder werden nicht neu
erzeugt.

Ablauf: `llm/pruefbilder/index.md` öffnen, zeilenweise das verlinkte Bild ansehen und
mit dem Drucktext vergleichen, dann wie unten beschrieben in `daten/pruefung_llm.csv`
die Spalten `korrektur` und `beleg` ausfüllen und mit `uebernehmen` in den Datensatz
übertragen.

### Für die LLM-Prüfliste

Funde aus der unabhängigen LLM-Lesung stehen in `daten/pruefung_llm.csv`
(`strassen/llm_vergleich.py pruefliste`). Nach dem Prüfen gegen den Scan dort die
Spalten `korrektur` und `beleg` ausfüllen (wie bei der Goldstandard-Stichprobe) und
anschließend

```bash
python3 -m strassen.llm_vergleich uebernehmen
```

ausführen — das überträgt die geprüften Funde nach `daten/korrekturen.csv`
(`quelle=llm-lauf`). Anschließend wie oben `python3 -m strassen.erschliessen` neu
laufen lassen, damit die Korrekturen wirksam werden.

Erfahrungen aus der Sichtung vom 2026-09-13, die `uebernehmen` und das Overlay voraussetzen:

- **Datum** in `korrektur` wie gedruckt oder als `TT.MM.JJJJ` eintragen — nicht als ISO-Datum
  (`JJJJ-MM-TT` wird vom Overlay nicht gelesen). Ein Datum, das der Parser selbst nur
  eingeschränkt lesen kann (z. B. Doppeljahr „etwa 1910/11"), lässt sich nicht als
  Korrektur eintragen; der Parser-Wert bleibt.
- **Ganzes Stadium nachtragen** (`feld=stadium_N`, `wert_parser` leer): `DATUM | NAME` mit
  senkrechtem Strich. Fehlt in der Prüfliste die Namenszeile, weil die Modelle nur das
  Datum sahen (Umbruch), die Zeile `stadium_N_datum` auf `stadium_N` umbenennen und beide
  Werte eintragen. Ein Stadium **vor** einem vorhandenen einfügen (Position 1 belegt) geht
  nur direkt in `daten/korrekturen.csv` mit leerem `wert_alt`; das vorhandene rückt auf.
- Zeilen `stadium_N` **mit** Parser-Wert sind nur Anzeige (Stadium als Ganzes weicht ab);
  die Korrektur gehört in die Teilfeld-Zeile `stadium_N_name` bzw. `_datum`.
- **`korrektur = wert_parser`** heißt: Parser hat recht, Eintrag am Scan geprüft. Solche
  Zeilen werden nicht als Korrektur, sondern als Bestätigung (`feld=eintrag`, `wert_alt`
  und `wert_neu` leer) ins Overlay geschrieben und heben den Eintrag ebenfalls auf
  `geprueft`.
- **`[sic!]`** gehört in den Beleg, nie in den Wert. Ein leerer Beleg bedeutet: Wortlaut
  identisch mit `korrektur`, am Prüfbild gesichtet.
- **Eintrag nicht auf dem Prüfbild?** Dann beginnt er oben auf der Folgeseite
  (Seitenendrest am Lemma, Parser-Seitenzahl um eins zu niedrig). Folgeseite rendern:
  `rendere_ausschnitt(*buchseite_zu_scan(N+1), QUELLE_PFAD, ziel, dpi=150)` aus
  `strassen.goldstandard`.

### Sichtung der unsicheren Einträge

Für alle Einträge mit `status=unsicher` erzeugt

```bash
python3 -m strassen.llm_vergleich unsicher            # -> daten/pruefung_unsicher.csv
python3 -m strassen.pruefbilder --pruefliste daten/pruefung_unsicher.csv \
        --ziel llm/pruefbilder_unsicher --einig beide --einig eines --einig keines --einig unlesbar
```

eine **vollständige** Prüfliste (alle Kopffelder und Stadien je Eintrag, nicht nur
Abweichungen) im Format der LLM-Prüfliste, ergänzt um die Spalte `grund` mit den
Prüfgründen des Parsers. `einig` kennt hier zusätzlich `keines` (beide Modelle lesen wie
der Parser). Die Sichtung läuft wie oben: Prüfbild ansehen, bei Parser-Fehlern `korrektur`
und `beleg` füllen; ist der ganze Eintrag korrekt, in **einer** Zeile des Eintrags
`korrektur = wert_parser` eintragen — das wird bei der Übernahme zur Bestätigung
(`feld=eintrag`) und hebt den Eintrag auf `geprueft`. Übernahme dann mit

```bash
python3 -m strassen.llm_vergleich uebernehmen --pruefliste daten/pruefung_unsicher.csv
python3 -m strassen.erschliessen && python3 -m strassen.veroeffentlichen
```

Zwischendurch prüft ein Trockenlauf, ob die bisher ausgefüllten Zellen durchgehen würden,
ohne etwas zu verändern:

```bash
python3 -m strassen.llm_vergleich pruefen --pruefliste daten/pruefung_unsicher.csv
```

Regeln, die dabei am häufigsten anschlagen: Nur die Spalte `korrektur` wirkt — Werte in
`wert_parser` einer handangelegten Zeile tun nichts. Ein fehlendes Stadium wird als Zeile
`stadium_N` (Zielposition, `wert_parser` leer, `korrektur` = `DATUM | NAME`) nachgetragen;
vorhandene Stadien werden nie von Hand umnummeriert, sie rücken von selbst auf. Modellwerte
wie „(nicht normalisierbar)" gehören nie in `korrektur`; ein Jahrhundert wird als
`16. Jahrhundert` eingetragen.

Schlüsselnummern-Dubletten (02402, 03448) fallen in dieser Liste zusammen und sind über
`schl_nr` nicht korrigierbar; sie bleiben `unsicher`, solange sie so im Buch stehen.

## Hinweis zur Stichprobe selbst

Die Ziehung ist geschichtet (40 automatisch, 10 unsicher) und deterministisch
(`random.Random(1936)` — Anspielung auf den Erhebungsstand des Adressbuchs, kein
Bezug zu diesem Projekt). Beide Statusgruppen sind bewusst vertreten, weil sie
unterschiedliche Fehlerprofile haben dürften: `unsicher` markiert Einträge, die der
Parser selbst nicht sicher erschließen konnte (s. README, Abschnitt „Methode").
