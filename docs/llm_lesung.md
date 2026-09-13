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
| automatisch | stadium_datum | 3789 | 3368 | 88.9 % |
| automatisch | stadium_name | 3789 | 3115 | 82.2 % |
| automatisch | stadium_urspruenglich | 3789 | 3466 | 91.5 % |
| automatisch | stadtteile | 2663 | 2515 | 94.4 % |
| automatisch | strassenklasse | 2663 | 2640 | 99.1 % |
| automatisch | verweis_auf | 2663 | 2539 | 95.3 % |
| geprueft | lemma | 207 | 200 | 96.6 % |
| geprueft | namensgruppe | 207 | 177 | 85.5 % |
| geprueft | stadium_datum | 345 | 313 | 90.7 % |
| geprueft | stadium_name | 345 | 298 | 86.4 % |
| geprueft | stadium_urspruenglich | 345 | 320 | 92.8 % |
| geprueft | stadtteile | 207 | 197 | 95.2 % |
| geprueft | strassenklasse | 207 | 207 | 100.0 % |
| geprueft | verweis_auf | 207 | 198 | 95.7 % |
| unsicher | lemma | 133 | 111 | 83.5 % |
| unsicher | namensgruppe | 133 | 95 | 71.4 % |
| unsicher | stadium_datum | 249 | 185 | 74.3 % |
| unsicher | stadium_name | 249 | 163 | 65.5 % |
| unsicher | stadium_urspruenglich | 249 | 195 | 78.3 % |
| unsicher | stadtteile | 133 | 119 | 89.5 % |
| unsicher | strassenklasse | 133 | 125 | 94.0 % |
| unsicher | verweis_auf | 133 | 126 | 94.7 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 4
- Daten nicht normalisierbar: 30
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 334

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2917 | 2793 | 95.7 % |
| automatisch | namensgruppe | 2917 | 2869 | 98.4 % |
| automatisch | stadium_datum | 4109 | 4104 | 99.9 % |
| automatisch | stadium_name | 4109 | 3934 | 95.7 % |
| automatisch | stadium_urspruenglich | 4109 | 4108 | 100.0 % |
| automatisch | stadtteile | 2917 | 2790 | 95.6 % |
| automatisch | strassenklasse | 2917 | 2916 | 100.0 % |
| automatisch | verweis_auf | 2917 | 2905 | 99.6 % |
| geprueft | lemma | 208 | 205 | 98.6 % |
| geprueft | namensgruppe | 208 | 200 | 96.2 % |
| geprueft | stadium_datum | 343 | 338 | 98.5 % |
| geprueft | stadium_name | 343 | 329 | 95.9 % |
| geprueft | stadium_urspruenglich | 343 | 341 | 99.4 % |
| geprueft | stadtteile | 208 | 202 | 97.1 % |
| geprueft | strassenklasse | 208 | 208 | 100.0 % |
| geprueft | verweis_auf | 208 | 199 | 95.7 % |
| unsicher | lemma | 154 | 134 | 87.0 % |
| unsicher | namensgruppe | 154 | 146 | 94.8 % |
| unsicher | stadium_datum | 259 | 247 | 95.4 % |
| unsicher | stadium_name | 259 | 230 | 88.8 % |
| unsicher | stadium_urspruenglich | 259 | 251 | 96.9 % |
| unsicher | stadtteile | 154 | 149 | 96.8 % |
| unsicher | strassenklasse | 154 | 151 | 98.1 % |
| unsicher | verweis_auf | 154 | 151 | 98.1 % |

