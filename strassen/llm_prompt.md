Du transkribierst eine Seite aus einem gedruckten Straßenlexikon (Essen, 2015). Jeder
Eintrag beginnt mit dem heutigen Straßennamen als fett gedrucktes Stichwort, dann folgen
Kopfangaben (`Schl.-Nr.:` fünfstellige Schlüsselnummer, `Stadtteil:` oder `Stadtteile:`,
`Str.-Kl.:` Straßenklasse, `Str.-Gr.:` Namensgruppe), dann die Namenskette (Datum,
Doppelpunkt, Name; mehrere durch Komma/Semikolon), danach ein Erläuterungstext in Prosa.
Manche Einträge bestehen nur aus `Siehe <Name>`.

Regeln:
1. Transkribiere ausschließlich, was auf der Seite steht. Nichts ergänzen, nichts
   modernisieren, keine Rechtschreibung „verbessern". Unleserliches als `?` markieren.
2. Gib GENAU EINE JSON-Liste zurück, ohne Text davor oder danach. Ein Objekt je Eintrag,
   der auf dieser Seite mit einem Stichwort BEGINNT. Einträge, die von der Vorseite
   hereinlaufen (kein Stichwort oben auf der Seite), auslassen.
3. Felder je Objekt (alle immer angeben, leer als "" bzw. []):
   - "schl_nr": Schlüsselnummer wie gedruckt, fünfstellig, z. B. "00417"
   - "lemma": das Stichwort
   - "stadtteile": Liste der Stadtteile, jeder einzeln, z. B. ["Frohnhausen", "Holsterhausen"]
   - "strassenklasse": Liste, z. B. ["Gemeindestraße"]
   - "namensgruppe": Text nach `Str.-Gr.:`
   - "verweis_auf": nur bei `Siehe <Name>` der Name, sonst ""
   - "stadien": Liste der Namensstadien in gedruckter Reihenfolge, je
     {"datum": "<Datum WÖRTLICH wie gedruckt, z. B. '29.08.1927', '16. Mai 1902', 'um 1900',
     'vor 1898', 'im 16. Jahrhundert', '1927'>", "name": "<Name wie gedruckt, inkl.
     Klammerzusätzen wie '(tlw.)'>", "urspruenglich": true wenn 'urspr.'/'ursprünglich'
     davor steht, sonst false}
     Ein Stadium ohne Datum: "datum": "".
   - "unvollstaendig": true, wenn der Eintrag am Seitenende abbricht, sonst false
4. Den Erläuterungstext NICHT transkribieren.
5. Kein Eintrag darf fehlen; die Schlüsselnummern laufen auf der Seite fortlaufend.

Beispiel eines Objekts:
{"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": ["Frohnhausen"],
 "strassenklasse": ["Gemeindestraße"], "namensgruppe": "Stadt und Ort", "verweis_auf": "",
 "stadien": [{"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": false},
             {"datum": "16.05.1902", "name": "Aachener Straße", "urspruenglich": false}],
 "unvollstaendig": false}
