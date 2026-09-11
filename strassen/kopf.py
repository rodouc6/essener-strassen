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

from strassen.datum import DATUMSSTEMPEL_MUSTER, SATZENDE, lese_datum, unscharf_eindeutig

# Der Ziffernblock der Schlüsselnummer wird gelegentlich vom OCR mit einem
# Leerzeichen mitten in der Zahl zerrissen ('01 544'). Ohne Toleranz brach
# die alte Fassung (\d{1,5}) am ersten Fragment ab ('01') — mehrere
# verschiedene Straßen kollidierten dadurch auf derselben, zu kurzen Nummer
# (u. a. 11 Straßen auf 00001; Hachestraße '011 52' unauffällig zu 00011
# statt 01152). Bis zu 5 optionale Leerzeichen zwischen den Ziffern werden
# toleriert; nach dem Entfernen der Leerzeichen wird auf 1–5 Ziffern
# validiert (parse_kopf) — mehr als 5 Ziffern ergeben lieber keinen Kopf
# (None) als eine geratene Nummer (precision-first).
_NUMMER = re.compile(r"^\s*(\d(?:[ ]?\d){0,5})\b")

# Marker-Bausteine, roh (ohne Gruppen) zur Wiederverwendung in Lookaheads.
# 'S[tl]r?' toleriert neben 'Str' auch das fehlende 'r' ('St.-Gr.:', 4 Fälle
# im Material, u. a. Helenenstraße Schl.-Nr. 01261) und die l/I-Verwechslung
# an zweiter Stelle — ohne die blieb z. B. namensgruppe leer statt gefüllt.
_M_STR = r"S[tl]r?[.:]?\s*-?\s*"
# Klassen-Marker: 'Kl', 'KI', 'KL' (Adolfstraße 00015 u. a., 4 Fälle), 'K.' (Amselweg
# 00265, 9 Fälle), 'Kt' (An den Friedhöfen 00150, 2 Fälle); Trenner ':' oder ';',
# auch doppelt ('Str.-Kl.;:', Brandstorstraße 00421). 8 Fälle mit ';' ließen die
# Straßenklasse bisher leer (Goldstandard: Cäcilienstraße 00540).
_M_KLASSE = _M_STR + r"K[lILt]?\.?\s*[:;]+"
# 'Gr?' toleriert zusätzlich das fehlende zweite 'r' ('Str.-G.:', Ilse-Menz-
# Weg Schl.-Nr. 00700); '[:;]' toleriert ein Semikolon statt Doppelpunkt
# nach dem Marker ('Str.-Gr.;', St.-Ingbert-Höhe Schl.-Nr. 02728) — beide
# ließen namensgruppe bisher leer und die nachfolgende _KLASSE-Suche (ohne
# erkannten Grenzmarker) blutete in die Namenskette hinein.
_M_GRUPPE = _M_STR + r"Gr?\.?\s*[:;]"

# Feldende: ein Punkt mit Leerzeichen, der NICHT auf eine Ziffer folgt — sonst
# springt die Grenze auf die Tagesziffer eines Datums ('14. Dezember', An der
# Blumenwiese 01552; 46 Namensgruppen im Material endeten so auf einer Zahl).
_FELDENDE = r"(?<!\d)\.\s"
# Namensgruppe endet außerdem vor einer Tagesziffer (mit optionalem OCR-Stern
# '*03.', Eligiushöhe 00756) — auch dann, wenn das Datum dahinter verstümmelt ist
# (Overhammshof 02356: '21. Januar mm nm …'). So bleibt die Namensgruppe sauber und
# das kaputte Datum landet sichtbar im Rest statt unsichtbar in der Gruppe.
_TAGESZIFFER = r",?\s*\*?\d{1,3}[.,]\s"

