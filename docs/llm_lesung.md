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
| automatisch | lemma | 2774 | 2514 | 90.6 % |
| automatisch | namensgruppe | 2774 | 2401 | 86.6 % |
| automatisch | stadium_datum | 3972 | 3529 | 88.8 % |
| automatisch | stadium_name | 3972 | 3246 | 81.7 % |
| automatisch | stadium_urspruenglich | 3972 | 3635 | 91.5 % |
| automatisch | stadtteile | 2774 | 2603 | 93.8 % |
| automatisch | strassenklasse | 2774 | 2749 | 99.1 % |
| automatisch | verweis_auf | 2774 | 2646 | 95.4 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 222 | 151 | 68.0 % |
| unsicher | namensgruppe | 222 | 162 | 73.0 % |
| unsicher | stadium_datum | 397 | 315 | 79.3 % |
| unsicher | stadium_name | 397 | 260 | 65.5 % |
| unsicher | stadium_urspruenglich | 397 | 330 | 83.1 % |
| unsicher | stadtteile | 222 | 198 | 89.2 % |
| unsicher | strassenklasse | 222 | 203 | 91.4 % |
| unsicher | verweis_auf | 222 | 205 | 92.3 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 10
- Daten nicht normalisierbar: 30
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 334

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 3029 | 2864 | 94.6 % |
| automatisch | namensgruppe | 3029 | 2951 | 97.4 % |
| automatisch | stadium_datum | 4290 | 4281 | 99.8 % |
| automatisch | stadium_name | 4290 | 4080 | 95.1 % |
| automatisch | stadium_urspruenglich | 4290 | 4289 | 100.0 % |
| automatisch | stadtteile | 3029 | 2882 | 95.1 % |
| automatisch | strassenklasse | 3029 | 3026 | 99.9 % |
| automatisch | verweis_auf | 3029 | 3013 | 99.5 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 243 | 175 | 72.0 % |
| unsicher | namensgruppe | 243 | 223 | 91.8 % |
| unsicher | stadium_datum | 408 | 386 | 94.6 % |
| unsicher | stadium_name | 408 | 340 | 83.3 % |
| unsicher | stadium_urspruenglich | 408 | 394 | 96.6 % |
| unsicher | stadtteile | 243 | 229 | 94.2 % |
| unsicher | strassenklasse | 243 | 229 | 94.2 % |
| unsicher | verweis_auf | 243 | 230 | 94.7 % |

