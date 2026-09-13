# Differenzbericht

Verglichen wird der Datenstand **vor Parser-Runde 2** (`alt` = Commit `54c5e2a`,
`daten/strassen.csv` und `daten/namen.csv`) mit der **Regeneration nach Runde 2**
(`neu` = dieser Lauf, 13. September 2026). Grundlage sind dieselben OCR-Seiten; verändert
haben sich allein die Parser-Regeln R1–R6 aus
`docs/specs/2026-09-13-parser-runde-2-design.md`:

- **R1** Trennstrich am Zeilenumbruch (`(?<=\w)-\n` → `-`) — behebt `Adolf- Rath-Straße`,
  `Überruhr- Holthausen`.
- **R2** Klammerzusätze normalisieren und abgeschnittene ergänzen (`{tiw.)`, `(Verl`, `(tw`
  → `(tlw.)`, `(Verl.)`); jede *Ergänzung* wird gekennzeichnet (`Klammerzusatz ergänzt`).
- **R3** Großumlaut am Wortanfang (`Agirstraße` → `Ägirstraße`, `Uckendorfer` → `Ückendorfer`).
- **R4** Römischer Ordnungspunkt (`I.`, `II.`, `III.`, `Ill.`) beendet den Lemma-Rückwärtslauf
  nicht mehr — `I. Buschlandweg` bleibt vollständig.
- **R5** Randzeichen vor Kopfwerten (`„ `, `) `, `” `, `nn `) und `; _`-Feldreste entfernen.
- **R6** Anker- und Trenner-Varianten (`Sch}`, `N.`, `-Schl.-Nr.`, `;` statt `:`) tolerieren
  und die Toleranz kennzeichnen (`Anker OCR-korrigiert`).

Annotiert sind — wie in `docs/regression/2026-09-parser-reparatur.md` — **jede** Zeile der
Kategorien „Stadium verloren" (hier: keine) und „Status automatisch → unsicher"
(130 Einzelbefunde) mit einer eingerückten `- Prüfung:`-Zeile, dazu die auffälligen
Einzelfälle in „Kopffeld verändert". Keine Zeile dieser Kategorien bleibt unkommentiert.

**Sollwerte aus Spec Abschnitt 4.2 gegengerechnet:**

