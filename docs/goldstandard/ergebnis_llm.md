# Goldstandard-Messung der LLM-Leser

Jedes geprüfte Feld der Goldstandard-Stichprobe (Seed 1936, menschlich geprüft) gegen den
Wert des jeweiligen Modells. Der Prompt wurde an anderen Seiten entwickelt und nach dieser
Messung nicht mehr verändert (Spec 2026-09-12, Abschnitt 4).

## Modell `mistral`

Gesamt: 478 Felder, 371 korrekt, Fehlerquote 22.4 %. Vom Parser ausgelassene Felder: 7 von 10 vom Modell gefunden.

| Schicht/Feldtyp | geprüft | korrekt | Fehlerquote |
|---|--:|--:|--:|
| automatisch | 388 | 311 | 19.8 % |
| unsicher | 90 | 60 | 33.3 % |
| lemma | 50 | 42 | 16.0 % |
| namensgruppe | 50 | 38 | 24.0 % |
| schl_nr | 50 | 43 | 14.0 % |
| stadium_datum | 89 | 66 | 25.8 % |
| stadium_name | 89 | 58 | 34.8 % |
| stadtteile | 50 | 40 | 20.0 % |
| strassenklasse | 50 | 43 | 14.0 % |
| verweis_auf | 50 | 41 | 18.0 % |

### Abweichungen

