# Unabhängige LLM-Lesung — Kennzahlen

Zwei bildfähige Modelle haben die Buchseiten unabhängig vom Parser gelesen (nur das
Seitenbild, kein OCR-Text). Die Modelle **verändern den Status nicht** (Option A der
Spec 2026-09-12); Abweichungen stehen in `daten/pruefung_llm.csv` zur manuellen Prüfung.
Beim Modell fehlende Einträge zählen in `eintraege_fehlend`, nicht in der
Übereinstimmungsquote — diese misst nur Felder beiderseits vorhandener Einträge.

## Modell `mistral`

- Seiten gelesen: 387, unlesbar: 0
- Einträge beim Modell: 3067, beim Parser fehlend im Modell: 349, nur beim Modell: 64
- Daten nicht normalisierbar: 214
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 340

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2663 | 2447 | 91.9 % |
| automatisch | namensgruppe | 2663 | 2332 | 87.6 % |
| automatisch | stadium_datum | 3782 | 3361 | 88.9 % |
| automatisch | stadium_name | 3782 | 3108 | 82.2 % |
| automatisch | stadium_urspruenglich | 3782 | 3459 | 91.5 % |
| automatisch | stadtteile | 2663 | 2515 | 94.4 % |
| automatisch | strassenklasse | 2663 | 2640 | 99.1 % |
| automatisch | verweis_auf | 2663 | 2539 | 95.3 % |
| geprueft | lemma | 338 | 311 | 92.0 % |
| geprueft | namensgruppe | 338 | 270 | 79.9 % |
| geprueft | stadium_datum | 603 | 508 | 84.2 % |
| geprueft | stadium_name | 603 | 473 | 78.4 % |
| geprueft | stadium_urspruenglich | 603 | 526 | 87.2 % |
| geprueft | stadtteile | 338 | 315 | 93.2 % |
| geprueft | strassenklasse | 338 | 330 | 97.6 % |
| geprueft | verweis_auf | 338 | 321 | 95.0 % |
| unsicher | lemma | 2 | 1 | 50.0 % |
| unsicher | namensgruppe | 2 | 1 | 50.0 % |
| unsicher | stadium_datum | 5 | 0 | 0.0 % |
| unsicher | stadium_name | 5 | 0 | 0.0 % |
| unsicher | stadium_urspruenglich | 5 | 0 | 0.0 % |
| unsicher | stadtteile | 2 | 1 | 50.0 % |
| unsicher | strassenklasse | 2 | 2 | 100.0 % |
| unsicher | verweis_auf | 2 | 1 | 50.0 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 4
- Daten nicht normalisierbar: 30
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 334

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2917 | 2793 | 95.7 % |
| automatisch | namensgruppe | 2917 | 2869 | 98.4 % |
| automatisch | stadium_datum | 4102 | 4097 | 99.9 % |
| automatisch | stadium_name | 4102 | 3927 | 95.7 % |
| automatisch | stadium_urspruenglich | 4102 | 4101 | 100.0 % |
| automatisch | stadtteile | 2917 | 2790 | 95.6 % |
| automatisch | strassenklasse | 2917 | 2916 | 100.0 % |
| automatisch | verweis_auf | 2917 | 2905 | 99.6 % |
| geprueft | lemma | 360 | 352 | 97.8 % |
| geprueft | namensgruppe | 360 | 348 | 96.7 % |
| geprueft | stadium_datum | 621 | 605 | 97.4 % |
| geprueft | stadium_name | 621 | 592 | 95.3 % |
| geprueft | stadium_urspruenglich | 621 | 619 | 99.7 % |
| geprueft | stadtteile | 360 | 348 | 96.7 % |
| geprueft | strassenklasse | 360 | 356 | 98.9 % |
| geprueft | verweis_auf | 360 | 345 | 95.8 % |
| unsicher | lemma | 2 | 2 | 100.0 % |
| unsicher | namensgruppe | 2 | 2 | 100.0 % |
| unsicher | stadium_datum | 5 | 5 | 100.0 % |
| unsicher | stadium_name | 5 | 5 | 100.0 % |
| unsicher | stadium_urspruenglich | 5 | 5 | 100.0 % |
| unsicher | stadtteile | 2 | 2 | 100.0 % |
| unsicher | strassenklasse | 2 | 2 | 100.0 % |
| unsicher | verweis_auf | 2 | 1 | 50.0 % |

