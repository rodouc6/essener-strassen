# Differenzbericht

| Kategorie | Anzahl |
|---|--:|
| Eintrag neu | 0 |
| Eintrag entfallen | 0 |
| Stadium gewonnen | 159 |
| Stadium verloren | 7 |
| Datum verändert | 8 |
| Name verändert | 34 |
| Kopffeld verändert | 180 |
| Status automatisch → unsicher | 61 |
| Status unsicher → automatisch | 58 |

## Prüfung gegen den Druck (Task 12, Spec 5.1)

Geprüft wurden am OCR-Text (`ocr/seiten/s<buchseite>.txt`) alle 7 Einträge unter
„Stadium verloren", alle 8 unter „Datum verändert", die 6 Einträge unter „Name verändert",
deren neuer Wert kürzer oder inhaltlich anders ist, und alle 58 Statuswechsel
`unsicher → automatisch` — zusammen 79 Einzelbefunde, jeweils als `- Prüfung:`-Zeile unter
dem Listenpunkt.

**Ergebnis:** 73 Befunde bestätigen den neuen Wert (Datumsgewinne, vollständige Namen,
entferntes Randrauschen) oder sind akzeptierte, als `unsicher` gekennzeichnete Verluste.
**6 Befunde sind echte Regressionen** — der Eintrag verliert ein gedrucktes Stadium und ist
dennoch `status=automatisch`, also nicht gekennzeichnet:

