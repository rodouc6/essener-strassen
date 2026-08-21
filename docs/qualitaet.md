# Qualitätsbericht

Drei unabhängige Selbstprüfungen des erschlossenen Datensatzes. Die konkreten Ausreißer (Lemma, Schlüsselnummer, Grund; ohne Textzitate) stehen in [`daten/pruefung_validierung.csv`](../daten/pruefung_validierung.csv).

## 1. Schlüsselnummern

- Bereich: 1–3771
- erfasst: 3338
- Lücken: 436
- Dubletten: 3

## 2. Alphabetische Ordnung

- aus der Sortierung fallende Lemmata: 73
  - davon bereits als „unsicher" gekennzeichnet: 38
  - davon neu auffällig (bisher „automatisch"): 35
  (bekannte Grenze: die Prüfung vergleicht nur direkte Nachbarn — zwei aufeinanderfolgende, gleichsinnig falsch sortierte Lemmata bleiben unentdeckt; Fälle in daten/pruefung_validierung.csv, grund=Alphabet)

## 3. Abgleich mit dem amtlichen Straßenverzeichnis

- bestätigt: 3196
- nicht im Verzeichnis: 142
  (erwartbar bei aufgehobenen Straßen — nicht automatisch ein Fehler; Fälle in daten/pruefung_validierung.csv, grund=„nicht im amtlichen Verzeichnis")

