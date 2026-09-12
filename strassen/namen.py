"""Namensstadien mit Datum aus dem Kopfrest lesen.

Jedes Stadium ist ein Datum-Name-Paar. Fehlt das Datum ('urspr.:'), wird das im
Feld datum_praezision ausgewiesen — nicht geschätzt. Die Datumsformen und die
Satzende-Regel kommen aus strassen.datum (eine Quelle für kopf.py und namen.py).

'urspr.:' kann mehrfach in derselben Kette vorkommen (22 Einträge im Material,
z. B. Altenessener Straße Schl.-Nr. 00053) — alle Vorkommen werden erfasst und
nach Textposition einsortiert. 'urspr.' ohne Doppelpunkt (8 Fälle, z. B. Velberter
Sträßchen 03203) wird erkannt und mit Hinweis versehen.

Der Name endet an Komma/Semikolon oder an einem echten Satzende (datum.SATZENDE):
Abkürzungs-/Klammerpunkte ('St. Annental', 'II. Weberstraße', '(Verl.)') bleiben
Namensbestandteil.

Positionsregel für Stempel ohne Doppelpunkt (Spec Regel 15): Sie zählen nur, wenn
sie am Anfang von rest stehen oder direkt auf ein Komma folgen (Kettentrenner) UND
der Name großgeschrieben beginnt. Ein Datum, dem ein Wort vorausgeht ('Am 25. Juli
1516 wurde'), ist Prosa.
"""
import re
from typing import NamedTuple

from strassen.datum import DATUMSSTEMPEL_MUSTER, SATZENDE, MONATE, lese_datum

__all__ = ["MONATE", "Stadium", "parse_namenskette", "unverarbeiteter_rest"]

_NAME = r"(?:(?!,|;|" + SATZENDE + r")[^\n]){1,80}"

_URSPR = re.compile(r"urspr\.(?P<trenner>:?)\s*(?P<name>" + _NAME + r")")
_STADIUM = re.compile(DATUMSSTEMPEL_MUSTER + r"\s*(?P<name>" + _NAME + r")")

HINWEIS_URSPR_OHNE_DOPPELPUNKT = "urspr. ohne Doppelpunkt"


class Stadium(NamedTuple):
    stadium: int
    gueltig_ab: str
    datum_praezision: str
    name: str
    ist_urspruenglich: bool
    hinweis: str = ""


def _position_erlaubt(rest: str, start: int) -> bool:
    """Für Stempel ohne regulären Doppelpunkt: Kettenanfang oder direkt nach Komma."""
    davor = rest[:start].rstrip()
    return davor == "" or davor.endswith(",")


def _akzeptierte_treffer(rest: str) -> list:
    """Ein interner Durchlauf über 'urspr.' und die akzeptierten Stadien, jeweils mit
    Textspanne (start, end) — Basis für parse_namenskette UND unverarbeiteter_rest,
    damit beide exakt dieselben Treffer als 'gelesen' behandeln."""
    roh = []

    for mu in _URSPR.finditer(rest):
        hinweis = "" if mu.group("trenner") == ":" else HINWEIS_URSPR_OHNE_DOPPELPUNKT
        roh.append((mu.start(), mu.end(), "", "unbekannt", mu.group("name").strip(),
                    True, hinweis))

    for m in _STADIUM.finditer(rest):
        name = m.group("name").strip()
        d = lese_datum(m)
        # Ein bloßes Jahr ist der schwächste Stempel: geschrieben als 'jjjj:'
        # (m.group('jahr_bloss')) oder als Volldatum, dessen Tag/Monat ungültig war
        # und das lese_datum deshalb auf das Jahr zurückgestuft hat (nicht aber ein
        # ausdrückliches 'vor/nach/um/etwa/gegen jjjj:' — das ist bewusst so
        # geschrieben, kein Degradat). Hinter Rauschen liest sich sonst ein
        # verstümmeltes Volldatum (Tag/Monat verloren) unbemerkt als stilles Jahr
        # (Dudweilerstraße 00685, S. 104: 'A 0, EEE 1935:' statt '14. November
        # 1935:'). Ein bloßes Jahr unterliegt deshalb IMMER der Positionsregel,
        # auch mit regulärem Doppelpunkt-Trenner.
        schwach = d.praezision == "jahr" and not m.group("qualifier")
        if d.trenner != ":" or schwach:
            if not _position_erlaubt(rest, m.start()) or not name[:1].isupper():
                continue
        roh.append((m.start(), m.end(), d.gueltig_ab, d.praezision, name, False, d.hinweis))

    roh.sort(key=lambda x: x[0])
    return roh


def parse_namenskette(rest: str) -> list:
    roh = _akzeptierte_treffer(rest)
    return [Stadium(stadium=i, gueltig_ab=g, datum_praezision=p, name=n,
                     ist_urspruenglich=u, hinweis=h)
            for i, (_, _, g, p, n, u, h) in enumerate(roh, 1)]


def unverarbeiteter_rest(rest: str) -> str:
    """Der Teil von rest, der von keinem akzeptierten Treffer (urspr. + Stadien)
    erfasst wurde — Rohtext, der zwischen/hinter der erkannten Kette liegen bleibt
    (Spec-Lücke Fix Task 12: verstümmelte Datumsfragmente wie '19377' lösten bisher
    keinen Prüfgrund aus, weil kein Muster darauf matcht). Trenner (',', ';',
    Leerraum) und ein abschließender Punkt zählen nicht als Rest."""
    spannen = sorted((start, end) for start, end, *_ in _akzeptierte_treffer(rest))
    stuecke = []
    pos = 0
    for start, end in spannen:
        if start > pos:
            stuecke.append(rest[pos:start])
        pos = max(pos, end)
    stuecke.append(rest[pos:])
    residuum = "".join(stuecke)

    vorher = None
    while vorher != residuum:
        vorher = residuum
        residuum = residuum.strip().strip(",;")
        if residuum.endswith("."):
            residuum = residuum[:-1]
    return residuum
