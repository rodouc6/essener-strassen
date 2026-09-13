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
| geprueft | lemma | 209 | 202 | 96.7 % |
| geprueft | namensgruppe | 209 | 178 | 85.2 % |
| geprueft | stadium_datum | 346 | 314 | 90.8 % |
| geprueft | stadium_name | 346 | 300 | 86.7 % |
| geprueft | stadium_urspruenglich | 346 | 321 | 92.8 % |
| geprueft | stadtteile | 209 | 199 | 95.2 % |
| geprueft | strassenklasse | 209 | 209 | 100.0 % |
| geprueft | verweis_auf | 209 | 200 | 95.7 % |
| unsicher | lemma | 131 | 109 | 83.2 % |
| unsicher | namensgruppe | 131 | 94 | 71.8 % |
| unsicher | stadium_datum | 249 | 185 | 74.3 % |
| unsicher | stadium_name | 249 | 163 | 65.5 % |
| unsicher | stadium_urspruenglich | 249 | 195 | 78.3 % |
| unsicher | stadtteile | 131 | 117 | 89.3 % |
| unsicher | strassenklasse | 131 | 123 | 93.9 % |
| unsicher | verweis_auf | 131 | 124 | 94.7 % |

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
| geprueft | lemma | 210 | 207 | 98.6 % |
| geprueft | namensgruppe | 210 | 201 | 95.7 % |
| geprueft | stadium_datum | 344 | 339 | 98.5 % |
| geprueft | stadium_name | 344 | 330 | 95.9 % |
| geprueft | stadium_urspruenglich | 344 | 342 | 99.4 % |
| geprueft | stadtteile | 210 | 204 | 97.1 % |
| geprueft | strassenklasse | 210 | 210 | 100.0 % |
| geprueft | verweis_auf | 210 | 201 | 95.7 % |
| unsicher | lemma | 152 | 132 | 86.8 % |
| unsicher | namensgruppe | 152 | 145 | 95.4 % |
| unsicher | stadium_datum | 259 | 247 | 95.4 % |
| unsicher | stadium_name | 259 | 230 | 88.8 % |
| unsicher | stadium_urspruenglich | 259 | 251 | 96.9 % |
| unsicher | stadtteile | 152 | 147 | 96.7 % |
| unsicher | strassenklasse | 152 | 149 | 98.0 % |
| unsicher | verweis_auf | 152 | 149 | 98.0 % |

