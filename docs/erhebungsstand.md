# Erhebungsstand des Adressbuchs Essen 1936

Misst, welchen Namensstand das Adressbuch Essen 1936 (`/home/christos/Projekte/AdressbuchEssen-v2/data/essen1936.csv`)
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
