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

from strassen.datum import (
    DATUMSSTEMPEL, DATUMSSTEMPEL_ANONYM, DATUMSSTEMPEL_MUSTER, SATZENDE, ist_schwach,
    position_erlaubt, unscharf_eindeutig,
)

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
_FELDENDE = r"(?<!\d)\.(?=\s|$)"
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
# gemeinsamen Satzende (datum.SATZENDE — Abkürzungspunkte 'St.', 'II.' zählen nicht)
# ODER an einem Komma/Semikolon, dem direkt (nach optionalem Leerraum) 'urspr.' oder
# der nächste Datumsstempel folgt — sonst bricht ein Stadium wie 'I. Levenhove,' (kein
# Satzende nach der römischen Zahl, kein Punkt vor dem nächsten Stempel) die ganze
# Kette ab und reißt alle folgenden Stadien mit aus kopf.rest heraus (Kämmereihude,
# Schl.-Nr. 01638, S. 185; Fix Task 12, Runde 1). Semikolon zusätzlich zu Komma, weil
# es im Material parallele Namensgeschichten trennt (Frau-Bertha-Krupp-Straße 00896,
# S. 118: '…Berthastraße; 23. September 1892: Alexstraße…', Fix Task 12, Runde 2).
# DATUMSSTEMPEL_ANONYM, weil dieselbe benannte Gruppe nicht zweimal im selben Muster
# vorkommen darf.
_NAMENSTEIL = r"(?:(?!" + SATZENDE + r")[^\d\n]){1,80}"
_STADIUM = re.compile(
    DATUMSSTEMPEL_MUSTER + r"\s*(?P<name>" + _NAMENSTEIL + r")"
    r"(?:" + SATZENDE + r"|[,;](?=\s*(?:urspr\.|" + DATUMSSTEMPEL_ANONYM + r")))"
)
_SATZENDE = re.compile(SATZENDE)
# Maximale Zeichenlänge eines Namens zwischen zwei Stempeln derselben Kette (80 Zeichen
# Name + etwas Raum für Trenner/Leerzeichen) — ersetzt die frühere, an einem strengen
# Treffer gemessene _MAX_LUECKE (Fix Task 12, Runde 2). _MAX_LUECKE maß den Abstand ab
# dem ENDE des letzten strengen `_STADIUM`-Treffers; das Kettenende verschob sich dabei
# unvorhersehbar, sobald ein einzelner Zwischenstempel aus einem der bekannten, in
# namen.py tolerierten Gründe (Semikolon statt Komma, fehlender Doppelpunkt mit
# kleingeschriebenem Namensrest) selbst nicht matchte — der Rest der eigentlich
# zusammenhängenden Kette fiel dann komplett aus `kopf.rest` heraus (sechs neue
# Regressionen in Runde 1, u. a. 00896, 00718). Die neue Regel misst stattdessen jeden
# ROHEN Stempel für sich (DATUMSSTEMPEL.finditer, unabhängig davon, ob `namen.py` ihn
# später als Namen akzeptiert) und lässt die Kette weiterlaufen, solange jeder Stempel
# höchstens _MAX_NAMENSLAENGE Zeichen nach dem Ende des vorigen Stempels beginnt — das
# reicht für den längsten Namen (80 Zeichen) plus Trenner. Ob ein einzelner
# Zwischenstempel selbst einen gültigen Namen ergibt, entscheidet weiterhin allein
# `namen.py`; ein nicht lesbarer Zwischenstempel (verstümmeltes Datum) bricht die
# Kette hier NICHT ab, sondern bleibt als Rauschen in `kopf.rest` liegen — sichtbar
# über den Prüfgrund 'Namenskette unvollständig gelesen' (Fix Task 12, Runde 1, Teil 2).
# Runde 3: 90 reichte für Frohnhauser Straße (Schl.-Nr. 00930, S. 122) nicht ganz —
# zwischen 'vor 1885: Herrenbankstraße (Umb.),' und '13. Dezember 1901:' liegen nicht
# nur ein Name, sondern ZWEI ('Herrenbankstraße (Umb.)' und, über 'urspr.:', 'Essen-
# Mülheimer-Straße (Umb.)') plus die Verbindungsworte 'gemeinsame Bezeichnung am' —
# gemessen 91 Zeichen, einen über der alten Grenze. 100 lässt dafür Raum, ohne einen
# Namen plus vollständige urspr.-Klausel um mehr als eine kurze Verbindungsphrase zu
# überschreiten.
_MAX_NAMENSLAENGE = 100


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


