"""Namensstadien mit Datum aus dem Kopfrest lesen.

Jedes Stadium ist ein Datum-Name-Paar. Fehlt das Datum ('urspr.:'), wird das
im Feld datum_praezision ausgewiesen — nicht geschätzt.

Neben dem vollen Tagesdatum kommen im Material ungefähre Jahresangaben vor
('vor 1898:', 'nach 1900:', 'um 1850:', 'etwa 1860:', 'gegen 1870:') — siehe
kopf._DATUM, die dieselben Qualifier bereits toleriert. Die Unschärfe wird
ehrlich ausgewiesen statt geglättet: 'vor'/'nach' behalten ihre Richtung als
eigene Präzisionsstufe; 'um'/'etwa'/'gegen' bedeuten alle drei dasselbe
(ungefähr, ohne Richtung) und werden als 'jahr' geführt, weil das Jahr selbst
die beste verfügbare Angabe ist — precision-first heißt hier: keine Schein-
genauigkeit vortäuschen, aber auch keine eigene Kategorie für eine Nuance
erfinden, die das Feldschema nicht vorsieht.
"""
import re
from typing import NamedTuple

MONATE = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
          "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11,
          "Dezember": 12}

_URSPR = re.compile(r"urspr\.:\s*(?P<name>[^,.;]{1,80})")

# Ein Stadium ist entweder ein volles Tagesdatum, eine gerichtete ungefähre
# Jahresangabe (vor/nach) oder eine ungerichtete ungefähre Jahresangabe
# (um/etwa/gegen) oder ein bloßes Jahr ohne Qualifier — je gefolgt von
# ':' und dem Namen. (?<!\d) verhindert, dass die Suche mitten in einer
# längeren Ziffernfolge ansetzt statt an deren Anfang.
_STADIUM = re.compile(
    r"(?<!\d)"
    r"(?:(?P<tag>\d{1,2})\.\s*(?P<monat>" + "|".join(MONATE) + r")\s+(?P<jahr_tag>\d{4})"
    r"|(?P<qualifier>vor|nach|um|etwa|gegen)\s+(?P<jahr_qual>\d{4})"
    r"|(?P<jahr_bloss>\d{4})"
    r")\s*:\s*(?P<name>[^,.;]{1,80})"
)

_GERICHTET = {"vor": "vor", "nach": "nach"}


class Stadium(NamedTuple):
    stadium: int
    gueltig_ab: str
    datum_praezision: str
    name: str
    ist_urspruenglich: bool


def parse_namenskette(rest: str) -> list:
    roh = []

    # 'urspr.:' steht, wenn vorhanden, immer als erstes Glied der Kette —
    # vor jedem datierten Stadium. Keine Positionssuche nötig.
    mu = _URSPR.search(rest)
    if mu:
        roh.append(("", "unbekannt", mu.group("name").strip(), True))

    for m in _STADIUM.finditer(rest):
        name = m.group("name").strip()
        if m.group("tag"):
            tag, jahr = int(m.group("tag")), int(m.group("jahr_tag"))
            monat = MONATE[m.group("monat")]
            roh.append((f"{jahr:04d}-{monat:02d}-{tag:02d}", "tag", name, False))
        elif m.group("qualifier"):
            praezision = _GERICHTET.get(m.group("qualifier"), "jahr")
            roh.append((m.group("jahr_qual"), praezision, name, False))
        else:
            roh.append((m.group("jahr_bloss"), "jahr", name, False))

    return [Stadium(stadium=i, gueltig_ab=g, datum_praezision=p, name=n,
                     ist_urspruenglich=u)
            for i, (g, p, n, u) in enumerate(roh, 1)]
