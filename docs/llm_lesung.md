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
| geprueft | lemma | 242 | 224 | 92.6 % |
| geprueft | namensgruppe | 242 | 199 | 82.2 % |
| geprueft | stadium_datum | 410 | 353 | 86.1 % |
| geprueft | stadium_name | 410 | 335 | 81.7 % |
| geprueft | stadium_urspruenglich | 410 | 365 | 89.0 % |
| geprueft | stadtteile | 242 | 228 | 94.2 % |
| geprueft | strassenklasse | 242 | 238 | 98.3 % |
| geprueft | verweis_auf | 242 | 230 | 95.0 % |
| unsicher | lemma | 98 | 88 | 89.8 % |
| unsicher | namensgruppe | 98 | 72 | 73.5 % |
| unsicher | stadium_datum | 198 | 155 | 78.3 % |
| unsicher | stadium_name | 198 | 138 | 69.7 % |
| unsicher | stadium_urspruenglich | 198 | 161 | 81.3 % |
| unsicher | stadtteile | 98 | 88 | 89.8 % |
| unsicher | strassenklasse | 98 | 94 | 95.9 % |
| unsicher | verweis_auf | 98 | 92 | 93.9 % |

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
| geprueft | lemma | 258 | 253 | 98.1 % |
| geprueft | namensgruppe | 258 | 246 | 95.3 % |
| geprueft | stadium_datum | 429 | 415 | 96.7 % |
| geprueft | stadium_name | 429 | 409 | 95.3 % |
| geprueft | stadium_urspruenglich | 429 | 427 | 99.5 % |
| geprueft | stadtteile | 258 | 250 | 96.9 % |
| geprueft | strassenklasse | 258 | 255 | 98.8 % |
| geprueft | verweis_auf | 258 | 244 | 94.6 % |
| unsicher | lemma | 104 | 101 | 97.1 % |
| unsicher | namensgruppe | 104 | 104 | 100.0 % |
| unsicher | stadium_datum | 197 | 195 | 99.0 % |
| unsicher | stadium_name | 197 | 188 | 95.4 % |
| unsicher | stadium_urspruenglich | 197 | 197 | 100.0 % |
| unsicher | stadtteile | 104 | 100 | 96.2 % |
| unsicher | strassenklasse | 104 | 103 | 99.0 % |
| unsicher | verweis_auf | 104 | 102 | 98.1 % |

