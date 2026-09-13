# Unabhängige LLM-Lesung — Kennzahlen

Zwei bildfähige Modelle haben die Buchseiten unabhängig vom Parser gelesen (nur das
Seitenbild, kein OCR-Text). Die Modelle **verändern den Status nicht** (Option A der
Spec 2026-09-12); Abweichungen stehen in `daten/pruefung_llm.csv` zur manuellen Prüfung.
Beim Modell fehlende Einträge zählen in `eintraege_fehlend`, nicht in der
Übereinstimmungsquote — diese misst nur Felder beiderseits vorhandener Einträge.

## Modell `mistral`

- Seiten gelesen: 387, unlesbar: 0
- Einträge beim Modell: 3067, beim Parser fehlend im Modell: 349, nur beim Modell: 81
- Daten nicht normalisierbar: 214

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2749 | 2483 | 90.3 % |
| automatisch | namensgruppe | 2749 | 2344 | 85.3 % |
| automatisch | stadium_datum | 4428 | 3879 | 87.6 % |
| automatisch | stadium_name | 4428 | 3381 | 76.4 % |
| automatisch | stadium_urspruenglich | 4428 | 4016 | 90.7 % |
| automatisch | stadtteile | 2749 | 2456 | 89.3 % |
| automatisch | strassenklasse | 2749 | 2723 | 99.1 % |
| automatisch | verweis_auf | 2749 | 2621 | 95.3 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 236 | 158 | 66.9 % |
| unsicher | namensgruppe | 236 | 172 | 72.9 % |
| unsicher | stadium_datum | 484 | 388 | 80.2 % |
| unsicher | stadium_name | 484 | 281 | 58.1 % |
| unsicher | stadium_urspruenglich | 484 | 413 | 85.3 % |
| unsicher | stadtteile | 236 | 204 | 86.4 % |
| unsicher | strassenklasse | 236 | 217 | 91.9 % |
| unsicher | verweis_auf | 236 | 219 | 92.8 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 20
- Daten nicht normalisierbar: 30

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 3005 | 2838 | 94.4 % |
| automatisch | namensgruppe | 3005 | 2875 | 95.7 % |
| automatisch | stadium_datum | 4398 | 4387 | 99.7 % |
| automatisch | stadium_name | 4398 | 3938 | 89.5 % |
| automatisch | stadium_urspruenglich | 4398 | 4397 | 100.0 % |
| automatisch | stadtteile | 3005 | 2687 | 89.4 % |
| automatisch | strassenklasse | 3005 | 3001 | 99.9 % |
| automatisch | verweis_auf | 3005 | 2987 | 99.4 % |
| geprueft | lemma | 1 | 1 | 100.0 % |
| geprueft | namensgruppe | 1 | 1 | 100.0 % |
| geprueft | stadium_datum | 1 | 1 | 100.0 % |
| geprueft | stadium_name | 1 | 1 | 100.0 % |
| geprueft | stadium_urspruenglich | 1 | 1 | 100.0 % |
| geprueft | stadtteile | 1 | 1 | 100.0 % |
| geprueft | strassenklasse | 1 | 1 | 100.0 % |
| geprueft | verweis_auf | 1 | 1 | 100.0 % |
| unsicher | lemma | 257 | 179 | 69.6 % |
| unsicher | namensgruppe | 257 | 234 | 91.1 % |
| unsicher | stadium_datum | 472 | 450 | 95.3 % |
| unsicher | stadium_name | 472 | 336 | 71.2 % |
| unsicher | stadium_urspruenglich | 472 | 458 | 97.0 % |
| unsicher | stadtteile | 257 | 229 | 89.1 % |
| unsicher | strassenklasse | 257 | 243 | 94.6 % |
| unsicher | verweis_auf | 257 | 242 | 94.2 % |