_STADTTEIL = re.compile(
    r"Stadtteile?\s+(.+?)(?=,?\s*" + _M_KLASSE + r"|,?\s*" + _M_GRUPPE + r"|" + _FELDENDE + r"|$)"
)
_KLASSE = re.compile(_M_KLASSE + r"\s*(.+?)(?=,?\s*" + _M_GRUPPE + r"|" + _FELDENDE + r"|$)")
_GRUPPE = re.compile(
    _M_GRUPPE + r"\s*(.+?)"
    r"(?=,?\s*(?:urspr\.|" + DATUMSSTEMPEL_MUSTER + r")|" + _TAGESZIFFER + r"|" + _FELDENDE + r"|$)"
)
# Namensteil eines Stadiums in der strengen Kettenerkennung: keine Ziffern, endet am
# gemeinsamen Satzende (datum.SATZENDE — Abkürzungspunkte 'St.', 'II.' zählen nicht).
_NAMENSTEIL = r"(?:(?!" + SATZENDE + r")[^\d\n]){1,80}"
_STADIUM = re.compile(DATUMSSTEMPEL_MUSTER + r"\s*(?P<name>" + _NAMENSTEIL + r")" + SATZENDE)
_SATZENDE = re.compile(SATZENDE)
# Maximale Lücke zwischen zwei Stadien, damit sie noch als zusammenhängende
# Namenskette direkt nach dem Kopf gelten. Auch mit der Monatsnamen-Beschränkung
# bleibt ein Rest-Risiko: ein echtes Datum mit echtem Monat und Doppelpunkt tief
# in der Erläuterung (z. B. ein Zitat oder eine Quellenangabe). Ein Sprung über
# mehr als diese Lücke gilt als Erläuterungstext, nicht als Fortsetzung der
# Namenskette.
_MAX_LUECKE = 40


class Kopf(NamedTuple):
    schl_nr: str
    stadtteile: list
    strassenklassen: list
    namensgruppe: str
    rest: str
    hinweise: tuple = ()


# Ein echter Feldwert beginnt nie mit einem (auch fragmentierten) Marker — das
# tritt nur auf, wenn im Rohtext der Doppelpunkt nach 'Str.-Kl'/'Str.-Gr' fehlt
# und die Klassen-Regex mangels Grenze bis zum nächsten Marker-Bruchstück liest
# (5 Fälle im Material). Solche Fragmente werden verworfen statt als Wert
# ausgegeben — precision-first: leer statt falsch.
_MARKER_FRAGMENT = re.compile(r"^" + _M_STR + r"[KG]")

# Geschlossenes Vokabular der Straßenklassen (Auszählung strassen.csv 2026-09-11:
# Gemeindestraße 3.059, Landstraße 93, Kreisstraße 39, Hauptstraße 22, Bundesstraße 15;
# Mehrfachnennungen als Kombinationen daraus). Fehlt der Marker 'Str.-Kl.:' ganz, aber
# ein Wort aus diesem Vokabular steht zwischen Stadtteil-Angabe und 'Str.-Gr.:', wird
# es übernommen — mit Hinweis, weil der Marker fehlt (13 Fälle, z. B. Eibergweg 00733).
STRASSENKLASSEN = ("Gemeindestraße", "Kreisstraße", "Landstraße", "Hauptstraße",
                   "Bundesstraße")
_KLASSENWORT = re.compile(r"\b(" + "|".join(STRASSENKLASSEN) + r")\b")

HINWEIS_KLASSE_OHNE_MARKER = "Straßenklasse ohne Marker"
HINWEIS_KLASSE_KORRIGIERT = "Straßenklasse OCR-korrigiert"


def _position_erlaubt(schwanz: str, start: int) -> bool:
    davor = schwanz[:start].rstrip()
    return davor == "" or davor.endswith(",")


def _stadienkette(schwanz: str) -> list:
    """Nur eine ununterbrochene Kette von Stadien direkt nach dem Kopfbereich
    akzeptieren (Lücke ≤ _MAX_LUECKE). Stempel ohne regulären Doppelpunkt zählen nur
    am Kettenanfang oder nach Komma und mit großgeschriebenem Namen (Spec Regel 15) —
    dieselbe Positionsregel wie namen.parse_namenskette. Ein bloßes Jahr (geschrieben
    als 'jjjj:' ODER ein Volldatum mit ungültigem Tag/Monat, das lese_datum deshalb
    auf das Jahr zurückstuft — nicht aber ein ausdrückliches 'vor/nach/um/etwa/gegen
    jjjj:') unterliegt derselben Regel IMMER, auch mit Doppelpunkt: es ist der
    schwächste Stempel und degradiert hinter Rauschen sonst ein verstümmeltes
    Volldatum unbemerkt zu einem stillen Jahr (Dudweilerstraße 00685, S. 104: 'A 0,
    EEE 1935:' statt '14. November 1935:')."""
    kette = []
    for t in _STADIUM.finditer(schwanz):
        d = lese_datum(t)
        schwach = d.praezision == "jahr" and not t.group("qualifier")
        if t.group("trenner") != ":" or schwach:
            if not _position_erlaubt(schwanz, t.start()) or not t.group("name").strip()[:1].isupper():
                continue
        if kette and t.start() - kette[-1].end() > _MAX_LUECKE:
            break
        kette.append(t)
    return kette


