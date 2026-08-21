# Erhebungsstand des Adressbuchs Essen 1936

Misst, welchen Namensstand das Adressbuch Essen 1936 (Adressbuch-Datensatz des
Kartenprojekts, siehe README, Abschnitt „Externe Eingaben")
tatsächlich abbildet, und leitet daraus die Konkordanz für das Kartenprojekt ab
(`strassen/stichtag.py`, `tests/test_stichtag.py`).

## Methode

Für jede Umbenennung (Übergang von einem Namensstadium zum nächsten in
`daten/namen.csv`) wird geprüft, ob das Adressbuch die alte oder die neue
Namensform verwendet (Straßennamen kleingeschrieben, „str."/„straße"
vereinheitlicht). Stadien ohne verwertbares Datum (`datum_praezision`
`unbekannt`) werden übersprungen, nie geschätzt. Jahrpräzision wird für die
Stichtagsfrage konservativ auf Jahresende gelegt; für die **monatsscharfe**
Auswertung wird sie ausgeschlossen, weil sie keinen echten Monat liefert —
das würde sonst einen Monat erfinden statt ihn aus den Daten zu lesen. Im
ausgewerteten Zeitraum (1935–1937) sind ohnehin alle tatsächlichen
Umbenennungs-Übergänge tagesgenau datiert (363 von 363), sodass dadurch
nichts verloren geht.

## Jährliche Auswertung

| Jahr | alt (Adressbuch nutzt alten Namen) | neu (Adressbuch nutzt neuen Namen) |
|-----:|------------------------------------:|-------------------------------------:|
| 1930 |  3 |  7 |
| 1931 |  9 |  6 |
| 1932 |  0 |  2 |
| 1933 | 19 | 14 |
| 1934 | 14 | 11 |
| 1935 |  9 | 23 |
| 1936 | 20 |  5 |
| 1937 | 183 | 0 |
| 1938 |  3 |  1 |
| 1939 |  3 |  0 |
| 1940 |  1 |  0 |

Bestätigt die frühere Grobmessung und präzisiert sie: 1937 ist mit der
tagesgenauen Dickhoff-Datierung 183:0 (statt vorher 196:15 auf schwächerer
Basis) praktisch vollständig unreflektiert; 1935 ist überwiegend reflektiert
(23:9); 1936 kippt bereits deutlich zu „alt" (20:5) — die Übergangszone.

## Monatsscharfe Auswertung (1935-01 bis 1937-12)

| Monat | alt | neu |
|-------|----:|----:|
| 1935-01 | 0 | 3 |
| 1935-02 | 1 | 0 |
| 1935-05 | 1 | 0 |
| 1935-06 | 0 | 2 |
| 1935-09 | 0 | 1 |
| 1935-10 | 0 | 11 |
| 1935-11 | 7 | 6 |
| 1936-01 | 12 | 5 |
| 1936-02 | 1 | 0 |
| 1936-08 | 7 | 0 |
| 1937-01 | 1 | 0 |
| 1937-02 | 22 | 0 |
| 1937-11 | 160 | 0 |

(Nur Monate mit mindestens einer tagesgenau datierten Umbenennung sind
aufgeführt; alle übrigen Monate im Bereich hatten keinen Übergang.)

## Interpretation

Der letzte Monat mit noch gemischtem Befund (Adressbuch zeigt teils schon
den neuen Namen) ist **1935-11** (7 alt : 6 neu); **1936-01** ist noch
gemischt, aber bereits deutlich zu „alt" verschoben (12:5). Ab **1936-02**
zeigt jeder ausgewertete Monat bis einschließlich 1937 ausschließlich „alt"
— das Adressbuch reflektiert keine einzige Umbenennung mehr, die ab Februar
1936 in Kraft trat. Das grenzt den tatsächlichen Erhebungsschluss des
Adressbuchs auf etwa **Ende 1935 bis Januar 1936** ein — plausibel für ein
Werk mit Titeljahr 1936, dessen Datenerhebung typischerweise im Vorjahr
abgeschlossen wird.

Die Daten reichen nicht aus, um den Erhebungsschluss monatsgenau
festzulegen: Zwischen November 1935 und Januar 1937 liegen nur vereinzelte
Umbenennungs-Ereignisse (Februar und August 1936, Januar und Februar 1937),
dazwischen mehrmonatige Lücken ohne jede Umbenennung — die Daten sagen für
diese Lücken schlicht nichts. Das ist aber für die Stichtagswahl praktisch
folgenlos: **jeder Stichtag zwischen ca. Februar 1936 und Januar 1937**
liefert dieselbe Zuordnung, weil in diesem gesamten Fenster keine weitere
Umbenennung mehr vom Adressbuch reflektiert wird. Der in Schritt 5
verwendete Stichtag **1936-06-30 liegt komfortabel in diesem stabilen
Fenster** und ist als Arbeitswert für die Konkordanz gut begründet, auch
wenn der exakte Erhebungsschluss unscharf bleibt. Eine engere Festlegung
(z. B. auf 1935-12-31) wäre nicht durch zusätzliche Daten gedeckt und würde
das Ergebnis der Konkordanz nicht ändern, da im fraglichen Fenster ohnehin
keine Umbenennung mehr ansteht.

## Konkordanz-Ableitung (`daten/konkordanz_1936.csv`)

Stichtag: **1936-06-30** (vorläufiger Arbeitswert, s. o. — noch keine
Nutzer-Festlegung auf einen engeren Zeitpunkt).

Die Konkordanz wird **nur aus Straßen mit `status=automatisch`** gebaut;
unsichere Lemmata (`status=unsicher`) gehören nicht in die produktive
Konkordanz, da ihr heutiger Name selbst nicht belastbar ist.

- Straßen gesamt: 3.338
- davon `status=automatisch` (Basis der Konkordanz): 3.100
- davon `status=unsicher` (ausgeschlossen): 238
- Konkordanzeinträge (nur `automatisch`, Stichtag 1936-06-30): **576**
  (zum Vergleich, mit den unsicheren Lemmata mitgerechnet: 670 — die 94
  Differenz sind Fälle, in denen eine unsichere Straße zum Stichtag einen
  vom heutigen Namen abweichenden historischen Namen hätte)
- bisherige (Wikipedia-)Konkordanz: 442

576 ist damit deutlich mehr als die bisherigen 442 — wie erwartet, da die
taggenaue Dickhoff-Datierung mehr Umbenennungen sicher vor bzw. nach dem
Stichtag einordnen kann als die gröbere Vorabmessung.

**Diese 576 sind durch Fix-Runde 1 und Fix-Runde 2 (s. u.) überholt** — die
dortigen 393 Einträge sind der aktuelle, produktive Stand von
`daten/konkordanz_1936.csv`.

## Fix-Runde 1 (Review von Task 7)

Die Review von Task 7 fand drei mechanische Probleme in der 576er-Konkordanz.
Der Controller hat dazu drei bindende Rulings getroffen, alle in
`strassen/stichtag.py` umgesetzt (`baue_konkordanz`, neue Funktion
`pruefe_konkordanz`) und mit Tests in `tests/test_stichtag.py` abgesichert.

**Ruling A — Klammerzusätze.** 228 von 576 Zeilen trugen Dickhoffs
Klammervermerke („(tlw.)", „(Verl.)", auch OCR-Varianten wie „{tlw.)",
„(t!w.)") noch im `ehemalig`-Namen und konnten dadurch nie einen
Adressbuch-Eintrag treffen. `baue_konkordanz` trennt jetzt jeden
Klammerausdruck am Namensende in eine eigene Spalte `zusatz` ab (Muster:
öffnende Klammer `(` oder `{`, schließende `)` oder `}`, beliebiger Inhalt
dazwischen) — sowohl für `ehemalig` als auch, falls vorhanden, für `heutig`
(in den echten Daten kommt das bei `heutig` nicht vor). Die
Umbenennungs-Information („nur Teil/Verlängerung betroffen") bleibt so
erhalten, der Name wird aber matchbar.

**Ruling B — Kollisionen.** Zwei Straßen im selben Stadtteil können nach der
Zusatz-Abtrennung denselben historischen Namen tragen (z. B. „Hochstraße" in
Kettwig kommt zweimal vor: schl_nr 03601 und 03736, beide zu
`(stadtteil, ehemalig)` = `(Kettwig, Hochstraße)`). Für den Adressbuch-Abgleich
sind sie nicht unterscheidbar. Jede Konkordanzzeile trägt jetzt eine Spalte
`eindeutig` (`ja`/`nein`); alle Mitglieder einer Kollisionsgruppe werden
`nein`. Ein nachgelagerter Consumer darf `eindeutig=nein`-Zeilen nicht mehr
still ineinander überschreiben, sondern muss sie erkennbar unterscheiden
oder verwerfen.

**Ruling C — mechanisches Konsistenz-Netz.** Mehrere Zeilen entstanden aus
unvollständigen oder korrupten Namensketten, z. B. schl_nr 00286: einziges
Stadium in `daten/namen.csv` ist „Marktplatz" (1900), das Lemma aber
„Barbarossaplatz" — die tatsächliche Umbenennung vom 14.11.1935 fehlt als
Stadium-Eintrag, die alte Konkordanzzeile „Marktplatz → Barbarossaplatz" war
dadurch falsch datiert. `baue_konkordanz` vergleicht jetzt für jede Straße
das chronologisch letzte datierte Stadium (zusatzbereinigt, normalisiert:
kleinschreiben, Whitespace vereinheitlicht, ß/ss angeglichen,
„str."/„straße" vereinheitlicht) mit dem aktuellen Lemma. Bei Abweichung
wird die Zeile **nicht** in die Konkordanz aufgenommen, sondern als
Prüffall zurückgegeben. Diese Prüfung ist vom Stichtag selbst unabhängig
(sie fragt nach der Konsistenz der ganzen Kette), hängt hier aber am
Stichtag-Parameter, weil nur die Straßen interessieren, die am Stichtag
überhaupt eine (potenzielle) Konkordanzzeile erzeugen würden — daher die
Signatur `pruefe_konkordanz(strassen, namen, stichtag)` (mit Stichtag,
abweichend vom Vorschlag im Ruling, aber dokumentiert).

Wichtig für Ruling C: Der Zusatz muss VOR dem Vergleich abgetrennt werden.
Ohne das hätten 256 der 529 im Datensatz global auftretenden
Ketten-Abweichungen fälschlich als Prüffall gegolten — reine
Formatierungsfälle wie „Aachener Straße (Verl.)" vs. Lemma „Aachener
Straße", bei denen die Kette in Wahrheit konsistent ist.

Die 7 vom Review benannten Fälle (00286, 03625, 03609, 00495, 00347, 00176,
00177) landen alle korrekt in `daten/pruefung_konkordanz.csv`, nicht mehr in
der Konkordanz — geprüft per Test und per Lauf auf den echten Daten.

`daten/pruefung_konkordanz.csv` verwendet dieselben Spaltennamen wie das von
`erschliessen` erzeugte `daten/pruefung.csv` (`buchseite`, `grund`), mit
`lemma` statt `lemma_roh` und `befund` statt `rohtext` — bewusst eine
eigene Datei, damit ein erneuter Pipeline-Lauf (`erschliessen` →
`pruefung.csv`) die Konkordanz-Prüffälle nicht überschreibt.

**Ergänzender Fund beim Umsetzen von Ruling A (nicht separat beauftragt,
aber eine direkte Konsequenz davon):** Bei 83 der ursprünglich 576 Zeilen
unterschied sich das Stadium vom Lemma nur durch einen Klammerzusatz (z. B.
Stadium „Aachener Straße (Verl.)" vs. Lemma „Aachener Straße") — nach
Abtrennung des Zusatzes ist der Name unverändert, es liegt also gar keine
echte Umbenennung vor. Der ursprüngliche „Name unverändert"-Check (aus dem
Brief) verglich nur die rohen Strings und griff hier nicht, weil sich die
rohen Strings durch den Zusatz unterschieden. Mit Ruling A hätte das sonst
83 sinnentleerte Konkordanzzeilen erzeugt (`ehemalig` == `heutig`). Der
Check wurde daher auf die zusatzbereinigten Namen verlegt (vor dem
Ruling-C-Konsistenz-Check); diese 83 Fälle erzeugen jetzt korrekt gar
keinen Eintrag. Test: `test_baue_konkordanz_laesst_nur_zusatz_unterschied_aus`.

### Neue Kennzahlen (Stichtag 1936-06-30, nur `status=automatisch`)

Die ursprünglichen 576 Zeilen zerfallen jetzt in drei Gruppen: 392 echte
Konkordanzeinträge, 101 Prüffälle (Ruling C) und 83 durch Zusatz-Abtrennung
als „unverändert" erkannte Nicht-Umbenennungen (392 + 101 + 83 = 576).

- Konkordanzeinträge gesamt: **392** (vorher 576)
- davon `eindeutig=ja`: 355
- davon `eindeutig=nein` (Kollisionen, Ruling B): 37
- davon mit nicht-leerem `zusatz` (Ruling A): 130
- Prüffälle (`daten/pruefung_konkordanz.csv`): **101**
- als „unverändert" erkannt und daher weder Konkordanz noch Prüffall: **83**
- Adressbuch-Matchquote der bereinigten `ehemalig`-Namen: **332 / 392**
  (84,7 %) literal (roh, kleingeschrieben, wie in der Review gemessen — dort
  vorher 288/348 bei den bereits „sauberen", zusatzfreien Zeilen); mit
  zusätzlicher „str."/„straße"-Normalisierung (`_norm_strasse`) **356 / 392**
  (90,8 %). Die verbleibenden Nicht-Treffer sind überwiegend Straßen, die
  1936 noch nicht bebaut/adressiert waren, oder Schreibvarianten, die über
  die vereinbarte Normalisierung hinausgehen — beides außerhalb des Scopes
  dieser Fix-Runde.

### Minor-Fixes

Bei der Erhebungsstand-Messung (jährlich wie monatlich) bleiben Straßen
unberücksichtigt, deren `gueltig_ab` nur ein Jahr angibt (keinen Tag) UND
die zugleich das einzige Stadium ihrer Straße sind — ohne Vorgänger-Stadium
gibt es keinen Übergang zu zählen. 7 Stadien in `daten/namen.csv` tragen
exakt `gueltig_ab=1936` (jahr- oder vor-Präzision); davon sind 4
(schl_nr 00118, 02150, 03635, 03750) zugleich das einzige Stadium ihrer
Straße und werden dadurch von der Messung vollständig übergangen (die
übrigen 3 haben weitere Stadien und tragen dort ganz normal zu jährlichen
Übergängen bei, sofern diese tagesgenau datiert sind).

Die Kommentierung von `_vergleichbar` wurde ergänzt: 'vor'-Präzision wird
dort wie 'jahr'-Präzision behandelt (nur der Jahreswert, konservativ auf
Jahresende gelegt); das ist unproblematisch, weil 'vor' bedeutet „irgendwann
vor diesem Jahr" — das tatsächliche Datum kann also nur noch früher liegen,
die Reihenfolge zu späteren Stadien bleibt korrekt, und bei Stichtags- bzw.
Kettenvergleichen mit einem so späten Bezugspunkt wie 1936 wirkt sich das
nicht aus.

## Selbstdurchsicht (5 Stichproben gegen Rohtext und Adressbuch)

| schl_nr | ehemalig (Konkordanz) | heutig | Adressbuch: ehemalig-Treffer | Adressbuch: heutig-Treffer |
|---------|------------------------|--------|------------------------------:|------------------------------:|
| 01838 | Klosterstraße | Kütings Garten | 25 | 0 |
| 00658 | Gartenkamp (tlw.) | Dreigarbenfeld | 109 | 0 |
| 02929 | Ringstraße | Stauseebogen | 16 | 0 |
| 03425 | Herderstraße | Woermannstraße | 11 | 0 |
| 00650 | Schellbergstraße | Dornbuschhegge | 19 | 0 |

Alle fünf Stichproben bestätigt: `daten/namen.csv`/`daten/strassen.csv`
weisen die Umbenennung korrekt nach dem Stichtag aus (bei 01838 explizit der
Brief-Testfall: Klosterstraße 1926–1937, danach Kütings Garten), und das
Adressbuch 1936 enthält ausschließlich den historischen Namen, nie den
heutigen — direkte empirische Bestätigung der Konkordanzrichtung.

Ein Nebenbefund bei 03425 (Woermannstraße): `daten/namen.csv` führt nur ein
einziges Stadium („Herderstraße", `vor 1922`) und keinen expliziten
Stadium-Eintrag für den Übergang zu „Woermannstraße" — das ist eine Lücke in
den Ursprungsdaten (Dickhoff-Erschließung), nicht im hier implementierten
Code. Der Adressbuch-Abgleich (11 Treffer „Herderstraße", 0 Treffer
„Woermannstraße") bestätigt empirisch, dass die Konkordanzzeile trotz der
Datenlücke korrekt ist.

(03425 selbst zeigt hier übrigens gerade die Grenze von Ruling C: das
einzige Stadium „Herderstraße" ≠ Lemma „Woermannstraße", müsste also
eigentlich ein Prüffall sein. Es bleibt aber ein Prüffall — der Lauf auf den
echten Daten bestätigt das, s. u.; die Stichprobe hier oben stammt aus der
Vor-Fix-Runde-Messung und ist durch Ruling C überholt.)

### Stichproben Fix-Runde 1

- **00286 raus?** Ja — `baue_konkordanz` liefert keine Zeile für 00286 mehr;
  `pruefe_konkordanz` liefert dafür genau einen Prüffall mit
  `grund="Namenskette unvollständig (letztes Stadium ≠ Lemma)"` und
  `lemma="Barbarossaplatz"`.
- **„Hochstraße" matchbar?** Ja — sechs Konkordanzzeilen mit
  `ehemalig="Hochstraße"` (schl_nr 03601, 00141, 00886, 03736, 02466, 02468),
  je nach Fall mit `zusatz="(tiw.)"` oder ohne. Davon sind vier über
  `eindeutig="nein"` als Kollision markiert (zwei in Kettwig: 03601/03736;
  zwei in Werden: 00886/02466 — Ruling B greift hier tatsächlich in echten
  Daten), die übrigen zwei (Stadtkern/00141, Kupferdreh/02468) sind
  `eindeutig="ja"`.
- **01838 unverändert korrekt?** Ja — weiterhin
  `{"stadtteil": "Freisenbruch", "ehemalig": "Klosterstraße", "heutig":
  "Kütings Garten", "zusatz": "", "eindeutig": "ja"}`, exakt wie vor der
  Fix-Runde (der Brief-Testfall ist von keinem der drei Rulings betroffen).

## Fix-Runde 2 (Re-Review von Task 7)

Restfund aus der Re-Review: Der „unverändert"-Drop aus Fix-Runde 1 (Zusatz-Fund)
verwarf **alle** Zeilen mit `ehemalig == heutig` nach Zusatz-Abtrennung, auch dann,
wenn der Zusatz selbst inhaltliche Information trug. Konkreter Fall: schl_nr 00318
Beisenstraße (Katernberg) — 1936 galt laut Dickhoff „Beisenstraße (tlw.)"; nach
Abtrennung von „(tlw.)" ist `ehemalig == heutig == "Beisenstraße"`, und die Zeile
wurde kommentarlos verworfen. Das kostet Information: „(tlw.)" heißt „teilweise" —
nur ein Teil der Straße trug 1936 diesen Namen, und das ist etwas, das eine
Konkordanz eigentlich festhalten sollte, statt es stillschweigend zu verschlucken.

**Empirische Prüfung der 83 betroffenen Zeilen aus Fix-Runde 1** (per Zusatz
klassifiziert, vor der Ruling-C-Prüfung, siehe Analyse-Lauf):

| Zusatz (klein, normalisiert) | Anzahl | Einordnung |
|---|---:|---|
| leer | — (nicht Teil der 83; das ist der reguläre Brief-Fall) | — |
| `(verl.)` | 60 | administrativ (Verlängerung) |
| `(verl)` | 18 | administrativ (Verlängerung) |
| `(umb.)` | 2 | administrativ (Umbenennung/Umnumerierung ohne Namensänderung) |
| `(essen)` | 1 | administrativ (Ortsklammer) |
| `(rüttenscheid)` | 1 | administrativ (Ortsklammer) |
| `(tlw.)` | 1 | **informationstragend** (Teilangabe) |

82 von 83 sind damit tatsächlich rein administrativ — das bestätigt exakt die
Einschätzung der Re-Review („82 harmlos"). Nur der eine `(tlw.)`-Fall (00318) trägt
echte Information. Der Ruling erlaubt in diesem Fall ausdrücklich, die
Behalten-Regel auf „(tlw.)"-artige Teil-Zusätze zu beschränken — das wurde
umgesetzt.

**Umsetzung.** Neue Funktion `_ist_teil_zusatz()` in `strassen/stichtag.py`: erkennt
Teil-Indikatoren wie „tlw.", „tiw.", „tIw.", „t!w.", „ttw.", „tlIw." (OCR-Varianten
von „teilweise", tolerant über ein Muster `t[il]{0,3}w|teil`) im Zusatz-Kern (Klammern,
Punkte, Ausrufezeichen und Leerzeichen entfernt). Der „unverändert"-Drop in
`_kandidat_oder_pruefung` greift nur noch, wenn `ehemalig == heutig` **und** weder
`zusatz_ehemalig` noch `zusatz_heutig` ein Teil-Indikator ist. Trifft ein
Teil-Indikator zu, bleibt die Zeile in der Konkordanz — mit `ehemalig == heutig`,
gefülltem `zusatz`, und `eindeutig` wie gewohnt über die Kollisions-Logik bestimmt.
Test: `test_baue_konkordanz_behaelt_informationstragenden_teil_zusatz` (Muster
00318).

**Bekannte Grenze:** Das Muster deckt nicht jede denkbare OCR-Variante ab — z. B.
„(tim.)" (w zu m verlesen), die an anderer Stelle im Datensatz vorkommt (aber nicht
unter den hier betroffenen 83), würde nicht erkannt. Im aktuellen Datensatz ist das
folgenlos, da unter den 83 betroffenen Zeilen nur die eine `(tlw.)`-Schreibweise
vorkommt; sollte künftig eine weitere Variante auftreten, würde sie (konservativ,
im Zweifel nicht raten) als administrativ behandelt und die Zeile gedroppt — im
Zweifelsfall also eher zu viel verworfen als zu wenig, was dem precision-first-
Prinzip entspricht (kein Fantasie-Konkordanzeintrag), aber bei einem echten
Informationsverlust erneut auffallen müsste.

### Neue Kennzahlen (Stichtag 1936-06-30, nur `status=automatisch`)

- Konkordanzeinträge gesamt: **393** (vorher 392 nach Fix-Runde 1, +1 durch den
  00318-Fall; ursprünglich 576)
- davon `eindeutig=ja`: 356 / `eindeutig=nein`: 37
- davon mit nicht-leerem `zusatz`: 131
- davon mit `ehemalig == heutig` (Teil-Zusatz-Fälle): **1** (00318)
- Prüffälle (`daten/pruefung_konkordanz.csv`): weiterhin 101 (unverändert — Fix-Runde 2
  betrifft nur den „unverändert"-Drop, nicht Ruling C)
- Adressbuch-Matchquote der bereinigten `ehemalig`-Namen: 333/393 (84,7 %) literal,
  357/393 (90,8 %) mit `_norm_strasse` — praktisch unverändert gegenüber Fix-Runde 1
  (ein einzelner zusätzlicher Eintrag ändert die Quote kaum)

### Stichprobe 00318

`daten/konkordanz_1936.csv` enthält jetzt:
```
Katernberg,Beisenstraße,Beisenstraße,00318,tag,Dickhoff 2015,(tlw.),ja
```
— stadtteil, ehemalig und heutig stimmen mit dem Rohbefund überein
(„Beisenstraße (tlw.)", Katernberg), der Zusatz „(tlw.)" ist erhalten, die Zeile ist
nicht mehr stillschweigend verschwunden.
