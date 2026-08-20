# Essener Straßenverzeichnis als Forschungsdatensatz — Design

**Datum:** 2026-08-20
**Status:** Entwurf zur Abnahme

## 1. Zweck

Aus Erwin Dickhoffs *Essener Straßen* (Klartext-Verlag, Essen 2015) entsteht ein
strukturierter, publizierbarer Datensatz aller Essener Straßen mit ihrer datierten
Namensgeschichte. Er dient zwei Zwecken:

1. **Nachnutzbarer Forschungsdatensatz** — veröffentlicht über Zenodo mit DOI, damit
   andere Projekte historische Essener Adressen auflösen können.
2. **Grundlage der Adressauflösung** im Projekt *Adressbuch Essen 1936* — dort ersetzt
   er die bisherige, schwächere Konkordanz.

### Der konkrete Anlass

Das Kartenprojekt nutzt bisher `shared/strassen_konkordanz.csv` mit **442 Einträgen**.
Diese stammen aus `Essener_Strassennamen_Konkordanz.xlsx` (1.684 Zeilen), die laut ihrem
eigenen Hinweisblatt automatisch aus Wikipedia-Artikeln extrahiert wurde — deren
Hauptquelle wiederum Dickhoff 2015 ist. Die bisherige Konkordanz ist also eine **zweifach
abgeleitete Form genau dieses Werks**.