| schl_nr | Lemma | Feld | soll | Modell |
|---|---|---|---|---|
| 00208 | Am Kreyenkrop | namensgruppe | Flurname, 08.10.1896: Rohrstraße | Flurname |
| 00208 | Am Kreyenkrop | stadium_1_datum | 1915-07-09 | 1896-10-08 |
| 00208 | Am Kreyenkrop | stadium_1_name | Bedingrader Straße (tiw.) | Rohrstraße |
| 00208 | Am Kreyenkrop | stadium_2_datum | 1967-05-03 | 1915-07-09 |
| 00208 | Am Kreyenkrop | stadium_2_name | Am Kreyenkrop | Bedingrader Straße (tlw.) |
| 00364 | Breukelmannhang | verweis_auf | Breukelmannhof |  |
| 00507 | Byfanger Straße | stadium_1_name | Oststraße (tiw.) | Oststraße (tlw.) |
| 00507 | Byfanger Straße | stadium_4_name | Byfanger Straße (Verl) | Byfanger Straße (Verl.) |
| 00577 | Hinsbecker Hang | schl_nr | 00577 | — |
| 00577 | Hinsbecker Hang | lemma | Hinsbecker Hang | — |
| 00577 | Hinsbecker Hang | stadtteile | Kupferdreh | — |
| 00577 | Hinsbecker Hang | strassenklasse | Gemeindestraße | — |
| 00577 | Hinsbecker Hang | namensgruppe | Honnschaft | — |
| 00577 | Hinsbecker Hang | verweis_auf | Hinsbecker Berg | — |
| 00577 | Hinsbecker Hang | stadium_1_datum | 1982-01-20 | — |
| 00577 | Hinsbecker Hang | stadium_1_name | Hinsbecker Hang | — |
| 00595 | Dahlhauser Straße | stadium_2_datum | vor 1874 | 1874 |
| 00595 | Dahlhauser Straße | stadium_3_datum | 1905-04-13 | (urspr., kein Datum) |
| 00595 | Dahlhauser Straße | stadium_4_datum | 1925-04-16 | (urspr., kein Datum) |
| 00891 | Franziskanerhöhe | verweis_auf | Franziskanerstraße |  |
| 00891 | Franziskanerhöhe | stadium_2_name | Kapitän-Lehmann-Höhe (Umb)) | Kapitän-Lehmann-Höhe (Umb.) |
| 00916 | Friedrich-Küch-Straße | stadium_1_name | Begasstraße | Begastraße |
| 01144 | Fritz-Schaub-Weg | stadtteile | Burgaltendorf | Altendorf |
| 01151 | Habichtstraße | stadium_3_name | Habichtstraße (Verl) | Habichtstraße (Verl.) |
| 01410 | Huyssenallee | namensgruppe | Familienname, Essener Geschichte und ÖOrtlichkeit | Familienname, Essener Geschichte und Örtlichkeit, urspr.: Kettwiger Chaussee |
| 01410 | Huyssenallee | stadium_1_datum | (urspr., kein Datum) | 1906-01-02 |
| 01410 | Huyssenallee | stadium_1_name | Kettwiger Chaussee | Huyssenallee |
| 01410 | Huyssenallee | stadium_2_datum | 1906-01-02 | — |
| 01410 | Huyssenallee | stadium_2_name | Huyssenallee | — |
| 01630 | Kaldenhoverbaum | lemma | Kaldenhoverbaum | Kaldenhoferbaum |
| 01630 | Kaldenhoverbaum | stadium_2_name | Kaldenhoverbaum | Kaldenhoferbaum |
| 01635 | Kamerunstraße | schl_nr | 01635 | — |
| 01635 | Kamerunstraße | lemma | Kamerunstraße | — |
| 01635 | Kamerunstraße | stadtteile | Gerschede | — |
| 01635 | Kamerunstraße | strassenklasse | Gemeindestraße | — |
| 01635 | Kamerunstraße | namensgruppe | Stadt und Ort | — |
| 01635 | Kamerunstraße | verweis_auf |  | — |
| 01635 | Kamerunstraße | stadium_1_datum | 1939-05-26 | — |
| 01635 | Kamerunstraße | stadium_1_name | Kamerunstraße | — |
| 01770 | Kösters Busch | schl_nr | 01770 | — |
| 01770 | Kösters Busch | lemma | Kösters Busch | — |
| 01770 | Kösters Busch | stadtteile | Stoppenberg | — |
| 01770 | Kösters Busch | strassenklasse | Gemeindestraße | — |
| 01770 | Kösters Busch | namensgruppe | Hofname | — |
| 01770 | Kösters Busch | verweis_auf |  | — |
| 01770 | Kösters Busch | stadium_1_datum | 1910-12-20 | — |
| 01770 | Kösters Busch | stadium_1_name | Zechenstraße | — |
| 01770 | Kösters Busch | stadium_2_datum | 1936-01-15 | — |
| 01770 | Kösters Busch | stadium_2_name | Kösters Busch | — |
| 01979 | Linnekeskamp | schl_nr | 01979 | — |
| 01979 | Linnekeskamp | lemma | Linnekeskamp | — |
| 01979 | Linnekeskamp | stadtteile | Stoppenberg | — |
| 01979 | Linnekeskamp | strassenklasse | Gemeindestraße | — |
| 01979 | Linnekeskamp | namensgruppe | Flurname | — |
| 01979 | Linnekeskamp | verweis_auf |  | — |
| 01979 | Linnekeskamp | stadium_1_datum | 1953-03-03 | — |
| 01979 | Linnekeskamp | stadium_1_name | Linnekeskamp | — |
| 02191 | Manderscheidtstraße | stadium_2_name | Manderscheidtstraße (Verl) | Manderscheidtstraße (Verl.) |
| 02222 | Nagelstraße | schl_nr | 02222 | — |
| 02222 | Nagelstraße | lemma | Nagelstraße | — |
| 02222 | Nagelstraße | stadtteile | Altenessen- Süd | — |
| 02222 | Nagelstraße | strassenklasse | Gemeindestraße | — |
| 02222 | Nagelstraße | namensgruppe | Industrie und Wirtschaft | — |
| 02222 | Nagelstraße | verweis_auf |  | — |
| 02222 | Nagelstraße | stadium_1_datum | 1909-11-26 | — |
| 02222 | Nagelstraße | stadium_1_name | Nagelstraße | — |
| 02356 | Overhammshof | stadium_1_datum | 1970-01-21 | (urspr., kein Datum) |
| 02461 | Priemhauser Weg | namensgruppe | Flurname | Flurname, urspr.: Deilmannsweg (nicht amtl.) |
| 02461 | Priemhauser Weg | stadium_1_datum | (urspr., kein Datum) | 1937-11-20 |
| 02461 | Priemhauser Weg | stadium_1_name | Deilmannsweg {nicht amtl.) | Priemhauser Weg |
| 02461 | Priemhauser Weg | stadium_2_datum | 1937-11-20 | — |
| 02461 | Priemhauser Weg | stadium_2_name | Priemhauser Weg | — |
| 02510 | Am Reiterhof | schl_nr | 02510 | — |
| 02510 | Am Reiterhof | lemma | Am Reiterhof | — |
| 02510 | Am Reiterhof | stadtteile | Stoppenberg | — |
| 02510 | Am Reiterhof | strassenklasse | Gemeindestraße | — |
| 02510 | Am Reiterhof | namensgruppe | Lagebezeichnung, vorm.: Distelbeckhof (tiIw.) | — |
| 02510 | Am Reiterhof | verweis_auf |  | — |
| 02510 | Am Reiterhof | stadium_1_datum | 1988-06-24 | — |
| 02510 | Am Reiterhof | stadium_1_name | Am Reiterhof | — |
| 02539 | Kardinal-Hengsbach-Platz | stadium_1_name | Kurienplatz | Kardinal-Hengsbach-Platz |
| 02539 | Kardinal-Hengsbach-Platz | stadium_2_datum | 1994-05-18 | — |
| 02539 | Kardinal-Hengsbach-Platz | stadium_2_name | Kardinal-Hengsbach-Platz | — |
| 02552 | Raiffeisenweg | namensgruppe | Person, Mann, Deutscher, Kommunalbeamter, Siedlung | Person, Mann |
| 02684 | Römlingweg | stadtteile | Überruhr- Holthausen | Überruhr-Holthausen |
| 02727 | Annental | stadtteile | Bergerhausen; Rellinghausen | Bergebausen; Rellinghausen |
| 02727 | Annental | namensgruppe | Kirche und Kloster |  |
| 02727 | Annental | stadium_2_name | Walpurgisstraße (tiw.) | Walburgisstraße (tlw.) |
| 03114 | Ten-Hövel-Weg | stadium_1_name | Ten- Hövel-Weg | Ten-Hövel-Weg |
| 03355 | Werner-Viebig-Weg | stadium_1_datum | (urspr., kein Datum) | 1937-11-20 |
| 03355 | Werner-Viebig-Weg | stadium_1_name | Franziskastraße | Werner-Viebig-Weg |
| 03355 | Werner-Viebig-Weg | stadium_2_datum | 1937-11-20 | — |
| 03355 | Werner-Viebig-Weg | stadium_2_name | Werner-Viebig- Weg | — |
| 03432 | Wolfsbankstraße | stadium_5_name | Carl-Funke- Straße | Carl-Funke-Straße |
| 03432 | Wolfsbankstraße | stadium_7_name | Wolfsbankstraße (Verl) | Wolfsbankstraße (Verl.) |
| 03748 | Schulstraße | schl_nr | 03748 | — |
| 03748 | Schulstraße | lemma | Schulstraße | — |
| 03748 | Schulstraße | stadtteile | Kettwig | — |
| 03748 | Schulstraße | strassenklasse | Gemeindestraße | — |
| 03748 | Schulstraße | namensgruppe | Lagebezeichnung | — |
| 03748 | Schulstraße | verweis_auf |  | — |
| 03748 | Schulstraße | stadium_1_datum | vor 1872 | — |
| 03748 | Schulstraße | stadium_1_name | Schulstraße | — |
| 03748 | Schulstraße | stadium_2_datum | 1939-03-14 | — |
| 03748 | Schulstraße | stadium_2_name | Langemarckstraße (Umb | — |
| 03748 | Schulstraße | stadium_3_datum | 1946-04-04 | — |
| 03748 | Schulstraße | stadium_3_name | Schulstraße (Umb.) | — |

## Modell `qwen`

Gesamt: 478 Felder, 430 korrekt, Fehlerquote 10.0 %. Vom Parser ausgelassene Felder: 8 von 10 vom Modell gefunden.

| Schicht/Feldtyp | geprüft | korrekt | Fehlerquote |
|---|--:|--:|--:|
| automatisch | 388 | 354 | 8.8 % |
| unsicher | 90 | 76 | 15.6 % |
| lemma | 50 | 47 | 6.0 % |
| namensgruppe | 50 | 45 | 10.0 % |
| schl_nr | 50 | 48 | 4.0 % |
| stadium_datum | 89 | 80 | 10.1 % |
| stadium_name | 89 | 69 | 22.5 % |
| stadtteile | 50 | 45 | 10.0 % |
| strassenklasse | 50 | 48 | 4.0 % |
| verweis_auf | 50 | 48 | 4.0 % |

### Abweichungen

| schl_nr | Lemma | Feld | soll | Modell |
|---|---|---|---|---|
| 00208 | Am Kreyenkrop | namensgruppe | Flurname, 08.10.1896: Rohrstraße | Flurname |
| 00208 | Am Kreyenkrop | stadium_1_datum | 1915-07-09 | 1896-10-08 |
| 00208 | Am Kreyenkrop | stadium_1_name | Bedingrader Straße (tiw.) | Rohrstraße |
| 00208 | Am Kreyenkrop | stadium_2_datum | 1967-05-03 | 1915-07-09 |
| 00208 | Am Kreyenkrop | stadium_2_name | Am Kreyenkrop | Bedingrader Straße (tlw.) |
| 00507 | Byfanger Straße | stadium_1_name | Oststraße (tiw.) | Oststraße (tlw.) |
| 00507 | Byfanger Straße | stadium_4_name | Byfanger Straße (Verl) | Byfanger Straße (Verl.) |
| 00595 | Dahlhauser Straße | stadium_3_datum | 1905-04-13 | (urspr., kein Datum) |
| 00891 | Franziskanerhöhe | stadium_2_name | Kapitän-Lehmann-Höhe (Umb)) | Kapitän-Lehmann-Höhe (Umb.) |
| 00916 | Friedrich-Küch-Straße | schl_nr | 00916 | — |
| 00916 | Friedrich-Küch-Straße | lemma | Friedrich-Küch-Straße | — |
| 00916 | Friedrich-Küch-Straße | stadtteile | Huttrop | — |
| 00916 | Friedrich-Küch-Straße | strassenklasse | Gemeindestraße | — |
| 00916 | Friedrich-Küch-Straße | namensgruppe | Person, Mann, Deutscher | — |
| 00916 | Friedrich-Küch-Straße | verweis_auf |  | — |
| 00916 | Friedrich-Küch-Straße | stadium_1_datum | 1914-10-09 | — |
| 00916 | Friedrich-Küch-Straße | stadium_1_name | Begasstraße | — |
| 00916 | Friedrich-Küch-Straße | stadium_2_datum | 1935-11-14 | — |
| 00916 | Friedrich-Küch-Straße | stadium_2_name | Friedrich-Küch-Straße | — |
| 01151 | Habichtstraße | stadium_3_name | Habichtstraße (Verl) | Habichtstraße (Verl.) |
| 01410 | Huyssenallee | namensgruppe | Familienname, Essener Geschichte und ÖOrtlichkeit | Familienname, Essener Geschichte und Örtlichkeit |
| 01837 | Küppersheide | stadtteile | Bredeney | Bredenei |
| 02191 | Manderscheidtstraße | stadium_2_name | Manderscheidtstraße (Verl) | Manderscheidtstraße (Verl.) |
| 02222 | Nagelstraße | stadtteile | Altenessen- Süd | Altenessen-Süd |
| 02356 | Overhammshof | stadium_1_datum | 1970-01-21 | (urspr., kein Datum) |
| 02356 | Overhammshof | stadium_1_name | Overhammshof |  |
| 02461 | Priemhauser Weg | stadium_1_name | Deilmannsweg {nicht amtl.) | Deilmannsweg (nicht amtli.) |
| 02510 | Am Reiterhof | namensgruppe | Lagebezeichnung, vorm.: Distelbeckhof (tiIw.) | Lagebezeichnung |
| 02510 | Am Reiterhof | stadium_1_datum | 1988-06-24 | (urspr., kein Datum) |
| 02510 | Am Reiterhof | stadium_1_name | Am Reiterhof | Distelbeckhof (tlw.) |
| 02684 | Römlingweg | stadtteile | Überruhr- Holthausen | Überruhr-Holthausen |
| 02727 | Annental | lemma | St. Annental | St. Annetal |
| 02727 | Annental | stadium_2_name | Walpurgisstraße (tiw.) | Walpurgisstraße (tlw.) |
| 02727 | Annental | stadium_3_name | St. Annental | St. Annetal |
| 03114 | Ten-Hövel-Weg | stadium_1_name | Ten- Hövel-Weg | Ten-Hövel-Weg |
| 03355 | Werner-Viebig-Weg | schl_nr | 03355 | — |
| 03355 | Werner-Viebig-Weg | lemma | Werner-Viebig-Weg | — |
| 03355 | Werner-Viebig-Weg | stadtteile | Kray | — |
| 03355 | Werner-Viebig-Weg | strassenklasse | Gemeindestraße | — |
| 03355 | Werner-Viebig-Weg | namensgruppe | Person, Mann, Deutscher, Betriebsdirektor, Siedlung | — |
| 03355 | Werner-Viebig-Weg | verweis_auf |  | — |
| 03355 | Werner-Viebig-Weg | stadium_1_datum | (urspr., kein Datum) | — |
| 03355 | Werner-Viebig-Weg | stadium_1_name | Franziskastraße | — |
| 03355 | Werner-Viebig-Weg | stadium_2_datum | 1937-11-20 | — |
| 03355 | Werner-Viebig-Weg | stadium_2_name | Werner-Viebig- Weg | — |
| 03432 | Wolfsbankstraße | stadium_5_name | Carl-Funke- Straße | Carl-Funke-Straße |
| 03432 | Wolfsbankstraße | stadium_7_name | Wolfsbankstraße (Verl) | Wolfsbankstraße (Verl.) |
| 03748 | Schulstraße | stadium_2_name | Langemarckstraße (Umb | Langemarckstraße (Umb.) |


---

## Messgrundlage

- Gemessen am 2026-09-12/13 über die 47 Buchseiten der Goldstandard-Stichprobe; beide
  Modelle mit demselben Prompt-Stand `530d5c9e77b5` (Endstand, seit dieser Messung
  unverändert).
- Die Normalisierung in `strassen/llm_vergleich.py` wurde für diese Messung **nicht**
  angepasst: alle Datumsangaben der Stichprobenseiten waren in der vorhandenen Form
  normalisierbar.
- Die Modelle sind zweite Leser; sie ändern den Status im Datensatz nicht.
