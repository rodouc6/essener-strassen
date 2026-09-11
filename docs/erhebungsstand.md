# Erhebungsstand des Adressbuchs Essen 1936

Misst, welchen Namensstand das Adressbuch Essen 1936 (Adressbuch-Datensatz des Kartenprojekts, siehe README, Abschnitt „Externe Eingaben") tatsächlich abbildet, und leitet daraus die Konkordanz für das Kartenprojekt ab (`strassen/stichtag.py`, `strassen/veroeffentlichen.py`, `tests/test_stichtag.py`). Erzeugt von `python3 -m strassen.veroeffentlichen` — bei unveränderten Eingaben byte-identisch reproduzierbar.

## Methode

Für jede Umbenennung (Übergang von einem Namensstadium zum nächsten in `daten/namen.csv`) wird geprüft, ob das Adressbuch die alte oder die neue Namensform verwendet (Straßennamen kleingeschrieben, „str."/„straße" vereinheitlicht). Stadien ohne verwertbares Datum (`datum_praezision` `unbekannt`) werden übersprungen, nie geschätzt. Für die **monatsscharfe** Auswertung zählen nur Stadien mit Tagespräzision — Jahrpräzision liefert keinen echten Monat, das würde sonst einen Monat erfinden statt ihn aus den Daten zu lesen.

## Jährliche Auswertung

| Jahr | alt (Adressbuch nutzt alten Namen) | neu (Adressbuch nutzt neuen Namen) |
|-----:|------------------------------------:|-------------------------------------:|
| 1825 | 0 | 1 |
| 1826 | 1 | 0 |
| 1860 | 1 | 1 |
| 1868 | 1 | 0 |
| 1871 | 1 | 0 |
| 1872 | 0 | 1 |
| 1874 | 1 | 1 |
| 1883 | 2 | 0 |
| 1885 | 1 | 0 |
| 1889 | 2 | 0 |
| 1890 | 2 | 0 |
| 1891 | 4 | 4 |
| 1892 | 2 | 0 |
| 1894 | 1 | 1 |
| 1895 | 2 | 1 |
| 1896 | 5 | 3 |
| 1897 | 4 | 2 |
| 1898 | 1 | 1 |
| 1899 | 1 | 1 |
| 1900 | 5 | 2 |
| 1901 | 1 | 2 |
| 1902 | 3 | 10 |
| 1903 | 4 | 5 |
| 1904 | 0 | 3 |
| 1905 | 1 | 0 |
| 1906 | 8 | 5 |
| 1907 | 1 | 5 |
| 1908 | 7 | 3 |
| 1909 | 3 | 5 |
| 1910 | 12 | 22 |
| 1911 | 2 | 4 |
| 1912 | 0 | 2 |
| 1913 | 0 | 1 |
| 1914 | 1 | 1 |
| 1915 | 40 | 56 |
| 1916 | 0 | 2 |
| 1919 | 3 | 1 |
| 1920 | 3 | 5 |
| 1922 | 6 | 7 |
| 1923 | 0 | 2 |
| 1924 | 1 | 2 |
| 1925 | 1 | 1 |
| 1926 | 2 | 7 |
| 1927 | 2 | 4 |
| 1928 | 2 | 2 |
| 1929 | 6 | 7 |
| 1930 | 5 | 7 |
| 1931 | 9 | 6 |
| 1932 | 0 | 3 |
| 1933 | 20 | 14 |
| 1934 | 14 | 12 |
| 1935 | 9 | 23 |
| 1936 | 20 | 5 |
| 1937 | 187 | 0 |
| 1938 | 3 | 1 |
| 1939 | 4 | 0 |
| 1940 | 1 | 0 |
| 1945 | 6 | 1 |
| 1946 | 12 | 2 |
| 1947 | 0 | 1 |
| 1948 | 2 | 0 |
| 1949 | 1 | 0 |
| 1950 | 1 | 1 |
| 1951 | 4 | 0 |
| 1952 | 1 | 0 |
| 1953 | 5 | 0 |
| 1954 | 4 | 0 |
| 1955 | 2 | 1 |
| 1956 | 2 | 0 |
| 1957 | 1 | 3 |
| 1958 | 0 | 1 |
| 1959 | 4 | 0 |
| 1961 | 4 | 1 |
| 1963 | 5 | 1 |
| 1964 | 2 | 0 |
| 1965 | 3 | 0 |
| 1966 | 3 | 1 |
| 1967 | 1 | 2 |
| 1968 | 2 | 0 |
| 1969 | 1 | 2 |
| 1970 | 11 | 2 |
| 1971 | 6 | 0 |
| 1972 | 4 | 1 |
| 1973 | 1 | 1 |
| 1974 | 1 | 0 |
| 1975 | 1 | 0 |
| 1976 | 6 | 1 |
| 1977 | 22 | 1 |
| 1978 | 19 | 0 |
| 1979 | 3 | 0 |
| 1980 | 3 | 0 |
| 1981 | 1 | 0 |
| 1982 | 1 | 0 |
| 1994 | 1 | 0 |
| 2003 | 1 | 0 |
| 2006 | 1 | 0 |
| 2011 | 1 | 0 |
| 2013 | 1 | 0 |

## Monatsscharfe Auswertung (1935-01 bis 1937-12)

| Monat | alt | neu |
|-------|----:|----:|
| 1935-01 | 0 | 3 |
| 1935-02 | 1 | 0 |
| 1935-05 | 1 | 0 |
| 1935-06 | 0 | 2 |
| 1935-09 | 0 | 1 |
| 1935-10 | 0 | 11 |
| 1935-11 | 7 | 6 |
| 1936-01 | 12 | 5 |
| 1936-02 | 1 | 0 |
| 1936-08 | 7 | 0 |
| 1937-01 | 1 | 0 |
| 1937-02 | 22 | 0 |
| 1937-11 | 164 | 0 |

(Nur Jahre/Monate mit mindestens einer verwertbar datierten Umbenennung sind aufgeführt; für die monatsscharfe Tabelle zusätzlich nur solche mit Tagespräzision.)

## Interpretation

Ab Umbenennungen ab Februar 1936 reflektiert das Adressbuch keine einzige mehr — das grenzt den tatsächlichen Erhebungsschluss auf etwa **Ende 1935 bis Januar 1936** ein, plausibel für ein Werk mit Titeljahr 1936. Der als Arbeitswert verwendete Stichtag **1936-06-30** liegt komfortabel im gesamten Zeitfenster (Februar 1936 bis Januar 1937), in dem keine weitere Umbenennung mehr auf den Datensatz einwirkt — eine engere Festlegung wäre durch die Daten nicht gedeckt und würde das Ergebnis der Konkordanz nicht ändern.

## Konkordanz-Ableitung (`daten/konkordanz_1936.csv`, Stichtag 1936-06-30)

Die Konkordanz wird **nur aus Straßen mit `status=automatisch`** gebaut; unsichere Lemmata (`status=unsicher`) gehören nicht in die produktive Konkordanz, da ihr heutiger Name selbst nicht belastbar ist. Einträge, deren Namenskette intern widersprüchlich ist (letztes Stadium ≠ Lemma nach Zusatz-Abtrennung, mechanisches Konsistenz-Netz), landen nicht in der Konkordanz, sondern als Prüffall in `daten/pruefung_konkordanz.csv`.

- Straßen gesamt: 3338
- davon `status=automatisch` (Basis der Konkordanz): 3094
- davon `status=unsicher` (ausgeschlossen): 244
- Konkordanzeinträge: **427**
  - davon `eindeutig=ja`: 388 / `eindeutig=nein` (Kollisionen): 39
  - davon mit Klammerzusatz (z. B. „(tlw.)", „(Verl.)"): 133
- Prüffälle (`daten/pruefung_konkordanz.csv`): **72**

Methodische Begründung der Konkordanz-Ableitung (Klammerzusätze abtrennen, Kollisionen markieren, mechanisches Konsistenz-Netz gegen unvollständige Namensketten, „(tlw.)"-Teilangaben als informationstragend behalten): siehe die Docstrings in `strassen/stichtag.py` (`_trenne_zusatz`, `_ist_teil_zusatz`, `_kandidat_oder_pruefung`, `baue_konkordanz`).