| Sollwert | gemessen | Bewertung |
|---|---|---|
| Straßen +9 (R6, neun namentlich genannte Einträge) | **+11** (3.338 → 3.349) | erfüllt und übertroffen: die neun Einträge der Spec (00465, 00710, 01067, 02070, 02086, 02599, 02821, 02834, 03297) sind alle da; 02834 Schulte-Hinsel-Straße erst nach der Nachbesserung der Anker-Regel. Zusätzlich 01729 Kleine Lenbachstraße und 03226 Virgiliastraße, die die Spec nicht vorhergesehen hatte. Kein Eintrag ist entfallen. |
| keine verlorenen Stadien in `automatisch`-Einträgen | **0 verlorene Stadien überhaupt** | erfüllt (Kategorie „Stadium verloren" ist leer, ebenso „Stadium gewonnen" und „Datum verändert" — Runde 2 rührt die Kettenlogik nicht an). |
| Lemma-Dubletten in `pruefung_validierung.csv` −22 (über R4, 24 Lemmata `I./II./III. <Name>`) | **−37 Zeilen** (229 → 192: `nicht im amtlichen Verzeichnis` 160 → 122, `Alphabet` 69 → 70) — aber nur **11 der 24** römischen Lemmata zurückgewonnen | Zahlenwert erfüllt, Mechanismus nur zur Hälfte: der Rückgang von 37 Zeilen stammt überwiegend aus dem Abgleich mit dem amtlichen Verzeichnis (R1/R2 machen Lemmata wieder auffindbar), nicht allein aus R4. R4 greift nur bei `I`, `II`, `III`, `IV`, `Ill`; die OCR-Lesarten `Il.`, `ll.`, `l.`, `1.` bleiben offen — siehe „Offene Grenze von R4" unter „Kopffeld verändert". Nichts davon ist geraten, die Restfälle bleiben sichtbar. |
| `einig=beide` in der Prüfliste unter 250 | **288** (von 712) | **nicht erreicht** — −60 %, aber 38 Zeilen über dem Sollwert; siehe unten. |

**Wirkung auf die Veröffentlichung** (`python3 -m strassen.veroeffentlichen`):
`strassen.csv` 3338 → 3349 Zeilen, `namen.csv` 5457 → 5473, `status`
`automatisch` 3066 → 2973 / `unsicher` 271 → 375 / `geprueft` 1 → 1.
Der Anstieg der `unsicher`-Zahl ist gewollt und keine Regression: 102 der 130
Rückstufungen betreffen Einträge, deren Kopffelder und Namenskette **Zeichen für Zeichen
unverändert** sind — der Parser hat sie schon vorher tolerant gelesen, nur eben still.
Runde 2 macht diese Toleranz sichtbar (precision-first). Die Konkordanz speist sich aus
den belastbaren Einträgen und schrumpft dadurch von 426 auf 406 Paare: 41 Paare fallen weg,
21 kommen hinzu. Von den 41 waren 15 gar keine Umbenennungen, sondern R1-Trennstrichfehler
(`Adolf- Rath-Straße` → `Adolf-Rath-Straße`), weitere 4 abgeschnittene Klammerzusätze
(`Thomaestraße (tiw` → `(tlw.)`) — diese 19 sind ein reiner Gewinn an Genauigkeit. Die
übrigen 22 gehören zu Einträgen, die jetzt `unsicher` sind und daher nicht mehr in die
Konkordanz einfließen (precision-first: lieber weniger Paare als ungeprüfte). Die 21 neuen
Paare stammen aus Einträgen, die von `unsicher` auf `automatisch` aufgestiegen sind.

**Zur Prüfliste:** `einig=beide` (beide Modelle widersprechen dem Parser) fällt von 712 auf
288, die Prüfliste insgesamt von 4317 auf 3585 Zeilen. Der Spec-Sollwert „unter 250" ist
damit **nicht erreicht**; er war eine Schätzung vor Kenntnis der Regelwirkung. Die
verbleibenden 288 Zeilen sind kein bekannter Parser-Fehler, sondern die noch ungesichtete
Restmenge (Namenswörterbuch-Fälle wie `Moitkestraße`, Layout-Zerfall S. 227/280) — sie ist
ausdrücklich Sichtungsarbeit für das Korrektur-Overlay und in den Nicht-Zielen der Spec
(Abschnitt 5) ausgenommen. R7 lässt zusätzlich den jeweils letzten Eintrag einer Buchseite
in der Kettenprüfung aus (nur Kopfvergleich): `seitenende_ausgelassen` = 340 (mistral) bzw.
334 (qwen).

**Nicht aufgetreten:** Der in Runde 2 diskutierte R2-Randfall — ein Name mit unpaariger
Klammer, dem Fließtext folgt, wird vollständig eingeklammert — kommt im regenerierten
Datenstand **nicht** vor: kein Eintrag in „Name verändert" gewinnt eine Klammer, die vorher
gar nicht da war, und `namen.csv` enthält keinen Namen mit eingeklammertem Fließtext
(längster Klammerinhalt: `Kuhstraße (Teil von Borbecker bis Bocholder Straße)`, schl_nr 03440
— schon vor Runde 2 wortgleich so). Der Randfall bleibt als Risiko dokumentiert, hat aber keine Zeile.

| Kategorie | Anzahl |
|---|--:|
| Eintrag neu | 11 |
| Eintrag entfallen | 0 |
| Stadium gewonnen | 0 |
| Stadium verloren | 0 |
| Datum verändert | 0 |
| Name verändert | 379 |
| Kopffeld verändert | 294 |
| Status automatisch → unsicher | 130 |
| Status unsicher → automatisch | 34 |

## Eintrag neu

Elf Einträge, die vor Runde 2 gar nicht erkannt wurden, weil ihr
Schlüsselnummer-Anker OCR-verstümmelt war (R6). Neun davon nennt die Spec namentlich;
01729 Kleine Lenbachstraße und 03226 Virgiliastraße kamen unvorhergesehen hinzu,
02834 Schulte-Hinsel-Straße erst mit der Nachbesserung an der Anker-Regel. Alle elf tragen
den Hinweis `Anker OCR-korrigiert` und damit Status `unsicher`. Entfallen ist kein Eintrag.

- 00465 Brunhildenstraße
- 00710 Am Schloss Schellenberg
- 01067 Graitengraben
- 01729 Kleine Lenbachstraße
- 02070 Malmedystraße
- 02086 Marreweg
- 02599 Riegelweg
- 02821 Schraeplerstraße
- 02834 Schulte-Hinsel-Straße
- 03226 Virgiliastraße
- 03297 Waldblick

## Name verändert

379 Namensstadien, ausnahmslos Schreibkorrekturen an derselben
Stelle der Kette — kein Stadium wechselt Datum oder Position. Aufschlüsselung:
277 Klammerzusätze (R2, `{tiw.)`/`(Verl`/`[tlw.)` → `(tlw.)`/`(Verl.)`), 100 Trennstriche am
Zeilenumbruch (R1, `Adolf- Rath-Straße` → `Adolf-Rath-Straße`) und 2 Großumlaute (R3,
`Agirstraße` → `Ägirstraße`, `Uckendorfer Straße` → `Ückendorfer Straße`). Jede Änderung
verkürzt oder korrigiert eine bekannte OCR-Verstümmelung; keine erfindet Text. Ein Name,
der eine vorher nicht vorhandene Klammer gewinnt, kommt nicht vor (s. oben, R2-Randfall).

- 00008 Ackerstraße — stadium: 3; alt: Ackerstraße (Verl); neu: Ackerstraße (Verl.)
- 00013 Adolf-Rath-Straße — stadium: 1; alt: Adolf- Rath-Straße; neu: Adolf-Rath-Straße
- 00016 Äbtissinsteig — stadium: 1; alt: Knottenberg (tIw); neu: Knottenberg (tlw.)
- 00018 Ägirstraße — stadium: 1; alt: Agirstraße; neu: Ägirstraße
- 00021 Ahnewinkelstraße — stadium: 3; alt: Ahnewinkelstraße (Verl); neu: Ahnewinkelstraße (Verl.)
- 00021 Ahnewinkelstraße — stadium: 5; alt: Ahnewinkelstraße (Verl); neu: Ahnewinkelstraße (Verl.)
- 00033 Alfrediquelle — stadium: 1; alt: Alfredistraße (tiw.); neu: Alfredistraße (tlw.)
- 00035 Alfred-Pott-Weg — stadium: 1; alt: Alfred- Pott-Weg; neu: Alfred-Pott-Weg
- 00050 Altendorfer Straße — stadium: 3; alt: Thomaestraße (tiw; neu: Thomaestraße (tlw.)
- 00050 Altendorfer Straße — stadium: 4; alt: Altendorfer Straße (tw; neu: Altendorfer Straße (tlw.)
- 00050 Altendorfer Straße — stadium: 6; alt: Altendorfer Straße (Verl); neu: Altendorfer Straße (Verl.)
- 00053 Altenessener Straße — stadium: 3; alt: Essen-Horster- Straße; neu: Essen-Horster-Straße
- 00081 Am Glockenberg — stadium: 6; alt: Am Glockenberg (Verl); neu: Am Glockenberg (Verl.)
- 00085 Am Handelshof - Handelshof 1913 KEN U E Weein Am Handelshof — stadium: 3; alt: Am Handelshof (Verl); neu: Am Handelshof (Verl.)
- 00091 Am Herrenbusch — stadium: 1; alt: Sonnenstraße {tlw.); neu: Sonnenstraße (tlw.)
- 00102 Am Krausen Bäumchen — stadium: 3; alt: Am krausen Bäumchen (Verl); neu: Am krausen Bäumchen (Verl.)
- 00134 Am Tann — stadium: 1; alt: Eckbertstraße (tiw.); neu: Eckbertstraße (tlw.)
- 00149 Am Zehnthof — stadium: 4; alt: Am Zehnthof (Verl); neu: Am Zehnthof (Verl.)
- 00187 Ardeystraße — stadium: 1; alt: Schellenbergstraße (tiw.); neu: Schellenbergstraße (tlw.)
- 00189 Arendahls Wiese — stadium: 1; alt: Lohstraße (tiw.); neu: Lohstraße (tlw.)
- 00192 Jacob-Grimm-Straße — stadium: 2; alt: Jacob-Grimm- Straße; neu: Jacob-Grimm-Straße
- 00208 Am Kreyenkrop — stadium: 2; alt: Bedingrader Straße (tiw.); neu: Bedingrader Straße (tlw.)
- 00209 Am Ostpark — stadium: 1; alt: Metzer Straße (tiw.); neu: Metzer Straße (tlw.)
- 00238 ) Am Richtenberg — stadium: 1; alt: Frohnhauser Straße (tIw.); neu: Frohnhauser Straße (tlw.)
- 00252 Alte Raadter Straße — stadium: 1; alt: Raadter Straße (tiw.); neu: Raadter Straße (tlw.)
- 00253 Alte Hatzper Straße — stadium: 2; alt: Hatzper Straße (tIw.); neu: Hatzper Straße (tlw.)
- 00255 Am Uhlenkrug — stadium: 1; alt: Wittekindstraße (tiw.); neu: Wittekindstraße (tlw.)
- 00281 Bamlerstraße — stadium: 3; alt: Berthold-Beitz-Boulevard (tlw; neu: Berthold-Beitz-Boulevard (tlw.)
- 00289 Barkhorstrücken — stadium: 2; alt: Barkhorstrücken (Verl); neu: Barkhorstrücken (Verl.)
- 00291 Barthel-Bruyn-Straße — stadium: 2; alt: Barthel-Bruyn- Straße; neu: Barthel-Bruyn-Straße
- 00315 Beethovenstraße — stadium: 3; alt: Beethovenstraße (Verl); neu: Beethovenstraße (Verl.)
- 00318 Beisenstraße — stadium: 2; alt: Alfred- Schröer-Straße; neu: Alfred-Schröer-Straße
- 00318 Beisenstraße — stadium: 3; alt: Beisenstraße (Verl); neu: Beisenstraße (Verl.)
- 00327 Berenberger Mark — stadium: 1; alt: An der Kluse (tiw.); neu: An der Kluse (tlw.)
- 00331 [sie > °" sr $ Bergheimer Steig — stadium: 1; alt: Fallstraße (tiw.); neu: Fallstraße (tlw.)
- 00342 Berliner Straße — stadium: 1; alt: Falkensteinstraße (tiw.); neu: Falkensteinstraße (tlw.)
- 00350 Bessemerstraße — stadium: 1; alt: Schraeplerstraße (tiw.); neu: Schraeplerstraße (tlw.)
- 00374 Blockstraße — stadium: 2; alt: Blockstraße (verl.); neu: Blockstraße (Verl.)
- 00395 Bonnekampstraße — stadium: 3; alt: Beisenstraße (tiw.); neu: Beisenstraße (tlw.)
- 00395 Bonnekampstraße — stadium: 4; alt: Bonnekampstraße (Verl); neu: Bonnekampstraße (Verl.)
- 00408 Bottroper Straße — stadium: 7; alt: Haus-Horl- Straße; neu: Haus-Horl-Straße
- 00420 Brandstorgasse — stadium: 3; alt: Brandstorgasse (Verl); neu: Brandstorgasse (Verl.)
- 00436 Breidbachweg — stadium: 2; alt: Altenhof Il (tiw.); neu: Altenhof Il (tlw.)
- 00463 Brüninghofer Weg — stadium: 5; alt: Brüninghofer Weg (Verl); neu: Brüninghofer Weg (Verl.)
- 00487 Büttnerstraße — stadium: 2; alt: Altenhof Il (tiw.); neu: Altenhof Il (tlw.)
- 00507 Byfanger Straße — stadium: 1; alt: Oststraße (tiw.); neu: Oststraße (tlw.)
- 00507 Byfanger Straße — stadium: 4; alt: Byfanger Straße (Verl); neu: Byfanger Straße (Verl.)
- 00509 Bergheimer Straße — stadium: 4; alt: Ripshorster Straße (Verl); neu: Ripshorster Straße (Verl.)
- 00515 Benno-Strauß-Straße — stadium: 1; alt: Kruppstraße (tiw.); neu: Kruppstraße (tlw.)
- 00516 Bredeneyer Kreuz — stadium: 2; alt: Frankenstraße (tiw.); neu: Frankenstraße (tlw.)
- 00528 Langenbrahmstraße — stadium: 2; alt: Ursulastraße (tIw.); neu: Ursulastraße (tlw.)
- 00528 Langenbrahmstraße — stadium: 4; alt: Langenbrahmstraße Umb. {tiw); neu: Langenbrahmstraße Umb. (tlw.)
- 00541 Camillo-Sitte-Platz — stadium: 2; alt: Camillo- Sitte-Platz; neu: Camillo-Sitte-Platz
- 00543 Carl-Funke-Straße — stadium: 2; alt: Carl-Funke- Straße; neu: Carl-Funke-Straße
- 00545 Carolus-Magnus-Straße — stadium: 3; alt: Carolus- Magnus-Straße (Verl.); neu: Carolus-Magnus-Straße (Verl.)
- 00561 Charlottenhöhe — stadium: 1; alt: Holteyerberg (tiw.); neu: Holteyerberg (tlw.)
- 00564 Körholzstraße — stadium: 2; alt: Körholzstraße [neue Führung); neu: Körholzstraße (neue Führung)
- 00565 Bochumer Landstraße — stadium: 3; alt: Bochumer Straße {tlw.); neu: Bochumer Straße (tlw.)
- 00566 Gerhard-Stötzel-Straße — stadium: 2; alt: Gerhard-Stötzel- Straße; neu: Gerhard-Stötzel-Straße
- 00571 Daniel-Eckhardt-Straße — stadium: 1; alt: Daniel- Eckhardt-Straße; neu: Daniel-Eckhardt-Straße
- 00572 Karl-Legien-Straße — stadium: 1; alt: Karl-Legien- Straße; neu: Karl-Legien-Straße
- 00574 Am Riehlpark — stadium: 2; alt: Riehlstraße (tlw); neu: Riehlstraße (tlw.)
- 00587 Rindersberger Mühle — stadium: 1; alt: Höseler Weg (tiw.); neu: Höseler Weg (tlw.)
- 00623 Dickmannstraße — stadium: 5; alt: Dickmannstraße (Verl); neu: Dickmannstraße (Verl.)
- 00637 Distelbeckhof — stadium: 1; alt: Emscherstraße {tlw.); neu: Emscherstraße (tlw.)
- 00665 Dahlmannstraße — stadium: 1; alt: Breilsort (tIw.); neu: Breilsort (tlw.)
- 00673 Druschelpfad — stadium: 2; alt: Altenhof II (tiw.); neu: Altenhof II (tlw.)
- 00686 Dorstfelder Straße — stadium: 1; alt: Dortmunder Straße (tiw.); neu: Dortmunder Straße (tlw.)
- 00694 Dumberger Straße — stadium: 3; alt: Dumberger Straße (Verl); neu: Dumberger Straße (Verl.)
- 00697 Heinz-Renner-Platz — stadium: 1; alt: Heinz-Renner- Platz; neu: Heinz-Renner-Platz
- 00708 Fritz-Schupp-Allee — stadium: 1; alt: Fritz-Schupp- Allee; neu: Fritz-Schupp-Allee
- 00719 Martin-Kremmer-Straße — stadium: 1; alt: Martin- Kremmer-Straße; neu: Martin-Kremmer-Straße
- 00722 Eckenbergstraße — stadium: 1; alt: Friedrichstraße (tiw.); neu: Friedrichstraße (tlw.)
- 00766 Elsa-Brändström-Straße — stadium: 2; alt: Elsa- Brändströmstraße; neu: Elsa-Brändströmstraße
- 00810 Ernst-Tengelmann-Ring — stadium: 1; alt: Ernst- Tengelmann-Ring; neu: Ernst-Tengelmann-Ring
- 00821 Hubert-Bollig-Straße — stadium: 1; alt: Hubert-Bollig- Straße; neu: Hubert-Bollig-Straße
- 00834 Hanns-Joachim-Maßner-Weg — stadium: 1; alt: Hannıs- Joachim-Maßner-Weg; neu: Hannıs-Joachim-Maßner-Weg
- 00835 ücke bis Heidhausen zurück zum Bahnhof” Wilhelm-Gefeller-Weg — stadium: 1; alt: Wilhelm- Gefeller-Weg; neu: Wilhelm-Gefeller-Weg
- 00837 Wilhelm-Döllken-Straße — stadium: 1; alt: Wilhelm- Döllken-Straße; neu: Wilhelm-Döllken-Straße
- 00845 Färberweg — stadium: 1; alt: Horststraße (tiw.); neu: Horststraße (tlw.)
- 00863 Fischweiher — stadium: 1; alt: Heinrichstraße (tiw.); neu: Heinrichstraße (tlw.)
- 00868 Flemingweg — stadium: 1; alt: Marthastraße (tw); neu: Marthastraße (tlw.)
- 00886 Forstmannstraße — stadium: 2; alt: Hochstraße (tiw.); neu: Hochstraße (tlw.)
- 00888 Franzenshöhe Frankenstraße — stadium: 1; alt: Steeler Straße (tiw.); neu: Steeler Straße (tlw.)
- 00891 Franziskanerhöhe — stadium: 2; alt: Kapitän-Lehmann-Höhe (Umb)); neu: Kapitän-Lehmann-Höhe (Umb.)
- 00893 Franziskastraße — stadium: 2; alt: Franz-Seldte-Straße {Umb.); neu: Franz-Seldte-Straße (Umb.)
- 00896 Frau-Bertha-Krupp-Straße — stadium: 4; alt: Frau-Berta-Krupp-Straße (Verl); neu: Frau-Berta-Krupp-Straße (Verl.)
- 00903 Heinrich-Lersch-Platz — stadium: 2; alt: Robert- Ley-Platz; neu: Robert-Ley-Platz
- 00904 Heinrich-Lersch-Straße — stadium: 5; alt: Heinrich- Lersch-Straße; neu: Heinrich-Lersch-Straße
- 00910 Fridtjof-Nansen-Straße — stadium: 3; alt: Fridtjof-Nansen- Straße; neu: Fridtjof-Nansen-Straße
- 00915 Friedrich-Ebert-Straße — stadium: 5; alt: Friedrich-Ebert- Straße (Umb.); neu: Friedrich-Ebert-Straße (Umb.)
- 00918 Friedrich-List-Straße — stadium: 2; alt: Friedrich- List-Straße; neu: Friedrich-List-Straße
- 00925 Frillendorfer Straße — stadium: 2; alt: Schimmelstraße (Umb)); neu: Schimmelstraße (Umb.)
- 00925 Frillendorfer Straße — stadium: 5; alt: Frillendorfer Straße (Verl); neu: Frillendorfer Straße (Verl.)
- 00935 Fünffußbank — stadium: 2; alt: Fünffußbank (Verl); neu: Fünffußbank (Verl.)
- 00939 Fürstäbtissinstraße — stadium: 1; alt: Rheinstraße (tiw.); neu: Rheinstraße (tlw.)
- 00943 Fulerumer Straße — stadium: 3; alt: Fulerumer Straße (Verl); neu: Fulerumer Straße (Verl.)
- 00947 Franz-Arens-Straße — stadium: 2; alt: Damannstraße (t!w.); neu: Damannstraße (tlw.)
- 00958 Franz-Voutta-Straße — stadium: 1; alt: Franz-Voutta- Straße; neu: Franz-Voutta-Straße
- 00959 Maria-Weber-Weg — stadium: 1; alt: Maria-Weber- Weg; neu: Maria-Weber-Weg
- 00990 Gasstraße — stadium: 2; alt: Gasstraße (Verl); neu: Gasstraße (Verl.)
- 00996 Gedingeweg — stadium: 4; alt: Gedingeweg (Verl); neu: Gedingeweg (Verl.)
- 01011 Gerhard-Küchen-Straße — stadium: 2; alt: Gerhard-Küchen- Straße; neu: Gerhard-Küchen-Straße
- 01019 Gerscheder Straße — stadium: 4; alt: Gerscheder Straße (Verl); neu: Gerscheder Straße (Verl.)
- 01027 Gewerkenstraße — stadium: 3; alt: Gewerkenstraße (Verl); neu: Gewerkenstraße (Verl.)
- 01038 Gerscheder Weiden — stadium: 2; alt: Weidenstraße (tw); neu: Weidenstraße (tlw.)
- 01040 Gleisdreieck — stadium: 1; alt: Schlägelstraße (tiw.); neu: Schlägelstraße (tlw.)
- 01045 Glühstraße — stadium: 2; alt: Glühstraße (Verl); neu: Glühstraße (Verl.)
- 01046 Gneisenaustraße — stadium: 1; alt: Parkstraße (tiw.); neu: Parkstraße (tlw.)
- 01058 Goldschmidtstraße — stadium: 1; alt: Söllingstraße (tlw); neu: Söllingstraße (tlw.)
- 01063 DEEP BE \ Kr Be [m Graffweg - um 1935 Graf-Bernadotte-Straße — stadium: 3; alt: Graf-Bernadotte- Straße; neu: Graf-Bernadotte-Straße
- 01066 Graf-Spee-Straße — stadium: 3; alt: Graf-Spee- Straße; neu: Graf-Spee-Straße
- 01103 Grugaplatz — stadium: 2; alt: Rudolf-von-Bennigsen- Foerder-Platz (Umb.); neu: Rudolf-von-Bennigsen-Foerder-Platz (Umb.)
- 01112 Gustav-Nachtigal-Straße — stadium: 1; alt: Gustav- Nachtigal-Straße; neu: Gustav-Nachtigal-Straße
- 01113 Gustav-Hicking-Straße — stadium: 2; alt: Gustav-Hicking- Straße; neu: Gustav-Hicking-Straße
- 01114 Gutenbergstraße — stadium: 3; alt: Gutenbergstraße (Verl); neu: Gutenbergstraße (Verl.)
- 01115 Guts-Muths-Weg — stadium: 1; alt: Guts- Muths-Weg; neu: Guts-Muths-Weg
- 01118 Geismarweg — stadium: 2; alt: Zölestinstraße (tIw.); neu: Zölestinstraße (tlw.)
- 01120 Großstraße — stadium: 1; alt: Kruppstraße (tiw.); neu: Kruppstraße (tlw.)
- 01124 Großwesterkamp — stadium: 3; alt: Josef-Hoeren-Straße (tiw.); neu: Josef-Hoeren-Straße (tlw.)
- 01125 a _ Alfred-Herrhausen-Brücke — stadium: 2; alt: Alfred- Herrhausen-Brücke; neu: Alfred-Herrhausen-Brücke
- 01128 Gustav-Streich-Straße — stadium: 1; alt: Gustav- Streich-Straße; neu: Gustav-Streich-Straße
- 01129 Albert-Schmidt-Weg — stadium: 1; alt: Albert-Schmidt- Weg; neu: Albert-Schmidt-Weg
- 01142 Thea-Leymann-Straße — stadium: 1; alt: Thea- Leymann-Straße; neu: Thea-Leymann-Straße
- 01151 Habichtstraße — stadium: 3; alt: Habichtstraße (Verl); neu: Habichtstraße (Verl.)
- 01155 Haedenkampstraße — stadium: 3; alt: Margaretenstraße (tiw.); neu: Margaretenstraße (tlw.)
- 01155 Haedenkampstraße — stadium: 5; alt: Haedenkampstraße (Verl); neu: Haedenkampstraße (Verl.)
- 01178 Hamburger Straße — stadium: 1; alt: Mühlenstraße (tiw.); neu: Mühlenstraße (tlw.)
- 01181 Hammer Straße — stadium: 4; alt: Am Schwarzen (Umb. tiw.); neu: Am Schwarzen (Umb. tlw.)
- 01186 Hansastraße — stadium: 2; alt: Markt (tiw.); neu: Markt (tlw.)
- 01186 Hansastraße — stadium: 4; alt: Hansastraße (Verl); neu: Hansastraße (Verl.)
- 01189 Hans-Luther-Allee — stadium: 3; alt: Hans- Luther-Allee; neu: Hans-Luther-Allee
- 01192 Hardenbergufer — stadium: 1; alt: Hafenstraße {tlw.); neu: Hafenstraße (tlw.)
- 01198 Hartzbeeker Mark — stadium: 1; alt: Rommesweg (tiw.); neu: Rommesweg (tlw.)
- 01207 Hattramstraße — stadium: 3; alt: Hattramstraße (Verl); neu: Hattramstraße (Verl.)
- 01212 Hatzper Bogen — stadium: 2; alt: Hatzper Straße (tiw.); neu: Hatzper Straße (tlw.)
- 01217 Haus Heisingen — stadium: 1; alt: Steinstraße (tiw.); neu: Steinstraße (tlw.)
- 01229 Heegstraße — stadium: 2; alt: Teilstraße(Umb.); neu: Teilstraße (Umb.)
- 01249 August-Schmidt-Straße — stadium: 4; alt: August-Schmidt- Straße; neu: August-Schmidt-Straße
- 01252 Heinrich-Sense-Weg — stadium: 1; alt: Karlstraße {tlw.); neu: Karlstraße (tlw.)
- 01258 Heisterholz — stadium: 4; alt: Heisterholz (Verl); neu: Heisterholz (Verl.)
- 01261 Helenenstraße — stadium: 3; alt: Helenenstraße (Verl); neu: Helenenstraße (Verl.)
- 01266 Helmholtzplatz — stadium: 3; alt: Heinitzstraße (tiw.); neu: Heinitzstraße (tlw.)
- 01272 Hendrik-Witte-Straße — stadium: 2; alt: Hendrik-Witte- Straße; neu: Hendrik-Witte-Straße
- 01275 Henningweg — stadium: 1; alt: Im Siepken [tiw.); neu: Im Siepken (tlw.)
- 01287 Hertzlerstraße — stadium: 1; alt: Nikolausstraße (tiw.); neu: Nikolausstraße (tlw.)
- 01288 Herwarthstraße — stadium: 4; alt: Herwarthstraße {Verl.); neu: Herwarthstraße (Verl.)
- 01305 Hilgerstraße — stadium: 2; alt: Hilgerstraße (Verl); neu: Hilgerstraße (Verl.)
- 01311 Hinsbecker Löh — stadium: 1; alt: Löhstraße (tiw.); neu: Löhstraße (tlw.)
- 01342 Hohe Buchen — stadium: 2; alt: Markuspfad (tiw.); neu: Markuspfad (tlw.)
- 01342 Hohe Buchen — stadium: 3; alt: Hohe Buchen (Verl); neu: Hohe Buchen (Verl.)
- 01376 Hubertweiche — stadium: 1; alt: Essener Straße {tlw.); neu: Essener Straße (tlw.)
- 01378 Huestraße — stadium: 2; alt: Otto-Hue- Straße; neu: Otto-Hue-Straße
- 01384 Heilermannstraße — stadium: 1; alt: Wächtlerstraße (tiw.); neu: Wächtlerstraße (tlw.)
- 01398 Humannstraße — stadium: 2; alt: Karl- Humann-Straße; neu: Karl-Humann-Straße
- 01405 Husemannweg — stadium: 1; alt: Kirchstraße {tlw.); neu: Kirchstraße (tlw.)
- 01409 Huttropstraße — stadium: 4; alt: Herwarthstraße (tIw.); neu: Herwarthstraße (tlw.)
- 01411 Homburger Weg — stadium: 1; alt: Parkweg (tiw.); neu: Parkweg (tlw.)
- 01425 Huckarder Straße — stadium: 1; alt: Dortmunder Straße (tIw.); neu: Dortmunder Straße (tlw.)
- 01431 Holteyer Hang — stadium: 1; alt: Holteyerberg {tiw.); neu: Holteyerberg (tlw.)
- 01439 Helen-Keller-Straße — stadium: 2; alt: Am Kreuz (tw.); neu: Am Kreuz (tlw.)
- 01461 Imbuschweg — stadium: 1; alt: Kirchstraße {tlw.); neu: Kirchstraße (tlw.)
- 01461 Imbuschweg — stadium: 2; alt: Alte Kirchstraße (tiw.); neu: Alte Kirchstraße (tlw.)
- 01501 Im Westerbruch — stadium: 2; alt: Im Westerbruch (Verl; neu: Im Westerbruch (Verl.)
- 01520 Irispfad — stadium: 1; alt: An Lindemanns Kreuz {tlw.); neu: An Lindemanns Kreuz (tlw.)
- 01551 Paul-Reichardt-Straße — stadium: 1; alt: Paul-Reichardt- Straße; neu: Paul-Reichardt-Straße
- 01571 Joachimstraße — stadium: 3; alt: Joachimstraße (Verl); neu: Joachimstraße (Verl.)
- 01576 Johann-Kruse-Straße — stadium: 1; alt: Johann-Kruse- Straße; neu: Johann-Kruse-Straße
- 01580 Joseph-Oertgen-Weg — stadium: 2; alt: Joseph-Oertgen- Weg; neu: Joseph-Oertgen-Weg
- 01582 Johannes-Brokamp-Straße — stadium: 2; alt: Borbecker Straße (tiw.); neu: Borbecker Straße (tlw.)
- 01583 Julienstraße — stadium: 3; alt: Julienstraße (verl.); neu: Julienstraße (Verl.)
- 01585 Jüngstallee — stadium: 1; alt: Altenhof II (tiw.); neu: Altenhof II (tlw.)
- 01590 Joseph-Breuer-Straße — stadium: 4; alt: Joseph-Breuer- Straße; neu: Joseph-Breuer-Straße
- 01591 Jenckestraße — stadium: 1; alt: Kruppstraße (tiw.); neu: Kruppstraße (tlw.)
- 01612 Julius-Hecker-Platz — stadium: 1; alt: Julius- Hecker-Platz; neu: Julius-Hecker-Platz
- 01613 Stephan-Tembories-Ring — stadium: 1; alt: Stephan- Tembories-Ring; neu: Stephan-Tembories-Ring
- 01622 Kaisershofstraße — stadium: 2; alt: Kaiserhofstraße (Verl); neu: Kaiserhofstraße (Verl.)
- 01623 Hannah-Arendt-Straße — stadium: 3; alt: Hannah-Arendt- Straße; neu: Hannah-Arendt-Straße
- 01625 Kaiser-Wilhelm-Platz — stadium: 1; alt: Kaiser- Wilhelm-Platz; neu: Kaiser-Wilhelm-Platz
- 01634 Kamblickweg — stadium: 2; alt: Osterfeld (tIw.); neu: Osterfeld (tlw.)
- 01644 Kaninenberghöhe — stadium: 2; alt: Ahrfeldstraße (tIw.); neu: Ahrfeldstraße (tlw.)
- 01645 Max-Keith-Straße — stadium: 2; alt: Max-Keith- Straße; neu: Max-Keith-Straße
- 01647 Bischof-Franz-Wolf-Straße — stadium: 1; alt: Karl- Peters-Straße; neu: Karl-Peters-Straße
- 01653 Kapitelwiese — stadium: 4; alt: Kapitelwiese (Verl); neu: Kapitelwiese (Verl.)
- 01659 Karl-Meyer-Platz — stadium: 1; alt: Karl- Meyer-Platz; neu: Karl-Meyer-Platz
- 01660 Karl-Meyer-Straße — stadium: 3; alt: Karl- Meyer-Straße; neu: Karl-Meyer-Straße
- 01665 Karnaper Straße — stadium: 1; alt: Essen- Horster-Straße; neu: Essen-Horster-Straße
- 01666 Karolienenstraße — stadium: 3; alt: Vom- Rath-Straße; neu: Vom-Rath-Straße
- 01666 Karolienenstraße — stadium: 4; alt: Vöcklinghauser Straße (tiw.); neu: Vöcklinghauser Straße (tlw.)
- 01667 Karolingerstraße — stadium: 1; alt: Horster Straße (tiw.); neu: Horster Straße (tlw.)
- 01667 Karolingerstraße — stadium: 2; alt: Hundebrinkstraße (tiw.); neu: Hundebrinkstraße (tlw.)
- 01675 Katernberger Straße — stadium: 3; alt: Nienhausener Straße (tiw.); neu: Nienhausener Straße (tlw.)
- 01675 Katernberger Straße — stadium: 4; alt: Katernberger Straße (Verl); neu: Katernberger Straße (Verl.)
- 01684 Kellersohnweg — stadium: 2; alt: Kellersohnweg (Verl); neu: Kellersohnweg (Verl.)
- 01699 Kevelohstraße — stadium: 2; alt: Kevelohstraße (Verl); neu: Kevelohstraße (Verl.)
- 01718 ern von der Heiligen Elisabeth zu Essen-(Schuir) Klarastraße — stadium: 2; alt: Horst- Wessel-Straße (Umb.); neu: Horst-Wessel-Straße (Umb.)
- 01724 Kleine Buschstraße — stadium: 2; alt: Buschstraße (tiw.); neu: Buschstraße (tlw.)
- 01726 Kleine Hammerstraße — stadium: 1; alt: Hammerstraße (tiw.); neu: Hammerstraße (tlw.)
- 01748 Klosterstraße — stadium: 2; alt: Helenenstraße (Umb.}; neu: Helenenstraße (Umb.)
- 01786 Kleine Steubenstraße — stadium: 2; alt: Steubenstraße {tlw.); neu: Steubenstraße (tlw.)
- 01791 Kortwiese — stadium: 2; alt: Korthover Weg (tiw.); neu: Korthover Weg (tlw.)
- 01805 Kraspothstraße — stadium: 2; alt: Grundstraße (tiw.); neu: Grundstraße (tlw.)
- 01861 Kofeldhöhe — stadium: 2; alt: Hunsiepen (tiw.); neu: Hunsiepen (tlw.)
- 01870 Käthe-Kollwitz-Straße — stadium: 3; alt: Käthe-Kollwitz- Straße; neu: Käthe-Kollwitz-Straße
- 01879 Fritz-Niermann-Platz — stadium: 1; alt: Fritz- Niermann-Platz; neu: Fritz-Niermann-Platz
- 01921 Laupendahler Landstraße — stadium: 5; alt: Laupendahler Landstraße (Verl); neu: Laupendahler Landstraße (Verl.)
- 01926 Pa Lazarettstraße — stadium: 2; alt: Lazarettstraße (Verl); neu: Lazarettstraße (Verl.)
- 01950 Lerchenstraße — stadium: 3; alt: General-Ludendorff- Straße (Umb.); neu: General-Ludendorff-Straße (Umb.)
- 01952 Lenaustraße — stadium: 3; alt: Lessingstraße (Verl); neu: Lessingstraße (Verl.)
- 01955 Levinstraße — stadium: 1; alt: Prosperstraße (tIw.); neu: Prosperstraße (tlw.)
- 01968 Lilienstraße — stadium: 4; alt: Lilienstraße {Umb.); neu: Lilienstraße (Umb.)
- 01971 Limbecker Straße — stadium: 2; alt: Limbecker Straße {Verl.); neu: Limbecker Straße (Verl.)
- 01997 Lohwiese — stadium: 2; alt: Ludwig- Knickmann-Straße; neu: Ludwig-Knickmann-Straße
- 02045 Helene-Müller-Weg — stadium: 1; alt: Helene- Müller-Weg; neu: Helene-Müller-Weg
- 02046 Bauer-Knühl-Weg — stadium: 1; alt: Bauer-Knühl- Weg; neu: Bauer-Knühl-Weg
- 02048 Wilhelm-Vogelsang-Weg — stadium: 1; alt: Wilhelm- Vogelsang-Weg; neu: Wilhelm-Vogelsang-Weg
- 02079 Mariengarten — stadium: 4; alt: Mariengarten (Verl); neu: Mariengarten (Verl.)
- 02095 Matthias-Erzberger-Straße — stadium: 5; alt: Matthias- Erzberger-Straße; neu: Matthias-Erzberger-Straße
- 02100 Max-Fiedler-Straße — stadium: 2; alt: Max-Fiedler- Straße; neu: Max-Fiedler-Straße
- 02103 Maybachstraße — stadium: 1; alt: Am Zweihonnschaftenwald {tlw.); neu: Am Zweihonnschaftenwald (tlw.)
- 02105 Mechtenbergstraße — stadium: 3; alt: Mechentenbergstraße (Verl); neu: Mechentenbergstraße (Verl.)
- 02124 Menzelstraße — stadium: 1; alt: Hobeisenstraße (tiw.); neu: Hobeisenstraße (tlw.)
- 02131 Metzendorfstraße — stadium: 1; alt: Hohlweg {tiw.); neu: Hohlweg (tlw.)
- 02133 Mathilde-Kaiser-Straße — stadium: 1; alt: Mathilde- Kaiser-Straße; neu: Mathilde-Kaiser-Straße
- 02137 Middeldorper Weg — stadium: 4; alt: Middeldorper Weg (Verl..; neu: Middeldorper Weg (Verl.)
- 02178 Munscheidstraße — stadium: 3; alt: Munscheidstraße (Verl); neu: Munscheidstraße (Verl.)
- 02180 Meckenstocker Höfe — stadium: 1; alt: Meckenstocker Weg (tiw.); neu: Meckenstocker Weg (tlw.)
- 02188 Möllershus — stadium: 1; alt: Dattenberg (tiw.); neu: Dattenberg (tlw.)
- 02191 Manderscheidtstraße — stadium: 2; alt: Manderscheidtstraße (Verl); neu: Manderscheidtstraße (Verl.)
- 02195 Mölleneystraße — stadium: 4; alt: Mölleneystraße (Verl); neu: Mölleneystraße (Verl.)
- 02234 Neue Heimat — stadium: 2; alt: Neue Heimat (Verl); neu: Neue Heimat (Verl.)
- 02239 Neukircher Mühle — stadium: 1; alt: Hafenstraße (tiw.); neu: Hafenstraße (tlw.)
- 02256 Nienhuser Busch — stadium: 1; alt: Wallstraße (tiw.); neu: Wallstraße (tlw.)
- 02258 Nierenhofer Straße — stadium: 5; alt: Nierenhofer Straße (Verl); neu: Nierenhofer Straße (Verl.)
- 02264 Nöckersberg — stadium: 3; alt: Nöckersberg (Verl); neu: Nöckersberg (Verl.)
- 02266 Nöggerathstraße — stadium: 3; alt: Gartenkamp (tiw.); neu: Gartenkamp (tlw.)
- 02287 Natorpstraße — stadium: 2; alt: Taubenstraße (Verl); neu: Taubenstraße (Verl.)
- 02290 Niebuhrstraße — stadium: 2; alt: Curtiusstraße (t!w.); neu: Curtiusstraße (tlw.)
- 02312 Oberer Pustenberg — stadium: 2; alt: Pustenberg (tiw.); neu: Pustenberg (tlw.)
- 02320 Oberstraße — stadium: 3; alt: Oberstraße (Verl); neu: Oberstraße (Verl.)
- 02326 Oskarstraße — stadium: 2; alt: Otmarstraße (tiw.); neu: Otmarstraße (tlw.)
- 02333 Oslenderstraße — stadium: 1; alt: Hüttenstraße (tiw.); neu: Hüttenstraße (tlw.)
- 02333 Oslenderstraße — stadium: 2; alt: Phönixberg {tiw.); neu: Phönixberg (tlw.)
- 02335 Obere Aue — stadium: 1; alt: Schacht Jacob (tIw.); neu: Schacht Jacob (tlw.)
- 02355 Ostuferstraße — stadium: 2; alt: Ostuferstraße (Verl); neu: Ostuferstraße (Verl.)
- 02388 Paßstraße — stadium: 3; alt: Paßstraße (Verl); neu: Paßstraße (Verl.)
- 02393 Paul-Brandi-Straße — stadium: 2; alt: Paul- Brandi-Straße; neu: Paul-Brandi-Straße
- 02402 Porscheplatz — stadium: 1; alt: Königstraße (tiw.); neu: Königstraße (tlw.)
- 02402 Porscheplatz — stadium: 2; alt: Schwarze Poth (tw); neu: Schwarze Poth (tlw.)
- 02402 Porscheplatz — stadium: 3; alt: Postallee (tiw.); neu: Postallee (tlw.)
- 02436 Pörtingsiepen — stadium: 4; alt: Pötingsiepen (Verl); neu: Pötingsiepen (Verl.)
- 02437 Pollerbecks Brink — stadium: 2; alt: Gartenkamp (tiw.); neu: Gartenkamp (tlw.)
- 02441 Porschekanzel — stadium: 1; alt: Schwarze Poth {tiw.); neu: Schwarze Poth (tlw.)
- 02461 Priemhauser Weg — stadium: 1; alt: Deilmannsweg {nicht amtl.); neu: Deilmannsweg (nicht amtl.)
- 02462 Prinz-Adolf-Straße — stadium: 2; alt: Prinz-Adolf- Straße; neu: Prinz-Adolf-Straße
- 02464 Prinz-Friedrich-Straße — stadium: 2; alt: Prinz-Friedrich- Straße; neu: Prinz-Friedrich-Straße
- 02467 Prosperstraße — stadium: 3; alt: Prosperstraße (Verl); neu: Prosperstraße (Verl.)
- 02474 Paul-Goerens-Straße — stadium: 2; alt: Paul-Goerens- Straße; neu: Paul-Goerens-Straße
- 02475 Platanenweg — stadium: 2; alt: Eschenstraße (tiw.); neu: Eschenstraße (tlw.)
- 02514 Heinrich-Held-Straße — stadium: 1; alt: Heinrich- Held-Straße; neu: Heinrich-Held-Straße
- 02517 Heinz-Bäcker-Straße — stadium: 1; alt: Heinz-Bäcker- Straße; neu: Heinz-Bäcker-Straße
- 02525 Ewald-Dutschke-Straße — stadium: 1; alt: Ewald- Dutschke-Straße; neu: Ewald-Dutschke-Straße
- 02538 Willy-Brandt-Platz — stadium: 1; alt: Willy-Brandt- Platz; neu: Willy-Brandt-Platz
- 02551 Rahmstraße — stadium: 3; alt: Brauerstraße (tiw); neu: Brauerstraße (tlw.)
- 02559 Rauchstraße — stadium: 2; alt: Levinstraße (tiw.); neu: Levinstraße (tlw.)
- 02569 Reckmannshof — stadium: 1; alt: Meckenstocker Weg (tiw.); neu: Meckenstocker Weg (tlw.)
- 02592 Heinrich-Brauns-Straße — stadium: 2; alt: Heinrich- Brauns-Straße; neu: Heinrich-Brauns-Straße
- 02613 Rodberger Straße — stadium: 1; alt: Velberter Straße (tiw.); neu: Velberter Straße (tlw.)
- 02621 Röntgenstraße — stadium: 3; alt: Marschallstraße (tlw; neu: Marschallstraße (tlw.)
- 02632 Rosastraße — stadium: 2; alt: Rosastraße (Verl; neu: Rosastraße (Verl.)
- 02636 Rotemühle — stadium: 2; alt: Rotemühle (tiw.); neu: Rotemühle (tlw.)
- 02641 Rubensstraße — stadium: 1; alt: Herwartstraße (tiw.); neu: Herwartstraße (tlw.)
- 02653 Rüstermark — stadium: 2; alt: Drosselstraße (tiw.); neu: Drosselstraße (tlw.)
- 02656 Rüttenscheider Straße — stadium: 5; alt: Hermann-Göring-Straße (Umb; neu: Hermann-Göring-Straße (Umb.)
- 02658 Ruhrallee — stadium: 3; alt: Ruhrallee (Verl); neu: Ruhrallee (Verl.)
- 02662 Ruhrglasstraße — stadium: 2; alt: Gemperwiese (tlw.}; neu: Gemperwiese (tlw.)
- 02688 Rossenrayweg — stadium: 1; alt: Wolfsbankring (tiw.); neu: Wolfsbankring (tlw.)
- 02717 Sachsenring — stadium: 2; alt: Beckmannstraße (tiw.); neu: Beckmannstraße (tlw.)
- 02723 Sammelband — stadium: 1; alt: H-Straße (tiw.); neu: H-Straße (tlw.)
- 02727 St. Annental — stadium: 2; alt: Walpurgisstraße (tiw.); neu: Walpurgisstraße (tlw.)
- 02741 Schalker Straße — stadium: 1; alt: HeBlerstraße (tIw.); neu: HeBlerstraße (tlw.)
- 02745 Scharpenhang — stadium: 3; alt: Scharpenhang (Verl); neu: Scharpenhang (Verl.)
- 02757 Scheppener Weg — stadium: 3; alt: Scheppener Weg (Verl); neu: Scheppener Weg (Verl.)
- 02766 Bert-Brecht-Straße — stadium: 2; alt: Bert-Brecht- Straße; neu: Bert-Brecht-Straße
- 02783 Schloßstraße — stadium: 3; alt: Schloßstraße (Verl); neu: Schloßstraße (Verl.)
- 02807 Schöllerskampstraße — stadium: 3; alt: Schöllerskampstraße (Verl); neu: Schöllerskampstraße (Verl.)
- 02837 Schulte-Pelkum-Straße — stadium: 2; alt: Schulte-Pelkum- Straße; neu: Schulte-Pelkum-Straße
- 02844 Schwanhildenhöhe — stadium: 1; alt: Kirchberg (tiw.); neu: Kirchberg (tlw.)
- 02847 Schwarze Horn — stadium: 3; alt: II. Hagen (tlw; neu: II. Hagen (tlw.)
- 02848 Schwarze-Lenen-Weg — stadium: 1; alt: Schwarze-Lenen- Straße; neu: Schwarze-Lenen-Straße
- 02852 Schweriner Straße — stadium: 5; alt: Schweriner Straße (Verl); neu: Schweriner Straße (Verl.)
- 02856 Segerothstraße — stadium: 2; alt: Heinrich-Unger-Straße (Umb)); neu: Heinrich-Unger-Straße (Umb.)
- 02868 Sevenarstraße — stadium: 1; alt: Kampstraße (tiw.); neu: Kampstraße (tlw.)
- 02879 Siepenblick — stadium: 1; alt: Thingstraße (tiw.); neu: Thingstraße (tlw.)
- 02924 Stahlstraße — stadium: 4; alt: Stahlstraße (Verl); neu: Stahlstraße (Verl.)
- 02940 Steinbrink — stadium: 1; alt: Wolfsbankstraße (tiw.); neu: Wolfsbankstraße (tlw.)
- 02974 Stoppenberger Straße — stadium: 2; alt: Lützowstraße (tiw; neu: Lützowstraße (tlw.)
- 02996 Sulzbachtal — stadium: 2; alt: Lahnbeckestraße (tiw.); neu: Lahnbeckestraße (tlw.)
- 02997 Sundernholz — stadium: 1; alt: Riesweg {tlw.); neu: Riesweg (tlw.)
- 03015 Stenkamps Busch — stadium: 1; alt: Hagedornstraße (tiw.); neu: Hagedornstraße (tlw.)
- 03016 Stensbeckhof — stadium: 1; alt: Moosstraße (tiw.); neu: Moosstraße (tlw.)
- 03021 Sylviastraße — stadium: 1; alt: Rosastraße (tiw.); neu: Rosastraße (tlw.)
- 03029 Schwarzensteinweg — stadium: 1; alt: In den Höfen (tiw.); neu: In den Höfen (tlw.)
- 03035 ne eh Schloßstraße - Wasserschloss Borbeck Schliemannstraße — stadium: 1; alt: Kerckhoffstraße {tlw.); neu: Kerckhoffstraße (tlw.)
- 03048 Tauweg — stadium: 2; alt: Rahmannstraße (tIw.); neu: Rahmannstraße (tlw.)
- 03052 Teisselstraße — stadium: 2; alt: Teisselstraße (Verl); neu: Teisselstraße (Verl.)
- 03070 Thusneldaplatz — stadium: 2; alt: Thusneldaplatz (tiw.); neu: Thusneldaplatz (tlw.)
- 03071 Tholstraße - Hof Thol Thusneldastraße — stadium: 1; alt: Am Goetheplatz (tiw.); neu: Am Goetheplatz (tlw.)
- 03080 Töpferstraße — stadium: 3; alt: Töpferstraße (Verl); neu: Töpferstraße (Verl.)
- 03103 Twentmannstraße — stadium: 5; alt: Twentmannstraße (Verl); neu: Twentmannstraße (Verl.)
- 03108 Theodor-Althoff-Straße — stadium: 2; alt: Beckmannsbusch (tw); neu: Beckmannsbusch (tlw.)
- 03114 Ten-Hövel-Weg — stadium: 1; alt: Ten- Hövel-Weg; neu: Ten-Hövel-Weg
- 03140 Überruhrstraße — stadium: 4; alt: Überruhrstraße (Verl); neu: Überruhrstraße (Verl.)
- 03141 Ulmengarten — stadium: 1; alt: Ulmenhof (tIw.); neu: Ulmenhof (tlw.)
- 03142 Ückendorfer Straße — stadium: 2; alt: Uckendorfer Straße; neu: Ückendorfer Straße
- 03164 Ulmenhang — stadium: 1; alt: Ulmenhof (tiw.); neu: Ulmenhof (tlw.)
- 03210 Verreshöhe — stadium: 2; alt: Altenhof II (tiw.); neu: Altenhof II (tlw.)
- 03228 Vöcklinghauser Straße — stadium: 1; alt: Karolinenstraße (tiw.); neu: Karolinenstraße (tlw.)
- 03234 Volksgartenweg — stadium: 2; alt: Rosenstraße (tiw.); neu: Rosenstraße (tlw.)
- 03237 Von-Bergmann-Straße — stadium: 1; alt: Grabenstraße (tiw.); neu: Grabenstraße (tlw.)
- 03238 Von-Bodenhausen-Weg — stadium: 2; alt: Altenhof II (tiw.); neu: Altenhof II (tlw.)
- 03240 i & KEN wre Vondernstraße - Haus Vondern Von-der-Tann-Straße — stadium: 1; alt: Von-der-Tann- Straße; neu: Von-der-Tann-Straße
- 03245 Von-Schmoller-Straße — stadium: 1; alt: Von- Schmoller-Straße; neu: Von-Schmoller-Straße
- 03247 Vorrathstraße — stadium: 1; alt: Eiserne Hand (tiw.); neu: Eiserne Hand (tlw.)
- 03254 Vryburg — stadium: 1; alt: Horststraße (tiw.); neu: Horststraße (tlw.)
- 03280 Maria-Berns-Straße — stadium: 1; alt: Maria- Berns-Straße; neu: Maria-Berns-Straße
- 03281 Clemens-Schmeck-Straße — stadium: 1; alt: Clemens- Schmeck-Straße; neu: Clemens-Schmeck-Straße
- 03282 Matthias-Lambertz-Weg — stadium: 1; alt: Matthias- Lambertz-Weg; neu: Matthias-Lambertz-Weg
- 03286 Martin-Vollmar-Straße — stadium: 1; alt: ) Graßmannstraße (tiw.); neu: ) Graßmannstraße (tlw.)
- 03287 Flandernstraße — stadium: 1; alt: Zinkstraße (tiw.); neu: Zinkstraße (tlw.)
- 03309 Wallstraße — stadium: 2; alt: Wallstraße (Verl); neu: Wallstraße (Verl.)
- 03312 Walter-Sachsse-Weg — stadium: 3; alt: Walter- Sachsse-Weg; neu: Walter-Sachsse-Weg
- 03333 Wehnertweg — stadium: 2; alt: Altenhof II (tiw.); neu: Altenhof II (tlw.)
- 03339 Weidkamp — stadium: 2; alt: Niederstraße (tIw.); neu: Niederstraße (tlw.)
- 03355 Werner-Viebig-Weg — stadium: 2; alt: Werner-Viebig- Weg; neu: Werner-Viebig-Weg
- 03359 Weserstraße — stadium: 3; alt: Joseph-Hommer-Weg (Umb; neu: Joseph-Hommer-Weg (Umb.)
- 03369 Westerwaldstraße — stadium: 1; alt: Meckenstocker Weg {tiw.); neu: Meckenstocker Weg (tlw.)
- 03369 Westerwaldstraße — stadium: 3; alt: Westerwaldstraße (Verl); neu: Westerwaldstraße (Verl.)
- 03370 Westfalenstraße — stadium: 4; alt: Westfalenstraße (Verl); neu: Westfalenstraße (Verl.)
- 03375 Wichteltal — stadium: 1; alt: Charlottenweg (tiw.); neu: Charlottenweg (tlw.)
- 03420 Wittenbergstraße — stadium: 2; alt: Veronikastraße (tiw.); neu: Veronikastraße (tlw.)
- 03420 Wittenbergstraße — stadium: 4; alt: Ortrudstraße (tiw.); neu: Ortrudstraße (tlw.)
- 03424 Wöhlerstraße — stadium: 1; alt: Hobeisenstraße (tw); neu: Hobeisenstraße (tlw.)
- 03432 Wolfsbankstraße — stadium: 5; alt: Carl-Funke- Straße; neu: Carl-Funke-Straße
- 03432 Wolfsbankstraße — stadium: 7; alt: Wolfsbankstraße (Verl); neu: Wolfsbankstraße (Verl.)
- 03440 Wüstenhöferstraße — stadium: 3; alt: Buschstraße (tiw.); neu: Buschstraße (tlw.)
- 03442 Wuppertaler Straße — stadium: 4; alt: Sartoriusstraße (tiw.); neu: Sartoriusstraße (tlw.)
- 03444 Walter-Hohmann-Straße — stadium: 2; alt: Walter- Hohmann-Straße; neu: Walter-Hohmann-Straße
- 03455 Wilhelm-Melchert-Straße — stadium: 1; alt: Wilhelm- Melchert-Straße; neu: Wilhelm-Melchert-Straße
- 03459 Wilhelm-Segerath-Straße — stadium: 1; alt: Wilhelm- Segerath-Straße; neu: Wilhelm-Segerath-Straße
- 03492 Zeche Eiberg — stadium: 1; alt: Kirchpfad {tiw.); neu: Kirchpfad (tlw.)
- 03493 208 ff Zeche Ernestine — stadium: 1; alt: Zechenstraße (tiw.); neu: Zechenstraße (tlw.)
- 03504 Zimmermannstraße — stadium: 3; alt: Zimmermannstraße (Verl); neu: Zimmermannstraße (Verl.)
- 03530 Zweihonnschaftenwald — stadium: 1; alt: Am Zweihonnschaftenwald {tiw.); neu: Am Zweihonnschaftenwald (tlw.)
- 03532 Zwölfling — stadium: 3; alt: Zwölfling (Verl); neu: Zwölfling (Verl.)
- 03533 Zindelstraße — stadium: 1; alt: Kaupenstraße (tiw.); neu: Kaupenstraße (tlw.)
- 03560 An der Schlucht — stadium: 1; alt: Schacht-Kronprinz-Straße (tiw.); neu: Schacht-Kronprinz-Straße (tlw.)
- 03564 An der Düsterbeck — stadium: 1; alt: Aufm Rolland {tlw.); neu: Aufm Rolland (tlw.)
- 03601 Am Bilstein — stadium: 3; alt: Hochstraße (tiw.); neu: Hochstraße (tlw.)
- 03603 Am Hammershöfchen — stadium: 2; alt: Icktener Siedlung (t!w.); neu: Icktener Siedlung (tlw.)
- 03653 Finkenweg — stadium: 1; alt: Dietrich- Eckart-Siedlung; neu: Dietrich-Eckart-Siedlung
- 03653 Finkenweg — stadium: 2; alt: Icktener Siedlung (tiw.); neu: Icktener Siedlung (tlw.)
- 03656 Freiligrathstraße — stadium: 2; alt: Karlstraße (tIw; neu: Karlstraße (tlw.)
- 03663 Graf-Zeppelin-Straße — stadium: 3; alt: Graf-Zeppelin- Straße; neu: Graf-Zeppelin-Straße
- 03670 Hauptstraße — stadium: 3; alt: Bahnhofstraße {tiw; neu: Bahnhofstraße (tlw.)
- 03670 Hauptstraße — stadium: 8; alt: Hauptstraße (Verl); neu: Hauptstraße (Verl.)
- 03670 Hauptstraße — stadium: 9; alt: Hauptstraße (Verl); neu: Hauptstraße (Verl.)
- 03680 Hopmannplatz — stadium: 1; alt: Bürgermeister- Hopmannn-Platz; neu: Bürgermeister-Hopmannn-Platz
- 03733 Oberlehberg — stadium: 1; alt: Alte Straße {tiw.); neu: Alte Straße (tlw.)
- 03736 Prälatenweg — stadium: 2; alt: Hochstraße (tiw.); neu: Hochstraße (tlw.)
- 03738 Rheinstraße — stadium: 1; alt: Alte Straße (tiw.); neu: Alte Straße (tlw.)
- 03740 Ringstraße — stadium: 3; alt: Johann- Wilhelm-Scheidt-Straße; neu: Johann-Wilhelm-Scheidt-Straße
- 03740 Ringstraße — stadium: 6; alt: Ringstraße (Verl); neu: Ringstraße (Verl.)
- 03743 Ruhrstraße — stadium: 2; alt: Essener Straße [tiw.); neu: Essener Straße (tlw.)
- 03747 Schmachtenbergstraße — stadium: 2; alt: Hindenburgstraße {Umb.); neu: Hindenburgstraße (Umb.)
- 03747 Schmachtenbergstraße — stadium: 3; alt: Schmachtenberstraße (Umb); neu: Schmachtenberstraße (Umb.)
- 03747 Schmachtenbergstraße — stadium: 4; alt: Schmachtenbergstraße (Verl); neu: Schmachtenbergstraße (Verl.)
- 03748 Schulstraße — stadium: 2; alt: Langemarckstraße (Umb; neu: Langemarckstraße (Umb.)
- 03757 Theodor-Fontane-Weg — stadium: 1; alt: Theodor- Fontane-Weg; neu: Theodor-Fontane-Weg

## Kopffeld verändert

294 Kopfwerte: 204 `stadtteile` und 60 `namensgruppe` sind
Trennstrich-Reparaturen (R1, `Überruhr- Holthausen` → `Überruhr-Holthausen`), 4
`verweis_auf` ebenso, 1 `strassenklasse` eine R5-Randzeichenentfernung
(`„ Gemeindestraße`). Von den 25 Lemma-Änderungen sind 11 Randzeichenentfernungen (R5:
`) Am Richtenberg`, `nn Hattenheimer Straße`, `” Emscherstraße` …), 11 wiedergewonnene
römische Ordnungspunkte (R4: `Buschlandweg` → `I. Buschlandweg`, `Ruschenfeld` →
`Ill. Ruschenfeld` — die Fälle, deren Lemma-Dubletten in `pruefung_validierung.csv`
dadurch verschwinden), 1 Trennstrich-Reparatur (`Helmholtz- Heiligenhauser Straße`) und
2 R4-Nebenwirkungen, die unten einzeln geprüft sind.

**Offene Grenze von R4:** die Spec erwartete 24 solcher Lemmata, zurückgewonnen sind 11.
Grund ist die OCR-Lesart: `II.` erscheint im Seitentext überwiegend als `Il.` oder `ll.`,
`I.` als `l.` oder `1.` (S. 93 `Il. Dellbrügge`, S. 289 `l. Schichtstraße`,
S. 294 `ll. Schockenhecke`, S. 315 `II. Stiege`). R4 deckt nur `I`, `II`, `III`, `IV`
und `Ill` ab; die Kleinbuchstaben-Lesarten bleiben unbehandelt und damit weiter als
Dublette sichtbar — bewusst nicht geraten, sondern gekennzeichnet.

- 00004 se Da Achternbergstraße - Haus Achternberg Achtermbergbredde — feld: lemma; alt: se Da Achternbergstraße - Haus Achternberg Achtermbergbredde; neu: Da Achternbergstraße - Haus Achternberg Achtermbergbredde
- 00010 Adelkampstraße — feld: strassenklasse; alt: „ Gemeindestraße; neu: Gemeindestraße
  - Prüfung: R5 wie vorgesehen — das führende Anführungszeichen ist ein Randartefakt des Scans, der Rest beginnt mit Großbuchstaben. Wert jetzt korrekt; der Hinweis `Randzeichen entfernt` stuft den Eintrag vorsichtshalber auf `unsicher`.
- 00016 Äbtissinsteig — feld: namensgruppe; alt: Person, Frau, Deutsche, Abtissin; neu: Person, Frau, Deutsche, Äbtissin
- 00026 Akstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Bergbau; neu: Essener Geschichte und Örtlichkeit, Bergbau
- 00054 Alte Zeilen — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 00055 Altmeyerstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 00087 Am Hauptbahnhof — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 00104 Am Kringel — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00124 Am Schlagbaum — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00132 Am Stift — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 00145 Am Weusthof — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 00155 ” An der Braut — feld: lemma; alt: ” An der Braut; neu: An der Braut
- 00164 Am Ehrenmal — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00172 An St. Hedwig — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00174 An St. Immakulata — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00176 An St. Quintin — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Kirche und Kloster; neu: Essener Geschichte und Örtlichkeit, Kirche und Kloster
- 00183 Antropstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 00207 ia Auf dem Sutan — feld: lemma; alt: ia Auf dem Sutan; neu: I. ia Auf dem Sutan
- 00233 Auf'm Rolland — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00238 ) Am Richtenberg — feld: lemma; alt: ) Am Richtenberg; neu: Am Richtenberg
- 00254 An den Quellen — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00281 Bamlerstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00284 Barbarakirchgang — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Kirche und Kloster; neu: Essener Geschichte und Örtlichkeit, Kirche und Kloster
- 00294 Basunestraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00301 Bausemshorst — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00354 Beuststraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Bergbau; neu: Essener Geschichte und Örtlichkeit, Bergbau
- 00363 Billsteinweg — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00367 Bischoffstraße — feld: stadtteile; alt: Altenessen- Nord; Süd; neu: Altenessen-Nord; Süd
- 00383 Böcklinstraße — feld: namensgruppe; alt: Person, Mann, Schweizer, Maler, Zeichner, Grafiker, Bildhauer, Malerviertel- Holsterhausen; neu: Person, Mann, Schweizer, Maler, Zeichner, Grafiker, Bildhauer, Malerviertel-Holsterhausen
- 00384 Böhmerheide — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00399 Borbecker Platz — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00400 Borbecker Straße — feld: stadtteile; alt: Borbeck- Mitte; Bochold; neu: Borbeck-Mitte; Bochold
- 00452 Brockhoffstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00476 Bückmannshof — feld: stadtteile; alt: Altenessen- Nord; Altenessen-Süd; neu: Altenessen-Nord; Altenessen-Süd
- 00477 Bückmannsmühle — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00481 Bürgerstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00489 Bulkersteig — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00502 Buschlandweg — feld: lemma; alt: Buschlandweg; neu: I. Buschlandweg
- 00518 Bramsfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00554 Hans-Thoma-Straße — feld: namensgruppe; alt: Person, Mann, Deutscher, Maler, Graphiker, Malerviertel- Holsterhausen; neu: Person, Mann, Deutscher, Maler, Graphiker, Malerviertel-Holsterhausen
- 00575 Gewalterberg — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 00601 Dandermannsteg — feld: lemma; alt: Dandermannsteg; neu: Zur ehemaligen Zeche Eintracht II. Dandermannsteg
  - Prüfung: Angenommene Nebenwirkung von R4 (S. 91). Weil der Ordnungspunkt in „Zeche Eintracht II." nicht mehr als Satzende zählt, läuft die Lemma-Rückwärtssuche über den Satz hinaus und nimmt „Zur ehemaligen Zeche Eintracht II." mit. `_lemma_auffaellig` erkennt die Überlänge, der Eintrag steht auf `unsicher` — gekennzeichnet statt still falsch. Namenskette (Dandermannsteg) und Kopffelder sind korrekt; der Preis dafür sind die zehn zurückgewonnenen `I./Ill. <Name>`-Lemmata.
- 00610 Deinghaushöhe — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00615 Dellmannsfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00616 Dellmannsweg — feld: stadtteile; alt: Überruhr- Holthausen; Burgaltendorf; neu: Überruhr-Holthausen; Burgaltendorf
- 00621 De-Wolff-Straße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00625 Diechmannplatz — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00634 Dionysiuskirchplatz — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00663 Drogandstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00718 Siebrechtweg — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00731 Ehrenzeller Platz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Hofname, Platz; neu: Essener Geschichte und Örtlichkeit, Hofname, Platz
- 00739 Eickwinkelstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00743 Eigenstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 00763 Ellernstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 00765 Elsa-Brändström-Platz — feld: verweis_auf; alt: Elsa- Brändström-Straße; neu: Elsa-Brändström-Straße
- 00775 ” Emscherstraße — feld: lemma; alt: ” Emscherstraße; neu: Emscherstraße
- 00775 ” Emscherstraße — feld: stadtteile; alt: Altenessen- Nord; Katernberg; neu: Altenessen-Nord; Katernberg
- 00778 Engelbertstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Geistlicher, Männlicher Vorname, Essener Geschichte und Ortlichkeit; neu: Person, Mann, Deutscher, Geistlicher, Männlicher Vorname, Essener Geschichte und Örtlichkeit
- 00785 Erbenbank — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00786 Erbslöhstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00787 Erdwegstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Pfarrer, Essener Geschichte und Ortlichkeit; neu: Person, Mann, Deutscher, Pfarrer, Essener Geschichte und Örtlichkeit
- 00816 Eskensfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00852 Feldmannhof — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 00865 Flakerfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00866 Flakering - Ehemaliger Hof Flake 1970 Flakering — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 00872 Fließstraße — feld: lemma; alt: Fließstraße; neu: I. Fließstraße
- 00935 Fünffußbank — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00937 Fünfhöfestraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 00939 Fürstäbtissinstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00939 Fürstäbtissinstraße — feld: namensgruppe; alt: Person, Frau, Deutsche, Abtissin; neu: Person, Frau, Deutsche, Äbtissin
- 00941 Fürstinstraße — feld: namensgruppe; alt: Person, Frau, Deutsche, Prinzessin, Abtissin; neu: Person, Frau, Deutsche, Prinzessin, Äbtissin
- 00944 Fundlandstraße — feld: stadtteile; alt: Altenessen- Süd; Katernberg; neu: Altenessen-Süd; Katernberg
- 00964 Peter-Reise-Weg — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00965 Heimbachweg — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 00974 Prinz-Friedrich-Platz — feld: verweis_auf; alt: Prinz- Friedrich-Straße; neu: Prinz-Friedrich-Straße
- 00981 Gänsemarkt — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 00989 Pausstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Hofname; neu: Essener Geschichte und Örtlichkeit, Hofname
- 01015 Gerlingplatz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Platz, (nicht amtlich): Gerlingswiese; neu: Essener Geschichte und Örtlichkeit, Platz, (nicht amtlich): Gerlingswiese
- 01016 Gerlingstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01027 Gewerkenstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01030 Gildehofstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01037 Gladbecker Straße — feld: stadtteile; alt: Stadtkern; Nordviertel; Altenessen-Süd; Altenessen- Nord; Vogelheim; Karnap; neu: Stadtkern; Nordviertel; Altenessen-Süd; Altenessen-Nord; Vogelheim; Karnap
- 01042 Glockenstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01045 Glühstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01059 Goosestraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01064 Grafenstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01080 Grenzgraben — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01085 Grimbartweg — feld: verweis_auf; alt: Reineke-Fuchs- Straße; neu: Reineke-Fuchs-Straße
- 01130 Am Lichtbogen — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01131 Tenderweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01132 Zur Schmiede — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01133 Gießereiweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01148 una Hans-Fehr-Allee — feld: lemma; alt: una Hans-Fehr-Allee; neu: Hans-Fehr-Allee
- 01161 Hagen — feld: lemma; alt: Hagen; neu: I. Hagen
- 01161 Hagen — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01169 Halbachstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01172 Halfmannwiese — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01204 nn Hattenheimer Straße — feld: lemma; alt: nn Hattenheimer Straße; neu: Hattenheimer Straße
- 01209 Hauerstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01213 Hausackerstraße — feld: namensgruppe; alt: Essen Geschichte und Ortlichkeit, Lage-bezeichnung; neu: Essen Geschichte und Örtlichkeit, Lage-bezeichnung
- 01218 un Haus-Horl-Straße — feld: lemma; alt: un Haus-Horl-Straße; neu: Haus-Horl-Straße
- 01233 Hegerkamp — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01269 Hemmerhof — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01282 25ff Hermannstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Essener Geschichte und Ortlichkeit; neu: Person, Mann, Deutscher, Essener Geschichte und Örtlichkeit
- 01283 Herrenbank — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01294 Heßlerstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01309 Hinderfeldsberg — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01341 Hofterbergstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01344 Hohe Haar — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01345 Hohe Kuppe — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01357 Hollestraße — feld: stadtteile; alt: Stadtkern; Östviertel; neu: Stadtkern; Ostviertel
- 01362 Holthuser Tal — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01363 Holtkämperheide — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01365 Holzschragen — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01366 Holzstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01368 Honnerskamp — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01372 Hortmannweg — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01373 Hospitalstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01381 Hülscherfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01385 Hülsmannstraße — feld: stadtteile; alt: Borbeck- Mitte; Gerschede; neu: Borbeck-Mitte; Gerschede
- 01385 Hülsmannstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01401 Hundebrinkstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01414 Hinseler Feld — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01423 Hossemsgarten — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01434 Hautkappenweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01442 Hattingsaue — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01443 Helenendamm — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01465 Im Erlenbruch — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01483 e PEREHERRANEEE Im Natt - Kotten im Natt 1970 Im Lindenstück — feld: lemma; alt: e PEREHERRANEEE Im Natt - Kotten im Natt 1970 Im Lindenstück; neu: PEREHERRANEEE Im Natt - Kotten im Natt 1970 Im Lindenstück
- 01494 Im Schollbrauk — feld: stadtteile; alt: Altenessen- Süd; Stoppenberg; neu: Altenessen-Süd; Stoppenberg
- 01587 Jupiterstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01589 Janstweg — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01605 Loewensteinstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01620 Kahrstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01638 Kämmereihude — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01654 Kappenbergstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01663 Karlstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01673 Siehe Kastellplatz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Platz; neu: Essener Geschichte und Örtlichkeit, Platz
- 01684 Kellersohnweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01687 Kelserweg — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01695 Kessingstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01696 Kettelerstraße — feld: stadtteile; alt: Borbeck- Mitte; Bochold; neu: Borbeck-Mitte; Bochold
- 01697 Kettwiger Straße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01699 Kevelohstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01708 Kinßfeldtstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01717 Klapperstraße — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01733 Kleiner Zuschlag — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01747 Klopstockstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01773 Kohlbergstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01781 Kolpingstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01796 Krablerstraße — feld: stadtteile; alt: Alten-essen- Süd; Vogelheim; neu: Alten-essen-Süd; Vogelheim
- 01823 Krümmgensfeld — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01824 Krummecke — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01832 Kühnholdstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 01841 Kuhlhoffstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 01846 Kunzestraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01856 Kevelohbusch — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01858 Krummeckweg — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01865 Kuhlmannsfeld — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 01866 Kreuzeskirchstraße — feld: namensgruppe; alt: Essener Gesichte und Ortlichkeit; neu: Essener Gesichte und Örtlichkeit
- 01891 Ladenspelderstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Maler, Kupferstecher, Malerviertel- Holsterhausen; neu: Person, Mann, Deutscher, Maler, Kupferstecher, Malerviertel-Holsterhausen
- 01899 Lanfermannfähre — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01915 Liebrechtstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01918 Laubrockweg — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 01929 Lehmanns Brink — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 01934 Leimgardtsfeld — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 01949 Lepsiusweg — feld: namensgruppe; alt: Person, Mann, Deutscher, Agyptologe, Sprachforscher, Bibliothekar; neu: Person, Mann, Deutscher, Ägyptologe, Sprachforscher, Bibliothekar
- 01963 Lierfeldstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 01970 Limbecker Platz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Platz; neu: Essener Geschichte und Örtlichkeit, Platz
- 01971 Limbecker Straße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 01977 Lindnerplatz — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02027 Luppostraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 02035 Leipoldtstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02042 Lunkegarten — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 02051 Treidelplatz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02084 Markt — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02102 Maxstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Kaufmann, Essener Geschichte und Ortlichkeit; neu: Person, Mann, Deutscher, Kaufmann, Essener Geschichte und Örtlichkeit
- 02112 Meinertstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02122 Mentingsbank — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 02134 Mevissenstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02150 Mönkhoffstraße — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 02154 Mövenstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02182 Mönkhoffs Busch — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 02184 Merkurstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 02220 Naatlandstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Flurname; neu: Essener Geschichte und Örtlichkeit, Flurname
- 02222 Nagelstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02245 Neulengrund - Neulenhof Neuweselstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02251 Niederstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02253 Niegischstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02268 Nootstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02274 Nordsternstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02282 Neptunstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 02311 et Obere Fuhr — feld: lemma; alt: et Obere Fuhr; neu: Obere Fuhr
- 02316 Oberholzweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02318 Oberscheidtstraße — feld: lemma; alt: Oberscheidtstraße; neu: e sowie Generaladjutant Kaiser Wilhelms I. Oberscheidtstraße
  - Prüfung: Dieselbe R4-Nebenwirkung (S. 251): „Kaiser Wilhelms I." beendet den Satz nicht mehr, der Rest „e sowie Generaladjutant Kaiser Wilhelms I." landet im Lemma. Form und Länge sind auffällig, der Eintrag ist `unsicher` (zusätzlich `Anker OCR-korrigiert`). Namenskette Bülowstraße → Oberscheidtstraße unverändert und richtig. Beide Fälle sind Kandidaten für das Korrektur-Overlay `daten/korrekturen.csv`.
- 02349 Overbeckstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Maler, Zeichner, Illustrator, Malerviertel- Holsterhausen; neu: Person, Mann, Deutscher, Maler, Zeichner, Illustrator, Malerviertel-Holsterhausen
- 02381 Palmbuschweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02387 Pasbachstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02401 Peanstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02419 Philippstraße — feld: stadtteile; alt: Altenessen- Süd; Stoppenberg; neu: Altenessen-Süd; Stoppenberg
- 02422 Pielstickerstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02444 Porthofplatz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Platz; neu: Essener Geschichte und Örtlichkeit, Platz
- 02445 Porthofstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02463 Prinzenstraße — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 02508 Schacht Neu-Cöln — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 02511 Zum Wolbeckshof — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02543 Radhoffstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02549 Rahmfeld — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02551 Rahmstraße — feld: stadtteile; alt: Altenessen- Süd; Stoppenberg; neu: Altenessen-Süd; Stoppenberg
- 02554 Ramers Kamp — feld: stadtteile; alt: Altenessen- Süd; Stoppenberg; neu: Altenessen-Süd; Stoppenberg
- 02590 Rheinischer Platz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Platz; neu: Essener Geschichte und Örtlichkeit, Platz
- 02593 Ribbeckstraße — feld: stadtteile; alt: Stadtkern; Östviertel; neu: Stadtkern; Ostviertel
- 02614 Rodemannskamp — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02615 Rodemannstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02625 Röttgersbank — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02638 Rottekamp — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02657 Ruhlandplatz — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02664 Grendtor — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02670 Ruschenfeld — feld: lemma; alt: Ruschenfeld; neu: Ill. Ruschenfeld
- 02684 Römlingweg — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 02737 Schäferstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Bauunternehmer, Essener Geschichte und Ortlichkeit; neu: Person, Mann, Deutscher, Bauunternehmer, Essener Geschichte und Örtlichkeit
- 02760 Schichtstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02761 Schichtstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02775 Schlettweg — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 02782 Schloßgarten — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02783 Schloßstraße — feld: stadtteile; alt: Borbeck- Mitte; Bedingrade; Frintrop; neu: Borbeck-Mitte; Bedingrade; Frintrop
- 02784 Schloßwiese — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02787 Schlusenkamp — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02788 Schmale Straße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 02797 Schnieringstraße — feld: lemma; alt: Schnieringstraße; neu: I. Schnieringstraße
- 02801 Schnurstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02815 Schongauerstraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Maler, Kupferstecher, Malerviertel- Holsterhausen; neu: Person, Mann, Deutscher, Maler, Kupferstecher, Malerviertel-Holsterhausen
- 02829 Schützenbahn — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02830 Schützkamp — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 02839 Schurenstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02841 Schnieringshof — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02850 Schwarze Straße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02856 Segerothstraße — feld: namensgruppe; alt: Flurname, Essener Geschichte und Ortlichkeit; neu: Flurname, Essener Geschichte und Örtlichkeit
- 02867 Seumannstraße — feld: stadtteile; alt: Altenessen- Süd; Stoppenberg; neu: Altenessen-Süd; Stoppenberg
- 02918 Spritzenstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02924 Stahlstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 02925 Stakenholt — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02926 Stankeitstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 02935 Steigerstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 02960 Stiege — feld: lemma; alt: Stiege; neu: I. Stiege
- 02962 Stiege — feld: lemma; alt: Stiege; neu: Ill. Stiege
- 02971 Stolbergstraße — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 03001 Schürenfeld — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03003 Saturnstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 03004 Springhoffsfeld — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 03005 Selbachstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 03028 Schmetzweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03033 Schollbraukring — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03034 Suitbertstraße — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 03067 Thiesstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03072 Tiefbaustraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03105 Terwestenweg — feld: lemma; alt: Terwestenweg; neu: I. Terwestenweg
- 03107 Terwestenweg — feld: lemma; alt: Terwestenweg; neu: Ill. Terwestenweg
- 03140 Überruhrstraße — feld: stadtteile; alt: Überruhr- Hinsel; Überruhr-Holthausen; Burgaltendorf; neu: Überruhr-Hinsel; Überruhr-Holthausen; Burgaltendorf
- 03143 Uhdestraße — feld: namensgruppe; alt: Person, Mann, Deutscher, Kavallerieoffizierr, Maler, Malerviertel- Holsterhausen; neu: Person, Mann, Deutscher, Kavallerieoffizierr, Maler, Malerviertel-Holsterhausen
- 03145 Uhlenbank — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 03155 Unsuhrstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03163 Uranusstraße — feld: stadtteile; alt: Überruhr- Hinsel; neu: Überruhr-Hinsel
- 03223 Vinckestraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 03261 Vosselerweg — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03272 Am Ziegelteich — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03296 Waisenstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03324 Weberstraße — feld: lemma; alt: Weberstraße; neu: I. Weberstraße
- 03339 Weidkamp — feld: stadtteile; alt: Borbeck- Mitte; Bergeborbeck; neu: Borbeck-Mitte; Bergeborbeck
- 03345 Welkerhude — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03352 Werdener Markt — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 03365 Westendstraße — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit; neu: Essener Geschichte und Örtlichkeit
- 03366 Westerdorfplatz — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03366 Westerdorfplatz — feld: namensgruppe; alt: Essener Geschichte und Ortlichkeit, Hofname, Platz; neu: Essener Geschichte und Örtlichkeit, Hofname, Platz
- 03367 Westerdorfstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03377 Wickingstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03383 Wielandstraße — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 03393 Wildbannstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03394 Wildpferdehut — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03403 Weigelwerkstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03412 Winkhausstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03422 Wittgenbusch — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 03423 Wittgenpfad — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 03429 Wolbeckstraße — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03433 Wolfsdelle — feld: stadtteile; alt: Überruhr- Holthausen; neu: Überruhr-Holthausen
- 03439 Wüllnerskamp — feld: stadtteile; alt: Altenessen- Nord; neu: Altenessen-Nord
- 03448 Wieselweg — feld: stadtteile; alt: Altenessen- Süd; Vogelheim; neu: Altenessen-Süd; Vogelheim
- 03491 Zangenstraße — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03495 Zechenstraße — feld: verweis_auf; alt: Carolus- Magnus-Straße; neu: Carolus-Magnus-Straße
- 03524 Zur Nieden — feld: stadtteile; alt: Altenessen- Süd; neu: Altenessen-Süd
- 03564 An der Düsterbeck — feld: stadtteile; alt: Borbeck- Mitte; neu: Borbeck-Mitte
- 03672 Helmholtz- Heiligenhauser Straße — feld: lemma; alt: Helmholtz- Heiligenhauser Straße; neu: Helmholtz-Heiligenhauser Straße
- 03691 ) Im Winkel — feld: lemma; alt: ) Im Winkel; neu: Im Winkel
- 03760 nn Uhlandstraße — feld: lemma; alt: nn Uhlandstraße; neu: Uhlandstraße

## Status automatisch → unsicher

130 Rückstufungen. Sie sind die beabsichtigte
Hauptwirkung von Runde 2: 118 stammen aus dem neuen Hinweis `Anker OCR-korrigiert` (R6),
10 aus `Klammerzusatz ergänzt` (R2), einer aus `Randzeichen entfernt` (R5), einer aus
`Lemma auffällig` (R4-Nebenwirkung). Bei 102 der 130 sind Kopffelder und Namenskette
identisch mit 54c5e2a — die Toleranz war schon vorher da, nur unsichtbar. Jede Zeile ist
einzeln geprüft.

- 00005 Achternbergstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00010 Adelkampstraße
  - Prüfung: R5: führendes Randzeichen `„ ` vor der Straßenklasse entfernt (`„ Gemeindestraße` → `Gemeindestraße`); der Hinweis `Randzeichen entfernt` stuft vorsichtshalber auf `unsicher`, weil der Rest der Zeile weiter verunreinigt sein kann. Der Wert selbst ist jetzt richtig.
- 00050 Altendorfer Straße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Thomaestraße (tiw" → „Thomaestraße (tlw.)"; Name: „Altendorfer Straße (tw" → „Altendorfer Straße (tlw.)"; Name: „Altendorfer Straße (Verl)" → „Altendorfer Straße (Verl.)" — jeweils eine Verbesserung (R1/R2/R5).
- 00064 Am Brandenbusch
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00068 Am Brückenkopf
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00088 Am Haus Stein
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00100 Am Kornkamp
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00154 An der Bläufabrik
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00174 An St. Immakulata
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Borbeck- Mitte" → „Borbeck-Mitte" — jeweils eine Verbesserung (R1/R2/R5).
- 00248 Am Rüttenscheider Stern
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00249 Am Stadthafen
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00260 Am Fröhlinge
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00281 Bamlerstraße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur stadtteile: „Altenessen- Süd" → „Altenessen-Süd"; Name: „Berthold-Beitz-Boulevard (tlw" → „Berthold-Beitz-Boulevard (tlw.)" — jeweils eine Verbesserung (R1/R2/R5).
- 00325 Bentheimer Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00480 Bülsebeckstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00515 Benno-Strauß-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Kruppstraße (tiw.)" → „Kruppstraße (tlw.)" — jeweils eine Verbesserung (R1/R2/R5).
- 00540 Cäcilienstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00560 Charlottenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00591 Dachstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00601 Dandermannsteg
  - Prüfung: Nebenwirkung von R4 (bekannt und angenommen): der Ordnungspunkt in „Zeche Eintracht II." gilt nicht mehr als Satzende, deshalb zieht der Rückwärtslauf den Satzrest „Zur ehemaligen Zeche Eintracht II." ins Lemma. `_lemma_auffaellig` erkennt die Überlänge und stuft auf `unsicher` — der Fehler ist gekennzeichnet, nicht still (precision-first). Namenskette und Kopffelder sind korrekt; Nachzug über das Korrektur-Overlay möglich (S. 91).
- 00615 Dellmannsfeld
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Überruhr- Holthausen" → „Überruhr-Holthausen" — jeweils eine Verbesserung (R1/R2/R5).
- 00648 Donnerstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00650 Dornbuschhegge
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00684 Dutzendriege
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00687 Drimbornweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00697 Heinz-Renner-Platz
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Heinz-Renner- Platz" → „Heinz-Renner-Platz" — jeweils eine Verbesserung (R1/R2/R5).
- 00751 Eiserne Hand
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00800 Esmarchstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00801 Essener Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00802 Essingweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00808 Euskirchenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00816 Eskensfeld
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Überruhr- Holthausen" → „Überruhr-Holthausen" — jeweils eine Verbesserung (R1/R2/R5).
- 00854 Fendelweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00869 Fleuenbruch
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00880 Förderstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00972 Käthe-Larsch-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 00980 Grävenweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01012 Gerhardstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01039 Glashüttenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01043 Glückaufstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01060 Gottfried-Wilhelm-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01061 Grabenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01183 Hangohrstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01227 Hedwig-Dransfeld-Platz
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01240 Heidhauser Platz
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01276 Henricistraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01296 Heuweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01347 Hohendahlstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01377 Huckshorst
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01383 Hülsenbruchstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01455 Im Beckmannsfeld
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01462 Im Dreieck
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01501 Im Westerbruch
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Im Westerbruch (Verl" → „Im Westerbruch (Verl.)" — jeweils eine Verbesserung (R1/R2/R5).
- 01517 Ingelheimer Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01518 Inselstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01596 Conrad-Engels-Weg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01602 Straßburger Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01607 Carl-Schmitz-Weg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01614 Am Bruchweiher
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01641 Kampmannbrücke
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01652 Kapitelberg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01671 Kasteienstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01710 Kirchhofsallee
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01734 Kleine Schäferstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01751 Klumbeckweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01771 Kötterei
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01784 Kopernikusstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01838 Kütings Garten
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01856 Kevelohbusch
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Überruhr- Hinsel" → „Überruhr-Hinsel" — jeweils eine Verbesserung (R1/R2/R5).
- 01869 Kleine Rahmstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01887 Kirchgang
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01900 Langeheide
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 01960 Lichterweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02032 Langeoogweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02044 Mariannenbahn
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02061 Märkische Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02082 Markgrafenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02137 Middeldorper Weg
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Middeldorper Weg (Verl.." → „Middeldorper Weg (Verl.)" — jeweils eine Verbesserung (R1/R2/R5).
- 02159 Moorenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02164 Mosebachstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02236 Neuessener Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02247 Nibelungenplatz
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02248 Nibelungenweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02267 Nöttelhof
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02273 Nordschleswigstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02312 Oberer Pustenberg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Pustenberg (tiw.)" → „Pustenberg (tlw.)" — jeweils eine Verbesserung (R1/R2/R5).
- 02314 Oberhauser Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02318 Oberscheidtstraße
  - Prüfung: Dieselbe R4-Nebenwirkung wie 00601: „Kaiser Wilhelms I." endet nicht mehr den Satz, der Rest „e sowie Generaladjutant Kaiser Wilhelms I." landet im Lemma. Form und Länge sind auffällig, der Eintrag ist `unsicher`; zusätzlich trägt er den R6-Hinweis `Anker OCR-korrigiert`. Namenskette (Bülowstraße → Oberscheidtstraße) unverändert und richtig (S. 251).
- 02462 Prinz-Adolf-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Prinz-Adolf- Straße" → „Prinz-Adolf-Straße" — jeweils eine Verbesserung (R1/R2/R5).
- 02506 Ostendeweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02521 Ketteltasches Hof
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02550 Rahmheide
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02563 Rausenbergerstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02578 Reineke-Fuchs-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02580 Rembrandtstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02621 Röntgenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still; R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Marschallstraße (tlw" → „Marschallstraße (tlw.)" — jeweils eine Verbesserung (R1/R2/R5).
- 02628 Rollstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02656 Rüttenscheider Straße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Hermann-Göring-Straße (Umb" → „Hermann-Göring-Straße (Umb.)" — jeweils eine Verbesserung (R1/R2/R5).
- 02659 Ruhrau
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02680 Regenbogenweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02749 Schederhofstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02752 Scheidtstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02775 Schlettweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Überruhr- Hinsel" → „Überruhr-Hinsel" — jeweils eine Verbesserung (R1/R2/R5).
- 02837 Schulte-Pelkum-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Schulte-Pelkum- Straße" → „Schulte-Pelkum-Straße" — jeweils eine Verbesserung (R1/R2/R5).
- 02839 Schurenstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Altenessen- Nord" → „Altenessen-Nord" — jeweils eine Verbesserung (R1/R2/R5).
- 02870 Sevinghauser Weg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02886 Simsonstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02900 Sophienstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02917 Springmannstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02927 Stapenhorststraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02953 Stensstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 02974 Stoppenberger Straße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Lützowstraße (tiw" → „Lützowstraße (tlw.)" — jeweils eine Verbesserung (R1/R2/R5).
- 03083 Tonstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03093 Triftstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03114 Ten-Hövel-Weg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Ten- Hövel-Weg" → „Ten-Hövel-Weg" — jeweils eine Verbesserung (R1/R2/R5).
- 03257 Veldeckestraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03345 Welkerhude
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Altenessen- Nord" → „Altenessen-Nord" — jeweils eine Verbesserung (R1/R2/R5).
- 03359 Weserstraße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Joseph-Hommer-Weg (Umb" → „Joseph-Hommer-Weg (Umb.)" — jeweils eine Verbesserung (R1/R2/R5).
- 03360 Wesselbaumweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03387 Wiesbadener Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03409 Windscheidstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03429 Wolbeckstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur stadtteile: „Altenessen- Nord" → „Altenessen-Nord" — jeweils eine Verbesserung (R1/R2/R5).
- 03444 Walter-Hohmann-Straße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Walter- Hohmann-Straße" → „Walter-Hohmann-Straße" — jeweils eine Verbesserung (R1/R2/R5).
- 03504 Zimmermannstraße
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Inhaltlich geändert hat sich nur Name: „Zimmermannstraße (Verl)" → „Zimmermannstraße (Verl.)" — jeweils eine Verbesserung (R1/R2/R5).
- 03552 Am Wiedenfeld
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03610 Fröbelweg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03617 An der Pierburg
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03676 Herkendell
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03731 Oefte
  - Prüfung: R6: der Anker dieser Seite weicht von `Schl.-Nr.:` ab. Gelesen wurde der Eintrag schon vorher (die Anker-Toleranz ist älter), neu ist allein der Hinweis — bisher tolerierte der Parser still. Kopffelder und Namenskette sind Zeichen für Zeichen identisch mit 54c5e2a — es ändert sich nur die Kennzeichnung, kein Datenverlust.
- 03748 Schulstraße
  - Prüfung: R2: ein abgeschnittener Klammerzusatz wurde zu einer Vollform ergänzt und die Ergänzung gekennzeichnet. Inhaltlich geändert hat sich nur Name: „Langemarckstraße (Umb" → „Langemarckstraße (Umb.)" — jeweils eine Verbesserung (R1/R2/R5).


## Status unsicher → automatisch

34 Aufstufungen — Einträge, deren einziger Prüfgrund
ein verstümmelter Klammerzusatz war. Nachgezählt: alle 34 tauchen in „Name verändert" mit
genau einer solchen Korrektur auf (`Sonnenstraße {tlw.)`, `Hindenburgstraße {Umb.)`,
`Helenenstraße (Umb.}`, `Curtiusstraße (t!w.)`).
R2 normalisiert die Form jetzt eindeutig; eine bloße Schreibvariante `{` statt `(` ist
belegt und wird deshalb nicht mehr gekennzeichnet (Spec R2: Korrekturen der Schreibung
gelten als eindeutig, nur *Ergänzungen* erzeugen einen Hinweis). Alle 34 sind in
„Name verändert" mit alter und neuer Form nachvollziehbar; kein Eintrag steigt auf, ohne
dass sein Prüfgrund nachweislich behoben wäre.

- 00091 Am Herrenbusch
- 00528 Langenbrahmstraße
- 00564 Körholzstraße
- 00637 Distelbeckhof
- 00893 Franziskastraße
- 00947 Franz-Arens-Straße
- 01192 Hardenbergufer
- 01252 Heinrich-Sense-Weg
- 01275 Henningweg
- 01288 Herwarthstraße
- 01376 Hubertweiche
- 01405 Husemannweg
- 01431 Holteyer Hang
- 01461 Imbuschweg
- 01748 Klosterstraße
- 01786 Kleine Steubenstraße
- 01968 Lilienstraße
- 01971 Limbecker Straße
- 02103 Maybachstraße
- 02131 Metzendorfstraße
- 02290 Niebuhrstraße
- 02333 Oslenderstraße
- 02441 Porschekanzel
- 02461 Priemhauser Weg
- 02662 Ruhrglasstraße
- 02997 Sundernholz
- 03369 Westerwaldstraße
- 03492 Zeche Eiberg
- 03530 Zweihonnschaftenwald
- 03564 An der Düsterbeck
- 03603 Am Hammershöfchen
- 03733 Oberlehberg
- 03743 Ruhrstraße
- 03747 Schmachtenbergstraße
