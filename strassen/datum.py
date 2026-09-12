"""Datumsstempel eines Namensstadiums und die Satzende-Regel.

Eine Quelle für kopf.py (Abgrenzung der Namenskette) und namen.py (Parsen der
Stadien). Bis 2026-09 existierte die Datumslogik doppelt mit leicht abweichenden
Regeln; in dieser Lücke saßen der Fallback-Bug und die Tagesziffer-Grenze
(Spec 2026-09-11, Abschnitt 1).

Ein Stempel ist eine der Formen
  'dd. Monat jjjj:'   'dd, Monat jjjj:'   'dd.mm.jjjj:'   'N. Jahrhundert:' / 'N. Jahrh.:'
  'vor|nach|um|etwa|gegen jjjj:'   'jjjj:'   'jjjj/jj:'
jeweils auch mit ';' oder ',' statt ':' oder ganz ohne Trennzeichen (dann liefert
lese_datum einen Hinweis; die Positionsregel dafür setzen die Aufrufer um, s.
namen.parse_namenskette und kopf._stadienkette).

precision-first: Ein ungültiger Tag oder Monat wird nicht verworfen und nicht
geraten, sondern auf die Jahresform reduziert und mit Hinweis versehen.
"""
import re
from typing import NamedTuple

MONATE = {"Januar": 1, "Februar": 2, "März": 3, "April": 4, "Mai": 5, "Juni": 6,
          "Juli": 7, "August": 8, "September": 9, "Oktober": 10, "November": 11,
          "Dezember": 12}

# Ein Punkt ist KEIN Satzende, wenn er auf eine Ziffer ('26.'), auf 'St' ('St.
# Annental') oder auf eine römische Zahl I–IV ('II. Weberstraße') folgt. 'Ill'
# zählt zusätzlich als römisch III: die OCR verwechselt dort regelmäßig 'I' und
# 'l' ('Ill. Ziegelstraße', Kämmereihude 01638, S. 185; 'Ill. Hagen' = 'III.
# Hagen', S. 331 u. a. — 14 Belege im Material, ausnahmslos 'III.' im Sinnzusammenhang).
# Lookbehinds sind je fester Breite; \b ist nullbreit und deshalb erlaubt.
_KEIN_ABKUERZUNGSPUNKT = r"(?<!\d)(?<!\bSt)(?<!\bI)(?<!\bII)(?<!\bIII)(?<!\bIV)(?<!\bIll)"
SATZENDE = _KEIN_ABKUERZUNGSPUNKT + r"\.(?=\s+[0-9A-ZÄÖÜ]|\s*$)"

_MONAT_WORT = r"(?P<monat>[A-Za-zÄÖÜäöü]{3,9})"     # Prüfung gegen MONATE in lese_datum
_TRENNER = r"\s*(?P<trenner>:|;|,|)"                 # ':' regulär, sonst Hinweis

DATUMSSTEMPEL_MUSTER = (
    r"(?<![\d/])(?:"
    r"(?:im\s+)?(?P<jh>\d{1,2})\.\s*Jahrh(?:undert|\.)"
    r"|(?P<num_tag>\d{2})\.(?P<num_monat>\d{2})\.(?P<num_jahr>\d{4})"
    r"|(?P<tag>\d{1,3})(?P<tag_trenner>[.,])\s*" + _MONAT_WORT + r"\s+(?P<jahr_tag>\d{4})"
    r"|(?P<qualifier>vor|nach|um|etwa|gegen)\s+(?P<jahr_qual>\d{4})(?:/(?P<jahr2>\d{2}))?"
    r"|(?P<jahr_bloss>\d{4})(?:/(?P<jahr2b>\d{2}))?"
    r")(?!\d)" + _TRENNER
)
DATUMSSTEMPEL = re.compile(DATUMSSTEMPEL_MUSTER)