def _teile(wert: str) -> list:
    wert = re.sub(r"\s+und\s+", ", ", wert)
    return [t.strip() for t in wert.split(",")
            if t.strip() and not _MARKER_FRAGMENT.match(t.strip())]


def parse_kopf(rumpf: str):
    m = _NUMMER.match(rumpf)
    if not m:
        return None
    ziffern = m.group(1).replace(" ", "")
    if not (1 <= len(ziffern) <= 5):
        return None
    schl_nr = ziffern.zfill(5)
    hinweise = []

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

    if not klassen and mg:
        # Regel 19: Klassenwort ohne Marker, nur im Bereich vor 'Str.-Gr.:'. Ohne
        # 'Str.-Kl.:' liest _STADTTEIL die Klassenwörter als weitere komma-getrennte
        # Glieder mit ('Stadtteil Freisenbruch, Gemeindestraße', Eibergweg 00733) —
        # sie stehen darum am Ende der bereits geteilten stadtteile-Liste und werden
        # von dort abgetrennt, exakt gegen das geschlossene Vokabular geprüft (keine
        # OCR-Toleranz ohne Marker, precision-first). Fehlt eine Stadtteil-Angabe
        # ganz, wird stattdessen der Rohtext vor 'Str.-Gr.:' durchsucht.
        if stadtteile:
            # Nimmt an, dass Klassenwörter zusammenhängend am Ende der
            # Stadtteil-Liste stehen (so beobachtet in allen 13 Korpus-Fällen).
            ende = len(stadtteile)
            while ende > 0 and stadtteile[ende - 1] in STRASSENKLASSEN:
                ende -= 1
            if ende < len(stadtteile):
                klassen = stadtteile[ende:]
                stadtteile = stadtteile[:ende]
                hinweise.append(HINWEIS_KLASSE_OHNE_MARKER)
        else:
            gefunden = _KLASSENWORT.findall(rumpf[m.end():mg.start()])
            if gefunden:
                klassen = gefunden
                hinweise.append(HINWEIS_KLASSE_OHNE_MARKER)

    # Regel 20: ein OCR-Fehler im Klassenwert ('Gemeindstraße') wird auf das
    # Vokabular korrigiert, mit Hinweis; zwei Fehler bleiben wie gelesen.
    korrigiert = []
    for klasse in klassen:
        if klasse in STRASSENKLASSEN:
            korrigiert.append(klasse)
            continue
        kandidat = unscharf_eindeutig(klasse, STRASSENKLASSEN)
        if kandidat:
            korrigiert.append(kandidat)
            if HINWEIS_KLASSE_KORRIGIERT not in hinweise:
                hinweise.append(HINWEIS_KLASSE_KORRIGIERT)
        else:
            korrigiert.append(klasse)
    klassen = korrigiert

    start = mg.end() if mg else (mk.end() if mk else m.end())
    schwanz = rumpf[start:]
    stadien = _stadienkette(schwanz)
    if stadien:
        rest = schwanz[:stadien[-1].end()]
    else:
        # Fallback: bis zum ersten echten Satzende — NICHT bis zum ersten '. ', das
        # die Tagesziffer eines sauber gedruckten Datums traf (38 Namensketten im
        # Material, Goldstandard: Kamerunstraße 01635).
        ms_ende = _SATZENDE.search(schwanz)
        rest = schwanz[:ms_ende.end()] if ms_ende else schwanz

    return Kopf(schl_nr=schl_nr, stadtteile=stadtteile, strassenklassen=klassen,
                namensgruppe=gruppe, rest=rest.strip(), hinweise=tuple(hinweise))
