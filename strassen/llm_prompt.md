Du transkribierst eine Seite aus einem gedruckten Straßenlexikon (Essen, 2015). Jeder
Eintrag beginnt mit dem heutigen Straßennamen als fett gedrucktes Stichwort, dann folgen
Kopfangaben (`Schl.-Nr.:` fünfstellige Schlüsselnummer, `Stadtteil:` oder `Stadtteile:`,
`Str.-Kl.:` Straßenklasse, `Str.-Gr.:` Namensgruppe), dann die Namenskette (Datum,
Doppelpunkt, Name; mehrere durch Komma/Semikolon), danach ein Erläuterungstext in Prosa.
Manche Einträge bestehen nur aus `Siehe <Name>`.

Die Kopfangaben laufen als ein Satz durch; die Feldgrenzen erkennt man an den Markern:
`Str.-Gr.:` reicht bis zum Beginn der Namenskette und kann selbst eine Komma-Liste sein
(z. B. `Str.-Gr.: Lagebezeichnung, Platz, vor 1898: Rathausplatz` — Namensgruppe ist
`Lagebezeichnung, Platz`, das erste Stadium `vor 1898: Rathausplatz`). Die Namenskette
beginnt mit dem ersten Datum oder mit `urspr.:` und endet mit dem Punkt vor dem
Erläuterungstext.

Regeln:
1. Transkribiere ausschließlich, was auf der Seite steht. Nichts ergänzen, nichts
   modernisieren, keine Rechtschreibung „verbessern" (`Phoenixhütte` bleibt
   `Phoenixhütte`, nicht `Phönixhütte`). Unleserliches als `?` markieren.
   Am Zeilenende getrennte Wörter wieder zusammensetzen: kein Wert endet oder beginnt
   mit einem Trennstrich, und ein Trennstrich der Silbentrennung verschwindet
   (`Kriegs-erinnerung` -> `Kriegserinnerung`). Echte Bindestriche im Namen bleiben
   (`Heinrich-Unger-Straße`).
2. Gib GENAU EINE JSON-Liste zurück, ohne Text davor oder danach. Ein Objekt je Eintrag,
   der auf dieser Seite mit einem Stichwort BEGINNT. Einträge, die von der Vorseite
   hereinlaufen (kein Stichwort oben auf der Seite), auslassen.
3. Felder je Objekt (alle immer angeben, leer als "" bzw. []):
   - "schl_nr": Schlüsselnummer wie gedruckt, fünfstellig, z. B. "00417"
   - "lemma": das Stichwort
   - "stadtteile": Liste der Stadtteile, jeder einzeln, z. B. ["Frohnhausen", "Holsterhausen"]
   - "strassenklasse": Liste, z. B. ["Gemeindestraße"]
   - "namensgruppe": Text nach `Str.-Gr.:`
   - "verweis_auf": der Name aus einem `Siehe <Name>`-Verweis, egal wo er im Eintrag
     steht — auch wenn er erst nach dem Erläuterungstext am Ende folgt (z. B.
     `... 21. November 1968: Alte Raadter Straße. Siehe Raadter Straße.` ->
     "Raadter Straße"). NICHT bei `Siehe auch <Name>` und nicht bei `Vgl. <Name>`;
     dann ""
   - "stadien": Liste der Namensstadien in gedruckter Reihenfolge, je
     {"datum": "<Datum WÖRTLICH wie gedruckt, z. B. '29.08.1927', '16. Mai 1902', 'um 1900',
     'vor 1898', 'im 16. Jahrhundert', '1927'>", "name": "<Name wie gedruckt, inkl.
     Klammerzusätzen wie '(tlw.)'>", "urspruenglich": true wenn 'urspr.'/'ursprünglich'
     davor steht, sonst false}
     Ein Stadium ohne Datum: "datum": "" — der Marker `urspr.` gehört NIE ins Datumsfeld
     und auch nicht in den Namen, sondern allein in "urspruenglich". Ein `urspr.:`-Stadium steht direkt hinter der
     Namensgruppe und hat oft kein Datum (`Str.-Gr.: Familienname, urspr.: Hofstraße,
     20. November 1937: Schwelmhöfe` -> zwei Stadien: {"datum": "", "name": "Hofstraße",
     "urspruenglich": true} und {"datum": "20. November 1937", "name": "Schwelmhöfe",
     "urspruenglich": false}). Solche datumslosen Stadien nie auslassen, sonst rutscht
     die ganze Kette um eins.
     Jeder "name" ist ein Straßenname, also kurz — nie ein Satz, nie ein Personenname
     mit Lebensdaten. Die Kette endet beim ersten Satz, der keine `Datum: Name`-Angabe
     mehr ist; alles danach ist Erläuterung. Lebensdaten (`*14. Oktober 1777`,
     `†17. Mai 1857`), Jahreszahlen in Sätzen, Mutterrollen- und Quellenangaben sind
     KEINE Stadien. Ein datumsloses Stadium gibt es nur mit dem Marker `urspr.`.
   - "unvollstaendig": true, wenn der Eintrag am Seitenende abbricht, sonst false
4. Den Erläuterungstext NICHT transkribieren.
5. Kein Eintrag darf fehlen. Jede `schl_nr` steht im Kopf ihres eigenen Eintrags und wird
   dort abgelesen — die Nummern sind NICHT durchgehend fortlaufend (auf einer Seite stehen
   z. B. 00046, 00252, 00054 nebeneinander); nie aus der Reihenfolge weiterzählen.

Beispiel eines Objekts (fiktives Beispiel, nicht aus dem Buch):
{"schl_nr": "09999", "lemma": "Musterweg", "stadtteile": ["Beispielviertel"],
 "strassenklasse": ["Gemeindestraße"], "namensgruppe": "Flurname", "verweis_auf": "",
 "stadien": [{"datum": "vor 1900", "name": "Alter Musterweg", "urspruenglich": false},
             {"datum": "3. März 1925", "name": "Musterweg", "urspruenglich": false}],
 "unvollstaendig": false}
