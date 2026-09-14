# Qualitätsbericht

Drei unabhängige Selbstprüfungen des erschlossenen Datensatzes. Die konkreten Ausreißer (Lemma, Schlüsselnummer, Grund; ohne Textzitate) stehen in [`daten/pruefung_validierung.csv`](../daten/pruefung_validierung.csv).

## 1. Schlüsselnummern

- Bereich: 1–3771
- erfasst: 3354
- Lücken: 420
- Dubletten: 2

## 2. Alphabetische Ordnung

- aus der Sortierung fallende Lemmata: 31
  - davon bereits als „unsicher" gekennzeichnet: 0
  - davon neu auffällig (bisher „automatisch"): 31
  (bekannte Grenze: die Prüfung vergleicht nur direkte Nachbarn — zwei aufeinanderfolgende, gleichsinnig falsch sortierte Lemmata bleiben unentdeckt; Fälle in daten/pruefung_validierung.csv, grund=Alphabet)

## 3. Abgleich mit dem amtlichen Straßenverzeichnis

- bestätigt: 3339
- nicht im Verzeichnis: 15
  (erwartbar bei aufgehobenen Straßen — nicht automatisch ein Fehler; Fälle in daten/pruefung_validierung.csv, grund=„nicht im amtlichen Verzeichnis")

## 4. Unabhängige LLM-Lesung

Zwei bildfähige Modelle haben die Seitenbilder unabhängig vom Parser gelesen; Kennzahlen in [`llm_lesung.md`](llm_lesung.md), die eigene Fehlerquote der Modelle gegen die Goldstandard-Stichprobe in [`goldstandard/ergebnis_llm.md`](goldstandard/ergebnis_llm.md).

