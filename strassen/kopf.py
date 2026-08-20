"""Strukturfelder aus dem Eintragskopf lesen.

Der Kopf ist eine Kette kommagetrennter Felder; der Erläuterungstext beginnt nach
dem letzten Datum-Name-Paar. Die Abgrenzung erfolgt über die Feldmuster selbst:
Was keinem Muster mehr entspricht, ist Fließtext.

Die Feldmarker ('Str.-Kl.:', 'Str.-Gr.:') toleriert die im Material vorkommenden
OCR-Varianten: fehlender Bindestrich/Punkt ('Str-Kl:'), Leerzeichen statt
Bindestrich ('Str. Gr.:') und die l/I-Verwechslung ('Str.-KI.:'). precision-first:
die Toleranz betrifft nur die Marker-Schreibweise, nicht die Feldwerte selbst —
wo kein Marker (auch tolerant) gefunden wird, bleibt das Feld leer statt geraten.
"""
import re
from typing import NamedTuple

_NUMMER = re.compile(r"^\s*(\d{1,5})\b")

# Marker-Bausteine, roh (ohne Gruppen) zur Wiederverwendung in Lookaheads.
_M_KLASSE = r"Str\.?\s*-?\s*K[lI]\.?\s*:"
_M_GRUPPE = r"Str\.?\s*-?\s*Gr\.?\s*:"
# Datumsstempel eines Namensstadiums: entweder ein volles Datum ('16. Mai 1902:')
# oder eine ungefähre Jahresangabe ohne Tag/Monat ('vor 1898:', 'um 1850:',
# 'etwa 1860:') — über 380 Fälle im Material, die sonst als Teil der
# Namensgruppe fehlgelesen würden.
_DATUM = r"(?:\d{1,2}\.\s*\w+\s+\d{4}|(?:vor|nach|um|etwa|gegen)\s+\d{4})\s*:"

_STADTTEIL = re.compile(
    r"Stadtteile?\s+([^,;]+?)(?=,|\s+" + _M_KLASSE + r"|\s+" + _M_GRUPPE + r"|$)"
)
# Fallback auf ".\s": vereinzelt fehlt im OCR der Doppelpunkt nach 'Str.-Gr'
# (5 Fälle); ohne Satzende-Grenze würde die Klasse sonst den kompletten
# restlichen Eintrag inklusive Erläuterung verschlucken.
_KLASSE = re.compile(_M_KLASSE + r"\s*(.+?)(?=,?\s*" + _M_GRUPPE + r"|\.\s|$)")
_GRUPPE = re.compile(
    _M_GRUPPE + r"\s*(.+?)"
    r"(?=,\s*(?:urspr\.:|" + _DATUM + r")|\.\s|$)"
)
# Kopfende: der Punkt nach dem letzten „Datum: Name"-Paar bzw. nach der Namensgruppe.
# Der Namensteil schließt Ziffern aus, damit die Suche nicht über die Tagesziffer
# eines nachfolgenden Datums hinweg an dessen Punkt ('09.') hängen bleibt.
_STADIUM = re.compile(_DATUM + r"\s*[^.\d]{1,80}?\.")


class Kopf(NamedTuple):
    schl_nr: str
    stadtteile: list
    strassenklassen: list
    namensgruppe: str
    rest: str


# Ein echter Feldwert beginnt nie mit einem (auch fragmentierten) Marker — das
# tritt nur auf, wenn im Rohtext der Doppelpunkt nach 'Str.-Kl'/'Str.-Gr' fehlt
# und die Klassen-Regex mangels Grenze bis zum nächsten Marker-Bruchstück liest
# (5 Fälle im Material). Solche Fragmente werden verworfen statt als Wert
# ausgegeben — precision-first: leer statt falsch.
_MARKER_FRAGMENT = re.compile(r"^Str\.?\s*-?\s*[KG]")


def _teile(wert: str) -> list:
    wert = re.sub(r"\s+und\s+", ", ", wert)
    return [t.strip() for t in wert.split(",")
            if t.strip() and not _MARKER_FRAGMENT.match(t.strip())]


def parse_kopf(rumpf: str):
    m = _NUMMER.match(rumpf)
    if not m:
        return None
    schl_nr = m.group(1).zfill(5)

    stadtteile = []
    ms = _STADTTEIL.search(rumpf)
    if ms:
        stadtteile = _teile(ms.group(1))

    klassen = []
    mk = _KLASSE.search(rumpf)
    if mk:
        klassen = _teile(mk.group(1))

    gruppe = ""
    mg = _GRUPPE.search(rumpf)
    if mg:
        gruppe = mg.group(1).strip().rstrip(",")

    # Rest = ab der Namensgruppe (bzw. Klasse/Nummer, falls Gruppe fehlt) bis zum
    # Ende des letzten Namensstadiums.
    start = mg.end() if mg else (mk.end() if mk else m.end())
    schwanz = rumpf[start:]
    stadien = list(_STADIUM.finditer(schwanz))
    rest = schwanz[:stadien[-1].end()] if stadien else schwanz.split(". ")[0]

    return Kopf(schl_nr=schl_nr, stadtteile=stadtteile, strassenklassen=klassen,
                namensgruppe=gruppe, rest=rest.strip())