Der Verlust dabei ist messbar: Von 1.684 Excel-Zeilen überstehen nur 442 den
`gilt_1936`-Filter in `pipeline/konvert_shared.py`, weil Wikipedia die Datierung oft nicht
hergibt (269 Zeilen ohne „Zeitraum von"). Dickhoff datiert dagegen taggenau. Bei derzeit
**8.323 nicht geokodierten Adressen** im Kartenprojekt ist das ein erheblicher Hebel.

## 2. Quelle und rechtlicher Rahmen

**Quelle:** Erwin Dickhoff: *Essener Straßen*. Klartext-Verlag, Essen 2015.
ISBN 978-3-8375-1231-1. Als Scan in zwei Bänden (100 + 94 Doppelseiten,
Buchseiten 2–201 und 202–388), 300 dpi, ohne Textebene.

**Rechtliche Linie.** Das Werk ist urheberrechtlich geschützt. Der Datensatz enthält
daher ausschließlich **nicht schutzfähige Fakten**: Straßenname, Schlüsselnummer,
Stadtteil, Straßenklasse, Namensgruppe, Umbenennungsdaten. Die **Erläuterungstexte**
(Namensherkunft, Hofgeschichte, Biographien, Literaturangaben) bleiben als lokaler
Arbeitsstand im Repository, sind aber von der Veröffentlichung ausgeschlossen — die
Nutzung für die eigene Forschung stützt sich auf § 60c UrhG.

Dickhoff wird im Datensatz durchgängig als Quelle geführt, mit Buchseite je Eintrag.

## 3. Verarbeitungsstufen

```
PDF-Doppelseiten
   └─(1) OCR ──────────► ocr/seiten/sNNN.txt      (eine Datei je Buchseite)
                              │
   └─(2) Parser ─────────────►│ strassen.csv + namen.csv + pruefung.csv
                              │
   └─(3) Validierung ─────────►│ qualitaet.md (bezifferte Fehlerquoten)
                              │
   └─(4) Ableitung ───────────► konkordanz_1936.csv → Kartenprojekt
```

### Stufe 1 — OCR (abgeschlossen)

Je PDF-Seite wird bei 300 dpi gerendert, der Bundsteg als weißer Mittelstreifen erkannt
und die Doppelseite dort in zwei Buchseiten geteilt; jede Hälfte liest tesseract (`deu`,
`--psm 3`).

Die Teilung ist notwendig, weil sie die **Buchseitenzahl als Beleg** sichert. Ein
Gegentest an S. 210/211 zeigte: geteilt und ungeteilt liefern denselben Text (11.516 vs.
11.517 Zeichen, 23 vs. 23 Einträge, Abweichung in einer einzigen Zeile an einem
Bruchzeichen). Der Gewinn liegt allein in der Seitenzuordnung.

Die Schnittposition **muss** erkannt werden: über alle 194 Doppelseiten schwankt sie
zwischen 44,1 % und 53,5 % der Bildbreite. Eine feste Mitte läge stellenweise über 200 px
im Textbereich. Die Erkennung greift auf allen 194 Seiten; der Fallback auf die
geometrische Mitte wurde nie gebraucht, bleibt aber als Protokolleintrag bestehen.

Die gedruckte Seitenzahl ist **nicht** verlässlich lesbar (auf S. 210 fehlte sie im OCR,
auf S. 211 nicht). Die Buchseite wird deshalb aus der laufenden PDF-Seite berechnet; die
gelesene Zahl dient nur der Kontrolle.

### Stufe 2 — Parser

Der Eintragskopf ist streng formatiert:

```
Lemma: Schl.-Nr.: NNNNN, Stadtteil X, Str.-Kl.: …, Str.-Gr.: …,
       [urspr.: …,] [TT. Monat JJJJ: Name,]… . [Erläuterungstext]
```

Der Parser arbeitet **regelbasiert und deterministisch** — nicht mit einem Sprachmodell.
Begründung: Der Datensatz wird veröffentlicht und muss von Dritten reproduzierbar sein;
ein Sprachmodell erzeugt falsche Angaben in plausibler Form, während ein Regelparser
sichtbar scheitert. Was er nicht sicher erfassen kann, geht nach `pruefung.csv` zur
manuellen Klärung — derselbe Round-Trip, den das Kartenprojekt bei den Körperschaften
verwendet.

Die Ankererkennung muss OCR-Fehler tolerieren: `Sch!.-Nr.` statt `Schl.-Nr.` kam bereits
in der Stichprobe vor. Ebenso `Str. Gr.` statt `Str.-Gr.`.

### Stufe 3 — Validierung

Das Werk lässt sich dreifach unabhängig gegen sich selbst prüfen:

| Prüfung | Findet |
|---|---|
| Schlüsselnummern (amtlich, fortlaufend) | übersprungene und doppelt gelesene Einträge |
| alphabetische Ordnung der Lemmata | verstümmelte Lemmata (`Kütings` → `Kiitings`) |
| Abgleich mit `strassen_aktuell.csv` (3.388 amtliche Namen) | OCR-Fehler in heute noch existierenden Namen |

Dazu eine **Goldstandard-Stichprobe**: 50 zufällig gezogene Einträge werden Zeichen für
Zeichen gegen den Scan geprüft. Ergebnis ist eine bezifferte Feldfehlerquote, die im
README ausgewiesen wird — Qualität belegt statt behauptet.

### Stufe 4 — Ableitung

`konkordanz_1936.csv` entsteht aus `namen.csv`: für jede Straße das Namensstadium, das am
Stichtag 31.12.1936 galt, verknüpft mit dem heutigen Lemma. Straßen, deren Datierung den
Stichtag nicht sicher entscheidet, werden **gekennzeichnet, nicht geraten**.

## 4. Datenmodell

Zwei verknüpfte Tabellen statt einer flachen Konkordanz. Grund: Ein Eintrag trägt
Eigenschaften der Straße *und* eine Folge von Namensstadien — eine 1:n-Beziehung, die in
einer flachen Tabelle nur als unparsbares Textfeld unterzubringen wäre.

### `strassen.csv`

| Feld | Beschreibung |
|---|---|
| `schl_nr` | amtliche Schlüsselnummer, fünfstellig, Primärschlüssel |
| `lemma` | heutiger Straßenname (Stichwort des Eintrags) |
| `stadtteile` | Stadtteil(e), mehrere durch `;` getrennt |
| `strassenklasse` | Gemeindestraße, Kreisstraße, Landstraße … (mehrere möglich) |
| `namensgruppe` | Str.-Gr. wörtlich übernommen (Flurname, Person, Lagebezeichnung …) |
| `verweis_auf` | bei „Siehe X" das Ziel-Lemma, sonst leer |
| `buchseite` | Beleg: Seite in Dickhoff 2015 |
| `status` | `automatisch` \| `geprueft` \| `unsicher` |

### `namen.csv`

| Feld | Beschreibung |
|---|---|
| `schl_nr` | Fremdschlüssel auf `strassen.csv` |
| `stadium` | laufende Nummer der Namensstufe, 1 = älteste |
| `gueltig_ab` | ISO-Datum, soweit bekannt |
| `datum_praezision` | `tag` \| `monat` \| `jahr` \| `vor` \| `nach` \| `unbekannt` |
| `name` | Straßenname in diesem Stadium |
| `ist_urspruenglich` | wahr bei `urspr.:`-Angaben ohne Datum |

Beispiel (Schl.-Nr. 01838, Buchseite 211):

```
01838, 1, 1904-11-18, tag, Kirchstraße,    falsch
01838, 2, 1926-06-01, tag, Klosterstraße,  falsch
01838, 3, 1937-11-20, tag, Kütings Garten, falsch
```

Damit lässt sich der Name **zu jedem Stichtag** ableiten — die Straße hieß 1936
„Klosterstraße". Ein Projekt zum Adressbuch 1912 oder 1950 nutzt denselben Datensatz.

### `pruefung.csv`

Einträge, die der Parser nicht sicher erfassen konnte: Buchseite, Rohtext, erkannter
Grund. Eingabemaske für die manuelle Klärung; nach der Korrektur läuft der Parser erneut.

## 5. Publikationsform

```
essener-strassen/
├── README.md              Beschreibung, Methode, bezifferte Qualität, Zitierhinweis
├── LICENSE                CC-BY-4.0 für den eigenen Anteil (Struktur, Code)
├── CITATION.cff           maschinenlesbare Zitierangabe
├── datapackage.json       Frictionless-Schema (Data Dictionary maschinenlesbar)
├── daten/                 strassen.csv, namen.csv, konkordanz_1936.csv
├── code/                  Parser, Validierung, Ableitung
├── docs/                  Spec, Qualitätsbericht, Entscheidungen
└── ocr/                   Arbeitsstand — von der Veröffentlichung ausgeschlossen
```

Veröffentlichung als GitHub-Release, mit Zenodo verknüpft (DOI je Version).

## 6. Schnittstelle zum Kartenprojekt

Das Kartenprojekt übernimmt `konkordanz_1936.csv` als Eingabe. Der bestehende
Wikipedia-Extrakt bleibt zunächst als zweite Quelle erhalten: Wo beide Aussagen treffen,
werden **Widersprüche protokolliert** — sie sind ein Qualitätssignal für beide Seiten.
Dickhoff hat als Primärquelle Vorrang.

## 7. Nicht-Ziele

- Keine Extraktion der Erläuterungstexte in Merkmale (Lebensdaten, Erstbelege) — später
  denkbar, jetzt nicht.
- Keine Geokodierung der Straßen; der Datensatz führt Namen, keine Geometrien.
- Kein durchsuchbares Volltext-PDF zur Weitergabe.
- Keine Änderung an der Pipeline des Kartenprojekts über den Konkordanz-Austausch hinaus.
