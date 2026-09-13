# Unabhängige LLM-Lesung — Kennzahlen

Zwei bildfähige Modelle haben die Buchseiten unabhängig vom Parser gelesen (nur das
Seitenbild, kein OCR-Text). Die Modelle **verändern den Status nicht** (Option A der
Spec 2026-09-12); Abweichungen stehen in `daten/pruefung_llm.csv` zur manuellen Prüfung.
Beim Modell fehlende Einträge zählen in `eintraege_fehlend`, nicht in der
Übereinstimmungsquote — diese misst nur Felder beiderseits vorhandener Einträge.

## Modell `mistral`

- Seiten gelesen: 387, unlesbar: 0
- Einträge beim Modell: 3067, beim Parser fehlend im Modell: 349, nur beim Modell: 70
- Daten nicht normalisierbar: 214
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 340

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2669 | 2416 | 90.5 % |
| automatisch | namensgruppe | 2669 | 2313 | 86.7 % |
| automatisch | stadium_datum | 3832 | 3403 | 88.8 % |
| automatisch | stadium_name | 3832 | 3125 | 81.6 % |
| automatisch | stadium_urspruenglich | 3832 | 3505 | 91.5 % |
| automatisch | stadtteile | 2669 | 2508 | 94.0 % |
| automatisch | strassenklasse | 2669 | 2644 | 99.1 % |
| automatisch | verweis_auf | 2669 | 2546 | 95.4 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 327 | 249 | 76.1 % |
| unsicher | namensgruppe | 327 | 250 | 76.5 % |
| unsicher | stadium_datum | 537 | 441 | 82.1 % |
| unsicher | stadium_name | 537 | 381 | 70.9 % |
| unsicher | stadium_urspruenglich | 537 | 460 | 85.7 % |
| unsicher | stadtteile | 327 | 293 | 89.6 % |
| unsicher | strassenklasse | 327 | 308 | 94.2 % |
| unsicher | verweis_auf | 327 | 305 | 93.3 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 10
- Daten nicht normalisierbar: 30
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 334

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2913 | 2754 | 94.5 % |
| automatisch | namensgruppe | 2913 | 2837 | 97.4 % |
| automatisch | stadium_datum | 4141 | 4132 | 99.8 % |
| automatisch | stadium_name | 4141 | 3936 | 95.0 % |
| automatisch | stadium_urspruenglich | 4141 | 4140 | 100.0 % |
| automatisch | stadtteile | 2913 | 2772 | 95.2 % |
| automatisch | strassenklasse | 2913 | 2910 | 99.9 % |
| automatisch | verweis_auf | 2913 | 2898 | 99.5 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 359 | 285 | 79.4 % |
| unsicher | namensgruppe | 359 | 337 | 93.9 % |
| unsicher | stadium_datum | 557 | 535 | 96.1 % |
| unsicher | stadium_name | 557 | 484 | 86.9 % |
| unsicher | stadium_urspruenglich | 557 | 543 | 97.5 % |
| unsicher | stadtteile | 359 | 339 | 94.4 % |
| unsicher | strassenklasse | 359 | 345 | 96.1 % |
| unsicher | verweis_auf | 359 | 345 | 96.1 % |