| Schl.-Nr. | Lemma | Ursache | Regel |
|---|---|---|---|
| 00595 | Dahlhauser Straße | Doppel-Tagesstempel `10./13. April 1905:` nicht modelliert, Rückfall auf bloßes Jahr → Positionsregel verwirft | 15 |
| 00720 | Eberhardstraße | Spaltenrauschen mitten im Datum (`28. Mai … 1919:`) → Rest-Stempel von Positionsregel verworfen | 15 / Spec 4 („nicht lösbar", soll `unsicher` bleiben) |
| 01386 | Hünninghausenweg | Störpunkt `19. Mai .1926:` → Rückfall auf bloßes Jahr → Positionsregel verwirft | 15 |
| 01638 | Kämmereihude | `kopf._STADIUM` kann `I. Levenhove,` nicht abschließen; Lücke > `_MAX_LUECKE` bricht die Kette; 2 von 3 Stadien fehlen | 4 (+ `_MAX_LUECKE`) |
| 00217 | Am Thyssenhaus | verstümmelte Jahreszahl `19377` → Namen gebendes Stadium fällt aus | Spec 4 („nicht lösbar", soll `unsicher` bleiben) |
| 03560 | An der Schlucht | Bildunterschrift mitten im Datum (`18. … September 1974:`) | Spec 4 („nicht lösbar", soll `unsicher` bleiben) |

Gemeinsames Muster von 00217, 00720, 01152, 03560: Der alte Parser las das Rauschen als
Namensteil und löste dadurch den Prüfgrund „Namensstadium auffällig" aus. Der neue Parser
verwirft das Rauschen sauber — und mit ihm den Prüfgrund. Der Eintrag sieht dann fehlerfrei
aus, obwohl ihm ein gedrucktes Stadium fehlt. Das verletzt das Erfolgskriterium der Spec
(„korrigiert oder gekennzeichnet, nie still falsch") und braucht eine eigene Kennzeichnung,
z. B. einen Prüfgrund, wenn das letzte Stadium nicht zum Lemma passt.

Zwei weitere, kleinere Feldfehler in `automatisch`-Einträgen sind unten kommentiert:
00500 (Namensgruppe endet auf dem verirrten `O` der Tagesziffer) und 02518 (OCR-verstümmelter
Name `Wilhelm- "lieswandt-Allee`, von `_name_auffaellig` nicht erkannt).

## Stadium gewonnen

- 00050 Altendorfer Straße — neu: 1883 Limbecker Chaussee
- 00103 Am Kreuz — neu: 1896-02-13 Georgstraße
- 00103 Am Kreuz — neu: 1915-07-09 Am Kreuz
- 00117 Am Ringofen — neu: 1959-09-08 Am Ringofen
- 00199 Asthöwerstraße — neu: 1957-01-23 Asthöwerstraße
- 00208 Am Kreyenkrop — neu: 1896-10-08 Rohrstraße
- 00217 Am Thyssenhaus — neu: 1961-02-22 Am Rheinstahlhaus
- 00246 Am Roten Haus — neu: 1964-05-20 Am Roten Haus
- 00246 Am Roten Haus — neu: 1970-09-23 Am Roten Haus (Verl) Name einer Flur
- 00254 An den Quellen — neu: 1969-03-19 An den Quellen
- 00299 Berliner Platz — neu: 1964-03-18 Berliner Platz
- 00379 Bocholder Straße — neu: Bocholder Landstraße
- 00400 Borbecker Straße — neu: 1891-04-30 Oberstraße (tlw.)
- 00408 Bottroper Straße — neu: 1868-07-06 Segerothstraße
- 00408 Bottroper Straße — neu: 1891-04-30 Blechstraße
- 00408 Bottroper Straße — neu: 1891-04-30 Phönixstraße
- 00408 Bottroper Straße — neu: 1895-11-28 Bruchstraße
- 00408 Bottroper Straße — neu: 1896-10-08 Franzstraße
- 00408 Bottroper Straße — neu: 1915-07-09 Auf dem Bleek
- 00408 Bottroper Straße — neu: 1915-07-09 Haus-Horl- Straße
- 00408 Bottroper Straße — neu: 1915-07-09 Im Hesselbruch am 29. August 1927 zusammengefasst unter der gemeinsamen Bezeichn
- 00423 Brassertstraße — neu: 1897-09-06 Clementinenstraße
- 00424 Brauerstraße — neu: 1895-01-15 Brauerstraße
- 00471 Berghausbusch — neu: 1974-12-11 Berghausbusch
- 00491 Bungertstraße — neu: 1501 Bungertstraße
- 00500 Kruppsche Buschhauser Straße — neu: 1909-02-05 Buschhauser Straße
- 00565 Bochumer Landstraße — neu: 1890 Chausseestraße
- 00565 Bochumer Landstraße — neu: 1909 Bahnhofstraße
- 00565 Bochumer Landstraße — neu: 1926-05-19 Bochumer Straße {tlw.)
- 00588 Carl-Kruft-Straße — neu: 1896 Edelstraße
- 00623 Dickmannstraße — neu: 1937-11-20 Vesterstraße
- 00674 BDudenstraße — neu: 1501 Schützenbahn
- 00745 Einbleckstraße — neu: 1895-11-28 Einbleckstraße
- 00756 Eligiushöhe — neu: 1932-10-03 Eligiushöhe
- 00817 Eskenshof — neu: 1973-06-13 Eskenshof
- 00864 Flachsmarkt — neu: 1501 Flachsmarkt
- 00866 Flakering - Ehemaliger Hof Flake 1970 Flakering — neu: 1959-09-02 Flakering
- 00928 Fritzstraße — neu: 1896-02-13 Fritzstraße
- 00957 Fischlaker Höfe — neu: 1922-06-02 In den Höfen
- 00957 Fischlaker Höfe — neu: 1970-12-16 Fischlaker Höfe
- 01007 Gemperwiese — neu: 1866 Klein Gümperwiese
- 01011 Gerhard-Küchen-Straße — neu: 1910-12-20 Küchenstraße
- 01013 Gerichtsstraße — neu: 1891-04-30 Gerichtsstraße
- 01019 Gerscheder Straße — neu: 1891-04-30 Gerscheder Straße
- 01026 Gewerbehofstraße — neu: 1957-01-23 Gewerbehofstraße
- 01027 Gewerkenstraße — neu: 1901-07-19 Weststraße
- 01027 Gewerkenstraße — neu: 1915-07-09 Gewerkenstraße
- 01027 Gewerkenstraße — neu: 1939-05-26 Gewerkenstraße (Verl)
- 01037 Gladbecker Straße — neu: 1903-11-27 Unionstraße
- 01037 Gladbecker Straße — neu: 1915-07-09 Koopmannstraße
- 01037 Gladbecker Straße — neu: 1889 Tunnelstraße
- 01037 Gladbecker Straße — neu: 1915-07-09 Feldmannstraße
- 01037 Gladbecker Straße — neu: 1927-08-09 Gladbecker Straße
- 01064 Grafenstraße — neu: 1855-09-07 Grafenstraße
- 01078 Grendgasse — neu: 1890-11-18 Grendgasse
- 01086 Grimbergstraße — neu: 1903-05-11 Grimbergstraße
- 01086 Grimbergstraße — neu: 1959-02-02 Grimbergstraße (Verl) Nach dem ehemaligen fürstlich-essendischen Lehngut Grimber
- 01146 Econova-Allee — neu: 1999-02-24 Econova-Allee. „econova” ist der Name für das über 152 ha große Industrie- und G
- 01150 Haardtstraße — neu: 1895-11-28 Streitweg
- 01150 Haardtstraße — neu: 1896-01-02 Scheidweg
- 01150 Haardtstraße — neu: 1915-07-09 Haardtstraße
- 01152 Hachestraße — neu: 1864-05-06 Am Bahnhof
- 01152 Hachestraße — neu: 1868-01-17 Märkische Straße
- 01186 Hansastraße — neu: 1890-11-18 Markt (tiw.)
- 01189 Hans-Luther-Allee — neu: 1907-05-03 Zweigertstraße (tlw.)
- 01190 Hans-Niemeyer-Straße — neu: 1930-05-31 Hans-Niemeyer-Straße
- 01198 Hartzbeeker Mark — neu: 1914-05-10 Rommesweg (tiw.)
- 01198 Hartzbeeker Mark — neu: 1934-06-05 Hartzbeeker Mark
- 01207 Hattramstraße — neu: 1903-03-12 Hattramstraße
- 01211 Haunerlandweg — neu: 1938-10-21 Haunerlandweg
- 01228 Hedwigstraße — neu: 1897-09-06 Hedwigstraße
- 01228 Hedwigstraße — neu: 1907-02-01 Hedwigstraße (Verl.)
- 01228 Hedwigstraße — neu: 1908-05-01 Hedwigstraße (Verl.)
- 01253 Heinrich-Strunk-Straße — neu: 1902-05-16 Helmholtzstraße
- 01253 Heinrich-Strunk-Straße — neu: 1956-07-03 Heinrich-Strunk-Straße
- 01273 Henglerplatz — neu: 1910 Henglerplatz
- 01301 Hiegemannsgasse — neu: 1919-05-28 Hiegemannsgasse
- 01308 Hindenburgstraße — neu: 1927-10-02 Hindenburgstraße
- 01310 Hinsbecker Berg — neu: 1900-11-06 Bergstraße
- 01310 Hinsbecker Berg — neu: 1934-01-12 Hinsbecker Berg
- 01320 Hobirkheide — neu: 1934-06-05 Hobirkheide
- 01416 Havelring — neu: 1960-09-07 Havelring
- 01492 Im Riek — neu: 1931-02-12 Im Riek
- 01528 Immengarten — neu: 1960-09-07 Immengarten
- 01535 Im Vaeste — neu: 1911-06-16 Im Vaeste
- 01542 Wiesmannskotten — neu: 1999-08-03 Wiesmannskotten
- 01552 An der Blumenwiese — neu: 1999-12-14 An der Blumenwiese
- 01591 Jenckestraße — neu: 1914-10-09 Kruppstraße (tiw.)
- 01591 Jenckestraße — neu: 1969-03-19 Jenckestraße
- 01632 Kallenbergstraße — neu: 1868-01-17 Schlenhofstraße (tlw.)
- 01632 Kallenbergstraße — neu: 1953-03-03 Hilgerstraße (tlw.)
- 01633 Kalthofweg — neu: 1954-02-23 Kalthofweg
- 01635 Kamerunstraße — neu: 1939-05-26 Kamerunstraße
- 01692 Kersthover Höhe — neu: 1952-07-31 Kersthover Höhe
- 01718 ern von der Heiligen Elisabeth zu Essen-(Schuir) Klarastraße — neu: 1897-09-06 Klarastraße
- 01718 ern von der Heiligen Elisabeth zu Essen-(Schuir) Klarastraße — neu: 1933-05-08 Horst- Wessel-Straße (Umb.)
- 01718 ern von der Heiligen Elisabeth zu Essen-(Schuir) Klarastraße — neu: 1945-06-18 Klarastraße (Umb.)
- 01724 Kleine Buschstraße — neu: ! Heißener Straße
- 01845 Kunstwerkerstraße — neu: 1903-02-04 Kunstwerkerstraße
- 01971 Limbecker Straße — neu: 1501 Lyndenbeker Straße
- 01994 Lohmühlental — neu: 1909-03-26 Stricker Straße
- 02016 Lütkenbrauk — neu: 1901-11-02 Kruppstraße
- 02084 Markt — neu: 1501 Markt
- 02110 Meerbruchstraße — neu: 1899 Meerbruchstraße
- 02149 Möllneys Nocken — neu: 1908-04-13 Möllneys Nocken
- 02269 Norbertstraße — neu: 1897-09-06 Nikolausstraße
- 02269 Norbertstraße — neu: 1906-01-26 Nicodemusstraße
- 02269 Norbertstraße — neu: 1906-05-25 Norbertstraße
- 02320 Oberstraße — neu: 1903-01-04 Ludgerusstraße
- 02335 Obere Aue — neu: 1964-05-20 Obere Aue. ze 5 Oberer Schloßhang- Schloss Borbeck ll
- 02356 Overhammshof — neu: 1970-01-21 Overhammshof
- 02449 Poststraße — neu: 1900-11-13 Poststraße
- 02449 Poststraße — neu: 2011-06-28 Poststraße (Verl.)
- 02474 Paul-Goerens-Straße — neu: 1902-05-16 Kruppstraße (tlw.)
- 02515 Bonsiepen — neu: 1989-05-18 Bonsiepen
- 02518 Wilhelm-Nieswandt-Allee — neu: 1990-11-22 Wilhelm- "lieswandt-Allee
- 02532 Hugo-Knippen-Straße — neu: 1991-11-13 Hugo-Knippen-Straße
- 02548 Rahmdörne — neu: 1896-02-13 Markenstraße
- 02548 Rahmdörne — neu: 1915-07-09 Rahmdörne
- 02760 Schichtstraße — neu: 1903-11-27 Steinstraße
- 02760 Schichtstraße — neu: 1915-07-09 1. Schichtstraße
- 02769 Schirnbecker Teiche — neu: Eibergstraße
- 02774 Schlenterstraße — neu: 1927-08-29 Schlenterstraße
- 02803 Schockenhecke — neu: 1903-03-12 Saarbrücker Straße
- 02803 Schockenhecke — neu: 1930-05-31 1. Schockenhecke
- 02804 Schockenhecke — neu: 1903-03-12 Saarbrücker Straße
- 02804 Schockenhecke — neu: 1930-05-31 1. Schockenhecke
- 02845 Schwanhildenstraße — neu: 1899-10-04 Schwanhildenstraße
- 02847 Schwarze Horn — neu: 1915-07-09 II. Hagen (tlw
- 02847 Schwarze Horn — neu: 1957-12-12 Schwarze Horn (Verl.)
- 02934 Steeler Straße — neu: Steeler Chaussee
- 02960 Stiege — neu: 1953-03-03 1. Stiege
- 02961 Stiege — neu: 1953-03-03 II. Stiege
- 03021 Sylviastraße — neu: 1897-09-06 Rosastraße (tiw.)
- 03035 ne eh Schloßstraße - Wasserschloss Borbeck Schliemannstraße — neu: 1894-08-29 Kerckhoffstraße {tlw.)
- 03035 ne eh Schloßstraße - Wasserschloss Borbeck Schliemannstraße — neu: 1929-07-24 Leisers Feld (tlw.)
- 03035 ne eh Schloßstraße - Wasserschloss Borbeck Schliemannstraße — neu: 1973-06-13 Schliemannstraße
- 03067 Thiesstraße — neu: 1896-02-13 Schützenstraße
- 03067 Thiesstraße — neu: 1915-07-09 Thiesstraße
- 03204 Velberter Straße — neu: Ruhrstraße (tlw.)
- 03213 Viehauser Berg — neu: 1501 Viehauser Straße
- 03215 Viehofer Straße — neu: 1501 Veyver Strate
- 03241 Von-Einem-Straße — neu: 1887-09-06 Ottilienstraße
- 03241 Von-Einem-Straße — neu: 1906-01-26 Ortrudstraße
- 03241 Von-Einem-Straße — neu: 1937-11-20 Von-Einem-Straße
- 03249 Voßbusch — neu: ! Voßbuschstraße
- 03277 Hängebank — neu: ) Ernststraße (tlw.)
- 03286 Martin-Vollmar-Straße — neu: ) Graßmannstraße (tiw.)
- 03440 Wüstenhöferstraße — neu: Styrumer Straße
- 03459 Wilhelm-Segerath-Straße — neu: 1976-12-08 Wilhelm- Segerath-Straße
- 03528 Zweigertstraße — neu: 1906-01-26 Felixstraße
- 03528 Zweigertstraße — neu: 1907-05-03 Zweigertstraße
- 03560 An der Schlucht — neu: 1916-02-18 Schacht-Kronprinz-Straße (tiw.)
- 03614 Kettwiger Weinberg — neu: 1977-11-29 Kettwiger Weinberg
- 03631 Beetstraße — neu: 1880 Beetstraße
- 03656 Freiligrathstraße — neu: 1978-04-07 Freiligrathstraße (Verl.)
- 03724 Mendener Straße — neu: 1978-03-14 Mendener Straße
- 03731 Oefte — neu: 0801 Oefte
- 03745 Schillerstraße — neu: 1930-01-28 Schillerstraße

## Stadium verloren

- 00422 Brandstraße — alt: 1826 aufm Brande
  - Prüfung: Verlust akzeptiert: Druck S. 78 'urspr.: (16. Jh.): opme Brand, 1826: aufm Brande, etwa 1860: Brandstraße'; Stadium 1 nimmt jetzt den ganzen Ausdruck '(16. Jh.): opme Brand' auf und verschluckt dabei '1826: aufm Brande'. Eintrag ist `unsicher`.
- 00595 Dahlhauser Straße — alt: 1905-04-13 Schottländerweg
  - Prüfung: REGRESSION: Druck S. 91 '…, 10./13. April 1905: Schottländerweg, 16. April 1925: Dahlhauser Straße.' Der Doppel-Tagesstempel '10./13. April 1905:' ist im Regelkatalog nicht modelliert; erkannt wird nur das bloße Jahr '1905:', das als schwacher Stempel der Positionsregel (Spec Regel 15) unterliegt und mangels Komma davor verworfen wird. Stadium fehlt, Eintrag bleibt `automatisch` — nicht gekennzeichnet.
- 00720 Eberhardstraße — alt: 1919 Horststraße (tiw.)
  - Prüfung: REGRESSION: Druck S. 101 '28. Mai' | Spaltenrauschen 'Tas / Echstenkämperweg - Hof Lohmann' | '1919: Horststraße (tiw.), etwa 1922: Eberhardstraße.' Genau der in Spec Abschnitt 4 als 'nicht durch Regeln lösbar' benannte Fall ('Rauschen mitten im Datum'), der laut Spec `unsicher` bleiben soll. Der Rest-Stempel '1919:' wird von Regel 15 verworfen; mit dem Stadium entfällt auch der bisherige Prüfgrund 'Namensstadium auffällig' — Eintrag jetzt `automatisch`.
- 01386 Hünninghausenweg — alt: 1926 Lindenstraße (Veri.)
  - Prüfung: REGRESSION: Druck S. 170 '19. Mai .1926: Lindenstraße (Veri.)' — Störpunkt vor der Jahreszahl. Der Stempel fällt auf das bloße Jahr '1926:' zurück und wird von der Positionsregel (Regel 15) verworfen. Stadium fehlt, Eintrag bleibt `automatisch`.
- 01638 Kämmereihude — alt: 1915-07-09 I
  - Prüfung: REGRESSION: Druck S. 185 '13. Februar 1896: Ill. Ziegelstraße, 09. Juli 1915: I. Levenhove, 25. Februar 1937: Kämmereihude.' `kopf._STADIUM` kann 'I. Levenhove,' nicht abschließen (nach römischer Zahl ist der Punkt kein Satzende, Regel 4; danach folgt ein Komma statt eines Satzendes), das Stadium fällt aus der Kette, und die Lücke bis zum nächsten Stempel überschreitet `_MAX_LUECKE` (42 > 40). `kopf.rest` endet deshalb nach 'Ill.'.
- 01638 Kämmereihude — alt: 1937-02-25 Kämmereihude
  - Prüfung: REGRESSION (gleiche Ursache): auch das Namen gebende Stadium '25. Februar 1937: Kämmereihude' fehlt. Der Eintrag hat nur noch ein einziges Stadium mit dem Rauschnamen 'Ill' — und ist dennoch `automatisch`.
- 02632 Rosastraße — alt: 1945-06-18 Rosastraße (Umb.)
  - Prüfung: Verlust akzeptiert: Druck S. 278 '01. Februar 1907 Rosastraße (Verl. Bis Rüttenscheider Straße), 29. August 1927: Kirdorfstraße (Umb.), 18. Juni 1945: Rosastraße (Umb.).' Der Punkt in '(Verl.' vor großgeschriebenem 'Bis' gilt als Satzende (Regel 4), `kopf.rest` endet dort. Eintrag ist `unsicher` (Hinweis 'Datum ohne Doppelpunkt').

## Datum verändert

- 00077 Am Freistein — stadium: 2; alt: 1892 (jahr); neu: 1892-03-29 (tag)
  - Prüfung: korrekt: Druck S. 34 '29, März 1892: Feldstraße' — Komma nach dem Tag (Regel 14), jetzt tagesgenau statt bloßes Jahr.
- 00192 Jacob-Grimm-Straße — stadium: 1; alt: 1907 (jahr); neu: 1907-09-27 (tag)
  - Prüfung: korrekt: Druck S. 181 '27. September / 1907: Arndtstraße' (Zeilenumbruch im Datum), jetzt tagesgenau.
- 00608 Deilbachufer — stadium: 1; alt: 1900 (jahr); neu: 1900-11-13 (tag)
  - Prüfung: korrekt: Druck S. 92 '13. Novemner 1900: Uferstraße' — Monatsname mit einem OCR-Fehler (Regel 16), jetzt tagesgenau.
- 01316 Hirtsieferstraße — stadium: 1; alt: 1920 (jahr); neu: 1920-10-01 (tag)
  - Prüfung: korrekt: Druck S. 161 '… Stadtverordneter 01. Oktober 1920: Mercatorstraße' — Stempel ohne Komma davor (Regel 15), jetzt tagesgenau.
- 02632 Rosastraße — stadium: 2; alt: 1927-08-29 (tag); neu: 1907-02-01 (tag)
  - Prüfung: kein Datumsfehler, sondern Folge des oben belegten Kettenabbruchs: Stadium 2 ist jetzt '01. Februar 1907 Rosastraße (Verl' (Druck S. 278) statt des früheren '29. August 1927: Kirdorfstraße (Umb.)'. Der neue Wert steht so im Druck; Eintrag ist `unsicher`.
- 02926 Stankeitstraße — stadium: 1; alt: 1903 (jahr); neu: 1903-11-27 (tag)
  - Prüfung: korrekt: Druck S. 310 'Bürgermeisten 27. November / 1903: Moltkestraße', jetzt tagesgenau.
- 03333 Wehnertweg — stadium: 2; alt: 1910 (jahr); neu: 1910-09-16 (tag)
  - Prüfung: korrekt: Druck S. 342 '16, September 1910: Altenhof II (tiw.)' — Komma nach dem Tag (Regel 14), jetzt tagesgenau.
- 03417 Wisthoffweg — stadium: 1; alt: 1897 (jahr); neu: 1897-11-29 (tag)
  - Prüfung: korrekt: Druck S. 351/352 '29. November' | Seitenumbruch | '1897: Höhenstraße (tlw.)' — Randrauschen entfernt (Regel 12), jetzt tagesgenau.

## Name verändert

Von den 34 Änderungen sind 28 reine Verlängerungen eines zuvor am Abkürzungs- oder
Ziffernpunkt abgeschnittenen Namens ('An St' → 'An St. Hedwig', 'I' → 'I. Weberstraße',
'Platz des 21' → 'Platz des 21. März'; Spec Regeln 1, 2, 4). Sie sind gegen den Druck
stichprobenweise über die zugehörigen Statuswechsel unten mitgeprüft und werden hier nicht
einzeln kommentiert. Einzeln geprüft sind die sechs Fälle, in denen der neue Name kürzer
oder inhaltlich anders ist.

- 00171 Albertus Magnus — stadium: 1; alt: An St; neu: An St. Albertus Magnus
- 00172 Hedwig — stadium: 1; alt: An St; neu: An St. Hedwig
- 00173 Ignatius — stadium: 2; alt: An St; neu: An St. Ignatius
- 00174 Immakulata — stadium: 1; alt: An St; neu: An St. Immakulata
- 00175 Marien — stadium: 2; alt: An St; neu: An St. Marien
- 00176 Quintin — stadium: 1; alt: An St; neu: An St. Quintin
- 00177 Stephan — stadium: 1; alt: An St; neu: An St. Stephan
- 00178 Thomas — stadium: 1; alt: An St; neu: An St. Thomas
- 00258 Am Fernmeldeamt — stadium: 1; alt: Am Fern- A ee meldeamt; neu: Am Fern- meldeamt
  - Prüfung: korrekt: Druck S. 33/34 '21. Januar 1970: Am Fern-' | Seitenzahl | 'meldeamt'; das Randrauschen 'A ee' ist jetzt entfernt (Regel 12).
- 00422 Brandstraße — stadium: 1; alt: (16; neu: (16. Jh.): opme Brand
- 00502 Buschlandweg — stadium: 1; alt: I; neu: I. Buschlandweg
- 00613 Dellbrügge — stadium: 1; alt: 1; neu: 1. Dellbrügge
- 00872 Fließstraße — stadium: 2; alt: I; neu: I. Fließstraße
- 01015 Gerlingplatz — stadium: 3; alt: Platz des 21; neu: Platz des 21. März
- 01022 Gerswidastraße — stadium: 1; alt: II; neu: II. Weberstraße
- 01161 Hagen — stadium: 1; alt: I; neu: I. Hagenstraße
- 01161 Hagen — stadium: 2; alt: I; neu: I. Hagen
- 01162 Hagen — stadium: 2; alt: II; neu: II. Hagen
- 01163 Hagen — stadium: 2; alt: II; neu: II. Hagen
- 01258 Heisterholz — stadium: 4; alt: Heisterholz EEE EEE (Verl); neu: Heisterholz (Verl)
  - Prüfung: korrekt: Druck S. 152/153; das Randrauschen 'EEE EEE' zwischen Name und Zusatz ist jetzt entfernt (Regel 12).
- 01322 Hochstraße — stadium: 1; alt: IV; neu: IV. Rottstraße
- 01760 Köllmannstraße — stadium: 1; alt: «77 l l N Zn J Ne | FH E> £ \ SI 1-17 ueN N EIER K/ 13 nun N ASZo.L Köllmannstra; neu: «77 N Zn J Ne | FH E> £ \ SI 1-17 ueN N EIER K/ 13 nun N ASZo.L Köllmannstraße
  - Prüfung: korrekt: Druck S. 202 'vor 1911:' gefolgt von großflächigem Bildrauschen; die reinen Rauschzeilen 'l' / 'l' sind entfernt (Regel 12) und der Name endet vollständig auf 'Köllmannstraße'. Eintrag bleibt `unsicher`.
- 02262 Nobermanns Hude — stadium: 1; alt: I; neu: I. Ziegelstraße
- 02632 Rosastraße — stadium: 2; alt: Kirdorfstraße (Umb.); neu: Rosastraße (Verl
  - Prüfung: s. o. unter 'Datum verändert': Folge des Kettenabbruchs an '(Verl. Bis'; der neue Wert steht im Druck, Eintrag ist `unsicher`.
- 02668 Ruschenfeld — stadium: 1; alt: I; neu: I. Ruschenfeld
- 02727 Annental — stadium: 3; alt: St; neu: St. Annental
- 02761 Schichtstraße — stadium: 2; alt: I; neu: I. Schichtstraße
- 02796 Schnieringstraße — stadium: 2; alt: 1; neu: 1. Schnieringstraße
- 02796 Schnieringstraße — stadium: 3; alt: I; neu: I. Schnieringstraße (Verl.)
- 03105 Terwestenweg — stadium: 1; alt: I; neu: I. Terwestenweg
- 03324 Weberstraße — stadium: 1; alt: I; neu: I. Weberstraße
- 03328 Weg am Berge — stadium: 2; alt: Weg am EP Berge; neu: Weg am Berge
  - Prüfung: korrekt: Druck S. 341/342 '20. November 1937: Weg am' | Seitenzahl | 'Berge'; das Randrauschen 'EP' ist entfernt (Regel 12).
- 03370 Westfalenstraße — stadium: 1; alt: Bredeneyer w Straße; neu: Bredeneyer Straße
  - Prüfung: korrekt: Druck S. 345/346 '18. November 1890: Bredeneyer' | Seitenzahl | 'Straße'; das Randrauschen 'w' ist entfernt (Regel 12).
- 03625 An der Seilerei — stadium: 1; alt: Kaiser-Wilhelm-Platz und 21; neu: Kaiser-Wilhelm-Platz und 21. Dezember 1899: Thalstraße

## Kopffeld verändert

- 00015 Adolfstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00042 Aloisstraße — feld: namensgruppe; alt: Männlicher Vorname, 02; neu: Männlicher Vorname
- 00050 Altendorfer Straße — feld: namensgruppe; alt: Lagebezeichnung, 1883: Limbecker Chaussee; neu: Lagebezeichnung
- 00062 Am Bonnenberg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00117 Am Ringofen — feld: namensgruppe; alt: Lagebezeichnung, 08, September 1959: Am Ringofen; neu: Lagebezeichnung
- 00137 Am Turm — feld: strassenklasse; alt: Ge-meindestraße; neu: Gemeindestraße
- 00150 An den Friedhöfen — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00170 Am Gemeindebusch — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00171 Albertus Magnus — feld: lemma; alt: Albertus Magnus; neu: An St. Albertus Magnus
- 00172 Hedwig — feld: lemma; alt: Hedwig; neu: An St. Hedwig
- 00173 Ignatius — feld: lemma; alt: Ignatius; neu: An St. Ignatius
- 00174 Immakulata — feld: lemma; alt: Immakulata; neu: An St. Immakulata
- 00175 Marien — feld: lemma; alt: Marien; neu: An St. Marien
- 00176 Quintin — feld: lemma; alt: Quintin; neu: An St. Quintin
- 00177 Stephan — feld: lemma; alt: Stephan; neu: An St. Stephan
- 00178 Thomas — feld: lemma; alt: Thomas; neu: An St. Thomas
- 00192 Jacob-Grimm-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Literaturwissenschaftlen 27; neu: Person, Mann, Deutscher, Literaturwissenschaftlen
- 00208 Am Kreyenkrop — feld: namensgruppe; alt: Flurname, 08.10.1896: Rohrstraße; neu: Flurname
- 00210 Auf der Bredde — feld: strassenklasse; alt: Gemeindstraße; neu: Gemeindestraße
- 00211 Auf der Bucht — feld: stadtteile; alt: ; neu: Heisingen
- 00220 Auf der Knappe — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00254 An den Quellen — feld: namensgruppe; alt: Gewässer, 19, März 1969: An den Quellen; neu: Gewässer
- 00265 Amselweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00268 AmWasserturm — feld: stadtteile; alt: ; neu: Burgaltendorf
- 00347 ME Bertramstraße — feld: lemma; alt: ME Bertramstraße; neu: Bertramstraße
- 00355 KL Bewerungestraße — feld: lemma; alt: KL Bewerungestraße; neu: Bewerungestraße
- 00379 Bocholder Straße — feld: namensgruppe; alt: Bauerschaft, urspr; neu: Bauerschaft
- 00400 Borbecker Straße — feld: namensgruppe; alt: Essener Geschichte und Örtlichkeit, Hofname, 30; neu: Essener Geschichte und Örtlichkeit, Hofname
- 00421 Brandstorstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00423 Brassertstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Jurist, 06, September 1897: Clementinenstraße; neu: Person, Mann, Deutscher, Jurist
- 00471 Berghausbusch — feld: namensgruppe; alt: Familienname, 11; neu: Familienname
- 00481 Bürgerstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00491 Bungertstraße — feld: namensgruppe; alt: Lagebezeichnung, 16; neu: Lagebezeichnung
- 00500 Kruppsche Buschhauser Straße — feld: namensgruppe; alt: Stadt und Ort, O5; neu: Stadt und Ort, O
- 00540 c Cäcilienstraße — feld: lemma; alt: c Cäcilienstraße; neu: Cäcilienstraße
- 00540 c Cäcilienstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00546 Cäsarstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00551 Colsmanstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00565 Bochumer Landstraße — feld: namensgruppe; alt: Lagebezeichnung, 1890: Chausseestraße, 1909: Bahnhofstraße; neu: Lagebezeichnung
- 00588 Carl-Kruft-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Bürgermeister, 1896: Edelstraße; neu: Person, Mann, Deutscher, Bürgermeister
- 00590 Dachsfeld — feld: stadtteile; alt: Dellwig; Str:-Kl.: Gemeindestraße; neu: Dellwig
- 00590 Dachsfeld — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00608 Deilbachufer — feld: namensgruppe; alt: Lagebezeichnung, 13; neu: Lagebezeichnung
- 00628 Diergardtstraße — feld: strassenklasse; alt: Gemeinde-straße; neu: Gemeindestraße
- 00674 BDudenstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Abt, Historiker, 16; neu: Person, Mann, Deutscher, Abt, Historiker
- 00685 Dudweilerstraße — feld: namensgruppe; alt: Stadt und Ort, 14; neu: Stadt und Ort
- 00701 ra Unterm Sternenzelt — feld: lemma; alt: ra Unterm Sternenzelt; neu: Unterm Sternenzelt
- 00720 Eberhardstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Bergmann, Männlicher Vorname, 28; neu: Person, Mann, Deutscher, Bergmann, Männlicher Vorname
- 00733 Eibergweg — feld: stadtteile; alt: Freisenbruch; Gemeindestraße; neu: Freisenbruch
- 00733 Eibergweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00745 Einbleckstraße — feld: namensgruppe; alt: Flurname, 28; neu: Flurname
- 00756 Eligiushöhe — feld: namensgruppe; alt: Person, Mann, Deutscher, Bischof, Heiliger, *03; neu: Person, Mann, Deutscher, Bischof, Heiliger
- 00778 Engelbertstraße — feld: strassenklasse; alt: ; neu: Kreisstraße
- 00817 Eskenshof — feld: namensgruppe; alt: Hofname, 13, Juni 1973: Eskenshof; neu: Hofname
- 00864 Flachsmarkt — feld: namensgruppe; alt: Essener Geschichte und Örtlichkeit, Platz, 16; neu: Essener Geschichte und Örtlichkeit, Platz
- 00866 Flakering - Ehemaliger Hof Flake 1970 Flakering — feld: namensgruppe; alt: Hofname, 02; neu: Hofname
- 00905 Freisenbruchstraße — feld: stadtteile; alt: Freisenbruch; Steele; Gemeindestraße; neu: Freisenbruch; Steele
- 00905 Freisenbruchstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00915 Friedrich-Ebert-Straße — feld: strassenklasse; alt: ; neu: Landstraße
- 00939 Fürstäbtissinstraße — feld: stadtteile; alt: Borbeck- Mitte; Gemeindestraße; neu: Borbeck- Mitte
- 00939 Fürstäbtissinstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00940 Fürstenbergstraße — feld: stadtteile; alt: Borbeck-Mitte; Gemeindestraße; neu: Borbeck-Mitte
- 00940 Fürstenbergstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00941 Fürstinstraße — feld: stadtteile; alt: Steele; Gemeindestraße; neu: Steele
- 00941 Fürstinstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00942 Fuldastraße — feld: stadtteile; alt: Bergerhausen; Gemeindestraße; neu: Bergerhausen
- 00942 Fuldastraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 00999 Geilinghausweg — feld: stadtteile; alt: ; neu: Heidhausen
- 01011 Gerhard-Küchen-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Industrieller, Siedlung, 20; neu: Person, Mann, Deutscher, Industrieller, Siedlung
- 01019 Gerscheder Straße — feld: namensgruppe; alt: Bauerschaft, 30, April 1891: Gerscheder Straße; neu: Bauerschaft
- 01026 Gewerbehofstraße — feld: namensgruppe; alt: Lagebezeichnung, 23, Januar 1957: Gewerbehofstraße; neu: Lagebezeichnung
- 01046 Gneisenaustraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01073 Graudenzstraße — feld: namensgruppe; alt: Stadt und Ort, 085; neu: Stadt und Ort
- 01078 Grendgasse — feld: namensgruppe; alt: Gewässer, 18, November 1890: Grendgasse; neu: Gewässer
- 01104 Grundstraße — feld: namensgruppe; alt: Lagebezeichnung, 29; neu: Lagebezeichnung
- 01152 Hachestraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01189 Hans-Luther-Allee — feld: namensgruppe; alt: Person, Mann, Deutscher, Politiker, Oberbürgermeister, Reichskanzler, 03; neu: Person, Mann, Deutscher, Politiker, Oberbürgermeister, Reichskanzler
- 01190 Hans-Niemeyer-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Rechtsanwalt, Notar, Justizrat, 31; neu: Person, Mann, Deutscher, Rechtsanwalt, Notar, Justizrat
- 01207 Hattramstraße — feld: namensgruppe; alt: Flurname, 12.03.1903: Hattramstraße; neu: Flurname
- 01211 Haunerlandweg — feld: namensgruppe; alt: Kotten, 21, Oktober 1938: Haunerlandweg; neu: Kotten
- 01247 Heimstättenweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01273 Henglerplatz — feld: namensgruppe; alt: Person, Mann, Deutscher, Stadtverordneter, Platz, etwa 1910/11: Henglerplatz; neu: Person, Mann, Deutscher, Stadtverordneter, Platz
- 01301 Hiegemannsgasse — feld: namensgruppe; alt: Familienname, 28; neu: Familienname
- 01316 Hirtsieferstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Politiker, Stadtverordneter 01; neu: Person, Mann, Deutscher, Politiker, Stadtverordneter
- 01320 Hobirkheide — feld: namensgruppe; alt: Hofname, 05; neu: Hofname
- 01333 Höntroper Straße — feld: stadtteile; alt: Horst; Gemeindestraße; neu: Horst
- 01333 Höntroper Straße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01382 Hülsebergstraße — feld: stadtteile; alt: Horst; Gemeindestraße; neu: Horst
- 01382 Hülsebergstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01392 Hufeisen — feld: namensgruppe; alt: Lagebezeichnung, 14; neu: Lagebezeichnung
- 01414 Hinseler Feld — feld: stadtteile; alt: ; neu: Überruhr- Hinsel
- 01416 Havelring — feld: namensgruppe; alt: Gewässer, 07; neu: Gewässer
- 01453 Imandtstraße — feld: stadtteile; alt: Horst; Gemeindestraße; neu: Horst
- 01453 Imandtstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01474 Höfe und ihre Aufsitzer die Schreibweise mit „v“ Im Hülsfeld — feld: namensgruppe; alt: Flurname, 10; neu: Flurname
- 01492 Im Riek — feld: namensgruppe; alt: Flurname, 12, Februar 1931: Im Riek; neu: Flurname
- 01521 Irmastraße — feld: stadtteile; alt: Horst; Gemeindestraße; neu: Horst
- 01521 Irmastraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01528 Immengarten — feld: namensgruppe; alt: Zoologie, 07; neu: Zoologie
- 01533 Im Schlagholz — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01542 Wiesmannskotten — feld: namensgruppe; alt: Kotten, 03, August 1999: Wiesmannskotten; neu: Kotten
- 01552 An der Blumenwiese — feld: namensgruppe; alt: Lagebezeichnung, PER B BEN: * ai 14; neu: Lagebezeichnung, PER B BEN: * ai
- 01563 Jahnplatz — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01581 Joseph-Schüller-Platz — feld: stadtteile; alt: ; neu: Katernberg
- 01591 Jenckestraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01601 y u Prager Straße — feld: lemma; alt: y u Prager Straße; neu: Prager Straße
- 01601 y u Prager Straße — feld: buchseite; alt: 264; neu: 265
- 01614 Am Bruchweiher — feld: stadtteile; alt: Stoppenberg im Bereich der Flur „Im Westerbruch" (Bruch = mooriger Grund; Boden); neu: Stoppenberg
- 01615 Am Stoppenberger Bach — feld: stadtteile; alt: ; neu: Stoppenberg
- 01632 Kallenbergstraße — feld: namensgruppe; alt: Familienname, 17; neu: Familienname
- 01633 Kalthofweg — feld: namensgruppe; alt: Kotten, 23, Februar 1954: Kalthofweg; neu: Kotten
- 01634 Kamblickweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 01724 Kleine Buschstraße — feld: namensgruppe; alt: Flurname, urspr.! Heißener Straße; neu: Flurname
- 01731 Kleiner Bruch — feld: namensgruppe; alt: EBD Bi Fa Sat ne Fa Kleiner Markt Flurname; neu: ne Fa Kleiner Markt Flurname
- 01845 Kunstwerkerstraße — feld: namensgruppe; alt: Lagebezeichnung, 04; neu: Lagebezeichnung
- 01863 Kleiner Schirnkamp — feld: strassenklasse; alt: Gemeindstraße; neu: Gemeindestraße
- 01896 Landsberghof — feld: stadtteile; alt: ; neu: Frillendorf
- 01971 Limbecker Straße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, im 16; neu: Essener Geschichte und Ortlichkeit
- 01981 Lippermannweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 02016 Lütkenbrauk — feld: namensgruppe; alt: Flurname, 02.11.1901: Kruppstraße; neu: Flurname
- 02035 Pa Leipoldtstraße — feld: lemma; alt: Pa Leipoldtstraße; neu: Leipoldtstraße
- 02084 Markt — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, 16; neu: Essener Geschichte und Ortlichkeit
- 02110 Meerbruchstraße — feld: namensgruppe; alt: Gemeinheit, etwa a tt 1899: Meerbruchstraße; neu: Gemeinheit
- 02149 Möllneys Nocken — feld: namensgruppe; alt: Flurname, 13; neu: Flurname
- 02171 Müllerstraße — feld: strassenklasse; alt: Gemeindstraße; neu: Gemeindestraße
- 02191 Manderscheidtstraße — feld: stadtteile; alt: ; neu: Frillendorf; Stoppenberg
- 02224 Narzissenweg — feld: namensgruppe; alt: Botanik, 05; neu: Botanik
- 02279 Nottekampswinkel — feld: strassenklasse; alt: Gemeondestraße; neu: Gemeindestraße
- 02317 Obernitzstraße — feld: strassenklasse; alt: Gemeindestraße; Str.- ir Sa E; neu: Gemeindestraße; Str.- Sa E
- 02335 Obere Aue — feld: stadtteile; alt: ; neu: Heisingen
- 02355 Ostuferstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 02356 Overhammshof — feld: namensgruppe; alt: Hofname, 21; neu: Hofname
- 02393 Paul-Brandi-Straße — feld: namensgruppe; alt: r Me Kosu Pauline - Zeche Pauline Person, Mann, Deutscher, Bankdirektor, Beigeordneter; neu: Kosu Pauline - Zeche Pauline Person, Mann, Deutscher, Bankdirektor, Beigeordneter
- 02429 Planckstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 02474 Paul-Goerens-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Metallograph, Ingenieur, 16; neu: Person, Mann, Deutscher, Metallograph, Ingenieur
- 02505 Diestweg — feld: stadtteile; alt: ; neu: Bochold
- 02508 Schacht Neu-Cöln — feld: strassenklasse; alt: Gemeinde-straße; neu: Gemeindestraße
- 02515 Bonsiepen — feld: namensgruppe; alt: Hofname, 18; neu: Hofname
- 02542 Rademachers Weg — feld: stadtteile; alt: Freisenbruch; Horst; Gemeindestraße; neu: Freisenbruch; Horst
- 02542 Rademachers Weg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 02600 Riehlstraße — feld: strassenklasse; alt: Gemeindstraße; neu: Gemeindestraße
- 02641 Rubensstraße — feld: strassenklasse; alt: ; neu: Hauptstraße
- 02727 Annental — feld: lemma; alt: Annental; neu: St. Annental
- 02769 Schirnbecker Teiche — feld: namensgruppe; alt: Gewässer, urspr; neu: Gewässer
- 02770 Schlackenstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 02774 Schlenterstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Pfarrer, 29.08.1927: Schlenterstraße; neu: Person, Mann, Deutscher, Pfarrer
- 02812 Schönscheidts Hof — feld: stadtteile; alt: ; neu: Kray
- 02845 Schwanhildenstraße — feld: namensgruppe; alt: Person, Frau, Äbtissin, 04; neu: Person, Frau, Äbtissin
- 02874 In der Nähe der Arminiusgarten! Sigsfeldstraße — feld: stadtteile; alt: ; neu: Nordviertel
- 02926 Stankeitstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Bürgermeisten 27; neu: Person, Mann, Deutscher, Bürgermeisten
- 02934 Steeler Straße — feld: namensgruppe; alt: Stadt und Ort, urspr; neu: Stadt und Ort
- 02949 Spervogelweg — feld: namensgruppe; alt: Person, Mann, Deutschen, Minnesängerr 27; neu: Person, Mann, Deutschen, Minnesängerr
- 02961 Stiege — feld: namensgruppe; alt: Lagebezeichnung, 03; neu: Lagebezeichnung
- 03021 Sylviastraße — feld: namensgruppe; alt: Weiblicher Vorname, 06, September 1897: Rosastraße (tiw.); neu: Weiblicher Vorname
- 03057 Tersteegenweg — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 03203 Velberter Sträßchen — feld: namensgruppe; alt: Stadt und Ort, urspr; neu: Stadt und Ort
- 03204 Velberter Straße — feld: namensgruppe; alt: Stadt und Ort, urspr; neu: Stadt und Ort
- 03213 Viehauser Berg — feld: namensgruppe; alt: Hofname, 16; neu: Hofname
- 03215 Viehofer Straße — feld: namensgruppe; alt: Essener Geschichte und Örtlichkeit, 16; neu: Essener Geschichte und Örtlichkeit
- 03227 Vittinghoffstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 03249 Voßbusch — feld: namensgruppe; alt: Flurname, urspr.! Voßbuschstraße; neu: Flurname
- 03277 Hängebank — feld: namensgruppe; alt: Lagebezeichnung, (urspr.) Ernststraße (tlw.); neu: Lagebezeichnung, (
- 03286 Martin-Vollmar-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Pfarrer, (urspr.) Graßmannstraße (tiw.); neu: Person, Mann, Deutscher, Pfarrer, (
- 03307 Walkürenweg — feld: strassenklasse; alt: Walkmühle —— 2 | 20; neu: Walkmühle —— 2 | 20. November 1937: Walkürenweg
- 03379 Wiedbach — feld: stadtteile; alt: Bedingrade; Gerschede; Gemeindestraße; neu: Bedingrade; Gerschede
- 03379 Wiedbach — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 03388 w WiesenbergstraßBe — feld: lemma; alt: w WiesenbergstraßBe; neu: WiesenbergstraßBe
- 03417 Wisthoffweg — feld: namensgruppe; alt: Hofname, 29; neu: Hofname
- 03425 Woermannstraße — feld: strassenklasse; alt: Gemeindstraße; neu: Gemeindestraße
- 03440 Wüstenhöferstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Generaldirektor, Industrieller, urspr; neu: Person, Mann, Deutscher, Generaldirektor, Industrieller
- 03444 Walter-Hohmann-Straße — feld: namensgruppe; alt: Person, ae w Mann, Deutscher, Stadtbaurat, Ingenieur; neu: Person, Mann, Deutscher, Stadtbaurat, Ingenieur
- 03459 Wilhelm-Segerath-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Geistlicher, 08; neu: Person, Mann, Deutscher, Geistlicher
- 03499 Zementstraße — feld: stadtteile; alt: Kupferdreh; Gemeindestraße; neu: Kupferdreh
- 03499 Zementstraße — feld: strassenklasse; alt: ; neu: Gemeindestraße
- 03553 u A NS Auf'm Stöcken — feld: lemma; alt: u A NS Auf'm Stöcken; neu: Auf'm Stöcken
- 03553 u A NS Auf'm Stöcken — feld: buchseite; alt: 58; neu: 59
- 03611 I El nl EEE EEE ER 4 4 bi Am Stadtwald — feld: lemma; alt: I El nl EEE EEE ER 4 4 bi Am Stadtwald; neu: EEE EEE ER 4 4 bi Am Stadtwald
- 03631 Beetstraße — feld: namensgruppe; alt: Flurname, vor 1880, Beetstraße; neu: Flurname
- 03731 Oefte — feld: namensgruppe; alt: Nummerierungsbezirk, 9; neu: Nummerierungsbezirk
- 03745 Schillerstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Dichter, Philosoph, Historiker 28; neu: Person, Mann, Deutscher, Dichter, Philosoph, Historiker

## Status automatisch → unsicher

- 00077 Am Freistein
- 00137 Am Turm
- 00210 Auf der Bredde
- 00269 An der Windmühle
- 00357 Bieberweg
- 00379 Bocholder Straße
- 00400 Borbecker Straße
- 00417 Brandenburger Straße
- 00422 Brandstraße
- 00467 Brunnsiepen
- 00608 Deilbachufer
- 00623 Dickmannstraße
- 00628 Diergardtstraße
- 00733 Eibergweg
- 00905 Freisenbruchstraße
- 00939 Fürstäbtissinstraße
- 00940 Fürstenbergstraße
- 00941 Fürstinstraße
- 00942 Fuldastraße
- 01011 Gerhard-Küchen-Straße
- 01037 Gladbecker Straße
- 01157 Hafenstraße
- 01168 Hagmanngarten
- 01186 Hansastraße
- 01189 Hans-Luther-Allee
- 01214 Haus-Berge-Straße
- 01308 Hindenburgstraße
- 01333 Höntroper Straße
- 01382 Hülsebergstraße
- 01401 Hundebrinkstraße
- 01453 Imandtstraße
- 01521 Irmastraße
- 01632 Kallenbergstraße
- 01672 Kastellgraben
- 01834 Külshammerweg
- 01863 Kleiner Schirnkamp
- 01994 Lohmühlental
- 02171 Müllerstraße
- 02182 Mönkhoffs Busch
- 02279 Nottekampswinkel
- 02320 Oberstraße
- 02474 Paul-Goerens-Straße
- 02508 Schacht Neu-Cöln
- 02542 Rademachers Weg
- 02600 Riehlstraße
- 02632 Rosastraße
- 02769 Schirnbecker Teiche
- 02934 Steeler Straße
- 03012 Spielkampshof
- 03204 Velberter Straße
- 03277 Hängebank
- 03286 Martin-Vollmar-Straße
- 03333 Wehnertweg
- 03379 Wiedbach
- 03425 Woermannstraße
- 03440 Wüstenhöferstraße
- 03496 BET un 2 Zehntfeld
- 03499 Zementstraße
- 03614 Kettwiger Weinberg
- 03625 An der Seilerei
- 03656 Freiligrathstraße

## Status unsicher → automatisch

- 00050 Altendorfer Straße
  - Prüfung: korrekt: S. 30, Kette vollständig ('1883: Limbecker Chaussee' … '19. Oktober 1950: Altendorfer Straße (Verl)'); das bisher fehlende Anfangsstadium ist jetzt erfasst.
- 00103 Am Kreuz
  - Prüfung: korrekt: S. 38, Kette '13. Februar 1896: Georgstraße, 09. Juli 1915: Am Kreuz' jetzt vollständig erfasst (vorher keine Kette).
- 00199 Asthöwerstraße
  - Prüfung: korrekt: S. 56, '23. Januar 1957: Asthöwerstraße' — Kette jetzt erkannt.
- 00208 Am Kreyenkrop
  - Prüfung: korrekt: S. 39, numerisches Datum '08.10.1896:' (Regel 7) jetzt erkannt; Kette vollständig.
- 00217 Am Thyssenhaus
  - Prüfung: REGRESSION: S. 44, Druck '22. Februar 1961: Am Rheinstahlhaus, 04. Februar 19377: Am Thyssenhaus.' Die verstümmelte Jahreszahl '19377' (in Spec Abschnitt 4 ausdrücklich als `unsicher` zu belassen genannt) lässt das Namen gebende Stadium ausfallen; der Eintrag ist trotzdem `automatisch`.
- 00246 Am Roten Haus
  - Prüfung: korrekt: S. 42, Kette vollständig; Stadium 2 zieht den anschließenden Erläuterungsanfang mit ('(Verl) Name einer Flur'), weil im Druck der Doppelpunkt fehlt — Wert steht so im Text.
- 00299 Berliner Platz
  - Prüfung: korrekt: S. 68, '18. März 1964: Berliner Platz' — Stempel mit Komma statt Doppelpunkt am Namensende, Kette erkannt.
- 00424 Brauerstraße
  - Prüfung: korrekt: S. 78, '15. Januar 1895: Brauerstraße' — Kette erkannt.
- 00491 Bungertstraße
  - Prüfung: korrekt: S. 85, '16. Jahrhundert: Bungertstraße' → Präzision `jahrhundert`, gueltig_ab 1501 (Regel 8).
- 00500 Kruppsche Buschhauser Straße
  - Prüfung: überwiegend korrekt: S. 86, 'O5. Februar 1909: Buschhauser Straße' — Tagesziffer mit OCR-'O' gelesen, Datum richtig. ABER: die Namensgruppe endet auf 'Stadt und Ort, O' (das verirrte 'O' der Tagesziffer) — kleiner Feldfehler in einem `automatisch`-Eintrag.
- 00502 Buschlandweg
  - Prüfung: korrekt: S. 86, '21. Oktober 1938: I. Buschlandweg' — der Punkt nach römisch I beendet den Namen nicht mehr (Regel 4).
- 00540 c Cäcilienstraße
  - Prüfung: korrekt: S. 87, Marker 'Str.-Kl.;' (Semikolon, Regel 9) jetzt erkannt, Straßenklasse gefüllt.
- 00588 Carl-Kruft-Straße
  - Prüfung: korrekt: S. 88, Anfangsstadium '1896: Edelstraße' jetzt erfasst, Kette vollständig.
- 00613 Dellbrügge
  - Prüfung: korrekt: S. 93, 'um 1860: 1. Dellbrügge' — Name vollständig statt nur '1'.
- 00701 ra Unterm Sternenzelt
  - Prüfung: korrekt: S. 330, Kette unverändert; der frühere Prüfgrund (Lemmarauschen 'ra') entfällt durch die Randrauschen-Bereinigung (Regel 12).
- 00756 Eligiushöhe
  - Prüfung: korrekt: S. 106, '*03. Oktober 1932: Eligiushöhe' — OCR-Stern vor der Tagesziffer (Regel 3) jetzt toleriert.
- 00864 Flachsmarkt
  - Prüfung: korrekt: S. 114, '16. Jahrh.: Flachsmarkt' → `jahrhundert`, 1501 (Regel 8).
- 00872 Fließstraße
  - Prüfung: korrekt: S. 115, '09. Juli 1915: I. Fließstraße' — Name vollständig statt nur 'I'.
- 00928 Fritzstraße
  - Prüfung: korrekt: S. 122, '13. Februar 1896: Fritzstraße' — Kette erkannt.
- 00957 Fischlaker Höfe
  - Prüfung: korrekt: S. 114, Kette '02. Juni 1922: In den Höfen, 16. Dezember 1970: Fischlaker Höfe' vollständig.
- 01013 Gerichtsstraße
  - Prüfung: korrekt: S. 126, '30. April 1891: Gerichtsstraße' — Kette erkannt.
- 01022 Gerswidastraße
  - Prüfung: korrekt: S. 127, 'vor 1826: II. Weberstraße' — Name vollständig statt nur 'II'.
- 01027 Gewerkenstraße
  - Prüfung: korrekt: S. 128, Kette vollständig inkl. numerischem Datum '26.05.1939:' (Regel 7).
- 01150 Haardtstraße
  - Prüfung: korrekt: S. 138, Kette dreistufig vollständig erfasst.
- 01152 Hachestraße
  - Prüfung: REGRESSION: S. 138, Druck '06. Mai 1864: Am Bahnhof, 17. Januar 1868: Märkische Straße, 05.' | Bildunterschrift 'FT - Haedenkampstraße - 1916' | 'Juni 1934: Hachestraße.' Das Namen gebende Stadium fällt durch das Rauschen mitten im Datum aus; Eintrag trotzdem `automatisch`. Immerhin korrekt: die zerrissene Schlüsselnummer '011 52' wird jetzt zu 01152 statt 00011 gelesen.
- 01161 Hagen
  - Prüfung: korrekt: S. 140, 'um 1860: I. Hagenstraße, 09. Juli 1915: I. Hagen' — beide Namen vollständig.
- 01207 Hattramstraße
  - Prüfung: korrekt: S. 145, numerisches Datum '12.03.1903: Hattramstraße' (Regel 7) jetzt als eigenes Stadium erfasst.
- 01322 Hochstraße
  - Prüfung: korrekt: S. 162, '18. November 1890: IV. Rottstraße' — Name vollständig statt nur 'IV'.
- 01535 Im Vaeste
  - Prüfung: korrekt: S. 178, '16. Juni 1911: Im Vaeste' — Kette erkannt.
- 01601 y u Prager Straße
  - Prüfung: korrekt: S. 265, Kette unverändert; der frühere Prüfgrund (Lemmarauschen 'y u') entfällt durch die Randrauschen-Bereinigung (Regel 12).
- 01635 Kamerunstraße
  - Prüfung: korrekt: S. 188, '26. Mai 1939: Kamerunstraße' — der Fallback schneidet nicht mehr an der Tagesziffer ab (Regel 1, Goldstandardfall).
- 01638 Kämmereihude
  - Prüfung: REGRESSION: s. o. unter 'Stadium verloren' — von drei gedruckten Stadien bleibt nur 'Ill' übrig, und der Eintrag wechselt dabei von `unsicher` zu `automatisch`. Der schwerste Fall dieses Laufs.
- 01692 Kersthover Höhe
  - Prüfung: korrekt: S. 194, '31. Juli 1952: Kersthover Höhe' — Kette erkannt.
- 02016 Lütkenbrauk
  - Prüfung: korrekt: S. 227, numerisches Datum '02.11.1901: Kruppstraße' (Regel 7) als Stadium 1 ergänzt.
- 02084 Markt
  - Prüfung: korrekt: S. 231, '16. Jahrhundert: Markt' → `jahrhundert`, 1501 (Regel 8).
- 02110 Meerbruchstraße
  - Prüfung: korrekt: S. 234, 'etwa 1899: Meerbruchstraße' — qualifizierter Jahresstempel erkannt.
- 02356 Overhammshof
  - Prüfung: korrekt: S. 254, '21. Januar 1970: Overhammshof' — Kette erkannt (im Druck folgt verstümmeltes Rauschen, das jetzt im Erläuterungstext bleibt, Regel 3).
- 02518 Wilhelm-Nieswandt-Allee
  - Prüfung: Datum korrekt (S. 349, '22. November 1990:'), ABER der Name ist OCR-verstümmelt ('Wilhelm- "lieswandt-Allee' statt 'Wilhelm-Nieswandt-Allee') und die Rauschheuristik `_name_auffaellig` greift nicht — Rauschname in einem `automatisch`-Eintrag.
- 02532 Hugo-Knippen-Straße
  - Prüfung: korrekt: S. 171, '13. November 1991: Hugo-Knippen-Straße'; die undatierte Vorstufe '(vorm.) Bergheimer Straße (tlw.)' steht im Druck ohne Datum und bleibt daher in der Namensgruppe.
- 02548 Rahmdörne
  - Prüfung: korrekt: S. 268, Kette inkl. numerischem Datum '09.07.1915:' (Regel 7) vollständig.
- 02668 Ruschenfeld
  - Prüfung: korrekt: S. 283, '05. Juli 1950: I. Ruschenfeld' — Name vollständig statt nur 'I'.
- 02727 Annental
  - Prüfung: korrekt: S. 309, '18. September 1926: St. Annental' — der Punkt nach 'St' beendet den Namen nicht mehr (Regel 4, Goldstandardfall).
- 02760 Schichtstraße
  - Prüfung: korrekt: S. 289, Kette vollständig, Name '1. Schichtstraße' (im Druck arabische 1 statt römisch I).
- 02761 Schichtstraße
  - Prüfung: korrekt: S. 289, '09. Juli 1915: I. Schichtstraße' — Name vollständig statt nur 'I'.
- 02774 Schlenterstraße
  - Prüfung: korrekt: S. 291, numerisches Datum '29.08.1927: Schlenterstraße' (Regel 7) erkannt.
- 02796 Schnieringstraße
  - Prüfung: korrekt: S. 293, beide Namen vollständig ('1. Schnieringstraße', 'I. Schnieringstraße (Verl.)').
- 02803 Schockenhecke
  - Prüfung: korrekt: S. 294, Kette vollständig, Name '1. Schockenhecke'.
- 02804 Schockenhecke
  - Prüfung: korrekt: S. 294, Kette vollständig, Name '1. Schockenhecke' (Parallel-Eintrag zu 02803).
- 02960 Stiege
  - Prüfung: korrekt: S. 315, '03. März 1953: 1. Stiege' — Name vollständig.
- 03067 Thiesstraße
  - Prüfung: korrekt: S. 323, Kette '13. Februar 1896: Schützenstraße, 09. Juli 1915: Thiesstraße' vollständig.
- 03105 Terwestenweg
  - Prüfung: korrekt: S. 321, '08. Juni 1960: I. Terwestenweg' — Name vollständig statt nur 'I'.
- 03324 Weberstraße
  - Prüfung: korrekt: S. 341, 'vor 1826: I. Weberstraße' — Name vollständig statt nur 'I'.
- 03388 w WiesenbergstraßBe
  - Prüfung: korrekt: S. 348, Kette unverändert; der frühere Prüfgrund (Lemmarauschen 'w …ßBe') entfällt durch die Randrauschen-Bereinigung (Regel 12).
- 03528 Zweigertstraße
  - Prüfung: korrekt: S. 362, Kette '26. Januar 1906: Felixstraße, 03. Mai 1907: Zweigertstraße' vollständig.
- 03553 u A NS Auf'm Stöcken
  - Prüfung: korrekt: S. 59, Kette unverändert; der frühere Prüfgrund (Lemmarauschen 'u A NS') entfällt durch die Randrauschen-Bereinigung (Regel 12).
- 03560 An der Schlucht
  - Prüfung: REGRESSION: S. 50, Druck '18. Februar 1916: Schacht-Kronprinz-Straße (tiw.), 18.' | Bildunterschrift 'L N ee ? An der Seilerei - Seilerei Zimmermann 1879 An der Walkmühle' | 'September 1974: An der Schlucht.' Das Namen gebende Stadium fällt durch das Rauschen mitten im Datum aus; Eintrag trotzdem `automatisch`.
- 03731 Oefte
  - Prüfung: korrekt: S. 251, '9. Jahrh.: Oefte' → `jahrhundert`, gueltig_ab 0801 (Regel 8).
- 03745 Schillerstraße
  - Prüfung: korrekt: S. 290, '… Historiker 28. Januar 1930: Schillerstraße' — Stempel ohne Komma davor (Regel 15), Kette erkannt.
