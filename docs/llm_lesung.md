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
| automatisch | lemma | 2663 | 2447 | 91.9 % |
| automatisch | namensgruppe | 2663 | 2332 | 87.6 % |
| automatisch | stadium_datum | 3797 | 3374 | 88.9 % |
| automatisch | stadium_name | 3797 | 3121 | 82.2 % |
| automatisch | stadium_urspruenglich | 3797 | 3472 | 91.4 % |
| automatisch | stadtteile | 2663 | 2515 | 94.4 % |
| automatisch | strassenklasse | 2663 | 2640 | 99.1 % |
| automatisch | verweis_auf | 2663 | 2539 | 95.3 % |
| geprueft | lemma | 200 | 193 | 96.5 % |
| geprueft | namensgruppe | 200 | 172 | 86.0 % |
| geprueft | stadium_datum | 323 | 293 | 90.7 % |
| geprueft | stadium_name | 323 | 281 | 87.0 % |
| geprueft | stadium_urspruenglich | 323 | 301 | 93.2 % |
| geprueft | stadtteile | 200 | 190 | 95.0 % |
| geprueft | strassenklasse | 200 | 200 | 100.0 % |
| geprueft | verweis_auf | 200 | 192 | 96.0 % |
| unsicher | lemma | 134 | 112 | 83.6 % |
| unsicher | namensgruppe | 134 | 96 | 71.6 % |
| unsicher | stadium_datum | 254 | 188 | 74.0 % |
| unsicher | stadium_name | 254 | 165 | 65.0 % |
| unsicher | stadium_urspruenglich | 254 | 197 | 77.6 % |
| unsicher | stadtteile | 134 | 120 | 89.6 % |
| unsicher | strassenklasse | 134 | 126 | 94.0 % |
| unsicher | verweis_auf | 134 | 126 | 94.0 % |

## Modell `qwen`

- Seiten gelesen: 381, unlesbar: 6
- Einträge beim Modell: 3283, beim Parser fehlend im Modell: 0, nur beim Modell: 10
- Daten nicht normalisierbar: 30
- Einträge am Seitenende (Kette kann auf der Folgeseite weiterlaufen, nur Kopf verglichen): 334

| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |
|---|---|--:|--:|--:|
| automatisch | lemma | 2917 | 2793 | 95.7 % |
| automatisch | namensgruppe | 2917 | 2869 | 98.4 % |
| automatisch | stadium_datum | 4117 | 4112 | 99.9 % |
| automatisch | stadium_name | 4117 | 3942 | 95.7 % |
| automatisch | stadium_urspruenglich | 4117 | 4116 | 100.0 % |
| automatisch | stadtteile | 2917 | 2790 | 95.6 % |
| automatisch | strassenklasse | 2917 | 2916 | 100.0 % |
| automatisch | verweis_auf | 2917 | 2905 | 99.6 % |
| geprueft | lemma | 201 | 198 | 98.5 % |
| geprueft | namensgruppe | 201 | 195 | 97.0 % |
| geprueft | stadium_datum | 321 | 316 | 98.4 % |
| geprueft | stadium_name | 321 | 306 | 95.3 % |
| geprueft | stadium_urspruenglich | 321 | 317 | 98.8 % |
| geprueft | stadtteile | 201 | 195 | 97.0 % |
| geprueft | strassenklasse | 201 | 201 | 100.0 % |
| geprueft | verweis_auf | 201 | 192 | 95.5 % |
| unsicher | lemma | 155 | 135 | 87.1 % |
| unsicher | namensgruppe | 155 | 147 | 94.8 % |
| unsicher | stadium_datum | 265 | 251 | 94.7 % |
| unsicher | stadium_name | 265 | 234 | 88.3 % |
| unsicher | stadium_urspruenglich | 265 | 255 | 96.2 % |
| unsicher | stadtteile | 155 | 150 | 96.8 % |
| unsicher | strassenklasse | 155 | 152 | 98.1 % |
| unsicher | verweis_auf | 155 | 152 | 98.1 % |