# Gruppenlose Form für Lookaheads: DATUMSSTEMPEL_MUSTER hat benannte Gruppen und
# darf deshalb nicht zweimal im selben Muster vorkommen (z. B. in einem Lookahead
# neben dem eigentlichen Treffer, kopf._STADIUM).
DATUMSSTEMPEL_ANONYM = re.sub(r"\(\?P<[^>]+>", "(?:", DATUMSSTEMPEL_MUSTER)

_GERICHTET = {"vor": "vor", "nach": "nach"}

HINWEIS_KOMMA_NACH_TAG = "Datum: Komma nach Tag"
HINWEIS_OHNE_DOPPELPUNKT = "Datum ohne Doppelpunkt"
HINWEIS_MONAT_KORRIGIERT = "Monatsname OCR-korrigiert"
HINWEIS_DOPPELJAHR = "Datum: Doppeljahr"
HINWEIS_TAG_UNGUELTIG = "Datum: Tag ungültig"
# Eigener Grund für ein nicht lesbares Monatswort (Abschlussreview): der Tag kann
# tadellos gedruckt sein, unlesbar ist allein der Monat — der Hinweis "Datum: Tag
# ungültig" wies dort bisher in die falsche Richtung.
HINWEIS_MONAT_UNLESBAR = "Datum: Monat unlesbar"


class Datum(NamedTuple):
    gueltig_ab: str       # ISO-Datum, Jahr (4-stellig) oder leer
    praezision: str       # tag | jahr | vor | nach | jahrhundert
    hinweis: str          # "" oder mehrere Hinweise, mit "; " verbunden
    trenner: str          # ':' ';' ',' oder ''


def lese_text(text: str):
    """Gedruckter Datumstext ('29.08.1927', 'um 1900', 'im 16. Jahrhundert', auch mit
    Trenner am Ende) -> Datum; None, wenn kein Stempelmuster passt; leer -> unbekannt.
    Gemeinsame Funktion für LLM-Vergleich und Korrektur-Overlay (Spec 2026-09-12)."""
    t = (text or "").strip()
    if not t:
        return Datum("", "unbekannt", "", "")
    m = DATUMSSTEMPEL.fullmatch(t)
    return lese_datum(m) if m else None


def lese_datum(m: re.Match) -> Datum:
    hinweise = []
    trenner = m.group("trenner")
    if trenner != ":":
        hinweise.append(HINWEIS_OHNE_DOPPELPUNKT)

    if m.group("jh"):
        jh = int(m.group("jh"))
        return Datum(f"{(jh - 1) * 100 + 1:04d}", "jahrhundert", "; ".join(hinweise), trenner)

    if m.group("num_jahr"):
        tag, monat, jahr = int(m.group("num_tag")), int(m.group("num_monat")), m.group("num_jahr")
        if 1 <= tag <= 31 and 1 <= monat <= 12:
            return Datum(f"{jahr}-{monat:02d}-{tag:02d}", "tag", "; ".join(hinweise), trenner)
        hinweise.append(HINWEIS_TAG_UNGUELTIG)
        return Datum(jahr, "jahr", "; ".join(hinweise), trenner)

    if m.group("jahr_tag"):
        return _tagesdatum(m, hinweise, trenner)

    if m.group("qualifier"):
        praezision = _GERICHTET.get(m.group("qualifier"), "jahr")
        if m.group("jahr2"):
            hinweise.append(HINWEIS_DOPPELJAHR)
        return Datum(m.group("jahr_qual"), praezision, "; ".join(hinweise), trenner)

    if m.group("jahr2b"):
        hinweise.append(HINWEIS_DOPPELJAHR)
    return Datum(m.group("jahr_bloss"), "jahr", "; ".join(hinweise), trenner)