def _stadienkette(schwanz: str):
    """Das Ende der zusammenhängenden Namenskette direkt nach dem Kopfbereich, als
    Index in schwanz — oder None, wenn schwanz nicht mit einem Stempel beginnt (dann
    greift in parse_kopf der alte Fallback: erstes Satzende).

    Die Kette ist der Lauf ALLER rohen Datumsstempel (datum.DATUMSSTEMPEL, unabhängig
    davon, ob namen.py sie später als Namen akzeptiert), solange jeder Stempel höchstens
    _MAX_NAMENSLAENGE Zeichen nach dem Ende des vorigen Stempels — beim ersten Stempel:
    nach dem Beginn des Schwanzes — beginnt (b) UND, falls
    er 'schwach' ist (datum.ist_schwach — dieselbe Regel wie in
    namen.parse_namenskette), am Kettenanfang oder direkt nach Komma/Semikolon steht
    (a, datum.position_erlaubt). Ein
    STARKER Stempel (reguläres Datum mit Doppelpunkt oder ausdrücklichem Qualifier)
    setzt die Kette dagegen unabhängig vom vorausgehenden Text fort — der Druck trennt
    zwei Stadien im Regelfall zwar durch Komma, ebenso oft aber durch einen normalen
    Satzpunkt (Natorpstraße 02287, S. 291: '19. September 1925: Taubenstraße (Verl).
    17. März 1971: Natorpstraße.' — kein Komma vor dem letzten, namensgebenden
    Stempel). Eine Positionsregel für ALLE Stempel (Fix Task 12, Runde 2) brach genau
    dieses alltägliche Trennmuster und riss dabei das namensgebende letzte Stadium aus
    der Kette (00930, 02287). Die Positionsregel bleibt trotzdem nötig, aber nur für
    schwache Stempel: sonst zählt jedes verirrte Jahr tief in der Erläuterung
    (Zitat, Quellenangabe) als Kettenfortsetzung. Der erste STARKE Stempel, der (b)
    verletzt, oder der erste SCHWACHE Stempel, der (a) oder (b) verletzt, beendet den
    Lauf.

    Das Kettenende selbst ist NICHT einfach das Ende des letzten Laufmitglieds: dessen
    Name kann sich noch über den rohen Stempel hinaus erstrecken. Es ist das Ende des
    strengen `_STADIUM`-Treffers ab dem Start des letzten Laufmitglieds, falls der
    existiert (er endet an SATZENDE oder, Fix Runde 1, an einem Komma/Semikolon vor
    dem nächsten Stempel/'urspr.'); sonst das nächste SATZENDE nach dem Ende des
    Laufmitglieds; sonst das Ende von schwanz."""
    lauf = []
    for t in DATUMSSTEMPEL.finditer(schwanz):
        if ist_schwach(t) and not position_erlaubt(schwanz, t.start()):
            break
        # Abstandsregel, auch für den ERSTEN Stempel — dort gemessen ab Beginn des
        # Schwanzes (Abschlussreview): ein starker Stempel öffnete die Kette bisher
        # unabhängig davon, wie tief in der Erläuterung er stand. Vor einem
        # legitimen Kettenanfang liegt höchstens eine kurze Klausel ('urspr.: Alter
        # Name, gemeinsame Bezeichnung am', im Material bis ~81 Zeichen).
        vorher = lauf[-1].end() if lauf else 0
        if t.start() - vorher > _MAX_NAMENSLAENGE:
            break
        lauf.append(t)
    if not lauf:
        return None

    letzter = lauf[-1]
    m = _STADIUM.match(schwanz, letzter.start())
    if m:
        return m.end()
    ms_ende = _SATZENDE.search(schwanz, letzter.end())
    if ms_ende:
        return ms_ende.end()
    return len(schwanz)


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
    ende = _stadienkette(schwanz)
    if ende is not None:
        rest = schwanz[:ende]
    else:
        # Fallback: bis zum ersten echten Satzende — NICHT bis zum ersten '. ', das
        # die Tagesziffer eines sauber gedruckten Datums traf (38 Namensketten im
        # Material, Goldstandard: Kamerunstraße 01635).
        ms_ende = _SATZENDE.search(schwanz)
        rest = schwanz[:ms_ende.end()] if ms_ende else schwanz

    return Kopf(schl_nr=schl_nr, stadtteile=stadtteile, strassenklassen=klassen,
                namensgruppe=gruppe, rest=rest.strip(), hinweise=tuple(hinweise))