def ist_schwach(m: re.Match) -> bool:
    """Ist der Stempel 'schwach', also leicht aus OCR-Rauschen entstanden?

    Schwach ist ein Stempel ohne regulären Doppelpunkt (Regel 15) ODER ein bloßes
    Jahr ohne ausdrücklichen Qualifier ('vor/nach/um/etwa/gegen') — geschrieben als
    'jjjj:' oder als Volldatum, dessen Tag/Monat ungültig war und das lese_datum
    deshalb auf das Jahr zurückgestuft hat. Hinter Rauschen liest sich sonst ein
    verstümmeltes Volldatum unbemerkt als stilles Jahr (Dudweilerstraße 00685,
    S. 104: 'A 0, EEE 1935:' statt '14. November 1935:'). Ein ausdrückliches
    'vor 1885:' ist dagegen bewusst so geschrieben, kein Degradat.

    Gemeinsame Regel für kopf._stadienkette (Kettenabgrenzung) und
    namen.parse_namenskette (Annahme eines Stadiums); beide müssen denselben
    Begriff verwenden, sonst weicht die Kettengrenze von den gelesenen Stadien ab.
    """
    d = lese_datum(m)
    return d.trenner != ":" or (d.praezision == "jahr" and not m.group("qualifier"))


def position_erlaubt(text: str, start: int) -> bool:
    """Darf ein SCHWACHER Stempel an dieser Position eine Kette fortsetzen?

    Nur am Kettenanfang oder direkt nach Komma bzw. Semikolon: der Druck trennt die
    Stadien einer Kette so (Semikolon trennt parallele Namensgeschichten, z. B.
    Frau-Bertha-Krupp-Straße 00896, S. 118). Ohne diese Regel zählt jedes verirrte
    Jahr tief in der Erläuterung — Zitat, Quellenangabe, Prosa wie 'Am 25. Juli 1516
    wurde' — als Stadium bzw. als Kettenfortsetzung. Für STARKE Stempel gilt sie
    nicht: die stehen im Material regelmäßig auch nach einem normalen Satzpunkt
    (Natorpstraße 02287, S. 291).
    """
    davor = text[:start].rstrip()
    return davor == "" or davor.endswith(",") or davor.endswith(";")


def _tagesdatum(m: re.Match, hinweise: list, trenner: str) -> Datum:
    jahr = m.group("jahr_tag")
    if m.group("tag_trenner") == ",":
        hinweise.append(HINWEIS_KOMMA_NACH_TAG)
    monat_nr = MONATE.get(m.group("monat"))
    if monat_nr is None:
        kandidat = unscharf_eindeutig(m.group("monat"), MONATE)
        if kandidat is None:
            hinweise.append(HINWEIS_MONAT_UNLESBAR)
            return Datum(jahr, "jahr", "; ".join(hinweise), trenner)
        hinweise.append(HINWEIS_MONAT_KORRIGIERT)
        monat_nr = MONATE[kandidat]
    tag = int(m.group("tag"))
    if not 1 <= tag <= 31:
        hinweise.append(HINWEIS_TAG_UNGUELTIG)
        return Datum(jahr, "jahr", "; ".join(hinweise), trenner)
    return Datum(f"{jahr}-{monat_nr:02d}-{tag:02d}", "tag", "; ".join(hinweise), trenner)


def unscharf_eindeutig(wort: str, kandidaten) -> str | None:
    """Der eine Kandidat mit Levenshtein-Distanz genau 1 zu wort (Groß-/
    Kleinschreibung egal); None, wenn keiner oder mehrere passen. Distanz 1 ist
    bewusst die Obergrenze: ein OCR-Fehler pro Wort ('Novemner', 'Aprit', 'Mat'),
    nicht zwei — sonst würde geraten."""
    treffer = [k for k in kandidaten if _distanz_eins(wort.lower(), k.lower())]
    return treffer[0] if len(treffer) == 1 else None


def _distanz_eins(a: str, b: str) -> bool:
    if a == b:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) == 1
    if abs(len(a) - len(b)) != 1:
        return False
    lang, kurz = (a, b) if len(a) > len(b) else (b, a)
    for i in range(len(lang)):
        if lang[:i] + lang[i + 1:] == kurz:
            return True
    return False
