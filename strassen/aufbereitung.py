"""Rohe OCR-Seiten zu fortlaufendem, parsebarem Text aufbereiten.

Reihenfolge ist wesentlich: Erst die über Zeilenumbrüche zerrissenen Feldmarker
zusammenziehen, dann die echte Silbentrennung auflösen. Umgekehrt zerstörte die
Silbentrennungsregel die Marker ('Str.-\nKl.:' würde zu 'Str.Kl.:').
"""
import re
from pathlib import Path

# Feldmarker, die im Satz über die Zeile brechen (661 + 55 + 9 Fälle im Material)
_MARKER = [
    (re.compile(r"(Str)\.-\s*\n\s*(Kl)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Str)\.-\s*\n\s*(Gr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"(Schl)\.-\s*\n\s*(Nr)\.?:"), r"\1.-\2.:"),
    (re.compile(r"Stadt-\s*\n\s*teil"), "Stadtteil"),
]
_KOLUMNENTITEL = re.compile(r"^\s*Essener Straßen\s*$", re.MULTILINE)
_SEITENZAHL = re.compile(r"^\s*\d{1,3}\s*$", re.MULTILINE)
# Alphabet-Abschnittskopf des Lexikons (alleinstehende Zeile vor dem ersten Eintrag
# eines Buchstabens, z. B. 'A', oder als Doppelkopf 'Q,R', wenn ein Buchstabe
# keinen eigenen Abschnitt trägt, S. 267). Wird sonst ins Folgelemma gezogen
# ('A Aachener Straße' statt 'Aachener Straße', 41 Fälle über 20 Buchstaben).
# Bewusst auf Einzelbuchstaben (+ komma-getrennt) beschränkt: alleinstehende
# Zwei-Buchstaben-Zeilen OHNE Komma ('ME', 'KL' u. a.) sind im Material geprüft
# Bildrauschen, keine Abschnittsköpfe — eine Regel für "1-2 Großbuchstaben" ohne
# Komma-Bedingung würde also nichts Legitimes retten, aber das Risiko eines
# echten, bislang unbeobachteten Zwei-Buchstaben-Inhalts erhöhen.
# Auch ein einzelner Kleinbuchstabe (OCR las 'C' als 'c', S. 87 — Goldstandard
# 00540 'c Cäcilienstraße'). Von 29 solchen Zeilen im Material ist eine ein
# echter Abschnittskopf, 28 sind Randrauschen; beides darf weg.
_ABSCHNITTSKOPF = re.compile(
    r"^[ \t]*[A-Za-zÄÖÜäöü](?:[ \t]*,[ \t]*[A-ZÄÖÜ])?[ \t]*$", re.MULTILINE)
# OCR-Fehler: „ß" am Zeilenanfang wird als „B" gelesen. Nur „stra-\nBe…" (Fragment
# beginnt mit „e") wird korrigiert zu „straße…" (9 Fälle). Andere „-\nB"-Fälle
# (Komposita wie „Essen-Bredeney") bleiben unangetastet.
_OCR_FEHLER = re.compile(r"([Ss]tra)-\n\s*B(?=e)")
# Silbentrennung: Trennstrich am Zeilenende vor Kleinbuchstabe.
# Vor Großbuchstabe ist der Strich Namensbestandteil (Franz-Arens-Straße).
_TRENNUNG = re.compile(r"-\n(?=[a-zäöüß])")
# Randrauschen (Scanrand, 36 Seiten): eine Zeile nur aus Wörtern mit ≤3 Buchstaben,
# ohne Ziffer und Satzzeichen ('mm nm mm nn nn', 'EEE EEE', 'Vs u'). Wird NUR als
# erste oder letzte nichtleere Zeile einer Seite entfernt — mitten im Text könnte
# eine solche Zeile ('an der A') legitim sein.
_RANDRAUSCHEN = re.compile(r"^\s*(?:[A-Za-zÄÖÜäöüß]{1,3}\s+)*[A-Za-zÄÖÜäöüß]{1,3}\s*$")
# Stadtteil-Marker-Varianten (13 der 14 leeren Stadtteil-Felder): 'Stadt-teil',
# 'Stadttei!', 'Stadteil', 'Stadttteil', 'Stadtteit', 'StadtteilX' ohne Leerzeichen.
# Lookahead verlangt Leerzeichen/Großbuchstabe/Bindestrich danach, damit
# 'Stadtteilen' in der Prosa unangetastet bleibt.
_STADTTEIL_MARKER = re.compile(r"Stadt-?t{0,2}ei[l!t](?P<pl>e?)-?(?=[ \tA-ZÄÖÜ])")
# OCR-Blocksatz klebt 'und' zwischen zwei Namen zusammen ('FrillendorfundStoppenberg',
# Manderscheidtstraße 02191 — Goldstandard). Nur Klein-und-Groß, nie innerhalb
# eines Wortes wie 'Hundstraße'.
_UND_KLEBT = re.compile(r"([a-zäöüß])und([A-ZÄÖÜ])")


def _entferne_randrauschen(text: str) -> str:
    zeilen = text.split("\n")
    nichtleer = [i for i, z in enumerate(zeilen) if z.strip()]
    if not nichtleer:
        return text
    for i in {nichtleer[0], nichtleer[-1]}:
        if _RANDRAUSCHEN.match(zeilen[i]):
            zeilen[i] = ""
    return "\n".join(zeilen)


def bereinige(text: str) -> str:
    text = _KOLUMNENTITEL.sub("", text)
    text = _SEITENZAHL.sub("", text)
    text = _ABSCHNITTSKOPF.sub("", text)
    return _entferne_randrauschen(text)


def verbinde_zeilen(text: str) -> str:
    for muster, ersatz in _MARKER:
        text = muster.sub(ersatz, text)
    text = _OCR_FEHLER.sub(r"\1ß", text)
    text = _TRENNUNG.sub("", text)
    text = text.replace("\n", " ")
    text = _STADTTEIL_MARKER.sub(lambda m: "Stadtteil" + m.group("pl") + " ", text)
    text = _UND_KLEBT.sub(r"\1 und \2", text)
    return re.sub(r"\s+", " ", text).strip()


def lade_seiten(verzeichnis) -> list:
    seiten = []
    for pfad in sorted(Path(verzeichnis).glob("s*.txt")):
        nummer = int(pfad.stem.lstrip("s"))
        seiten.append((nummer, pfad.read_text(encoding="utf-8", errors="replace")))
    return seiten


def aufbereiten(verzeichnis) -> list:
    return [(nr, verbinde_zeilen(bereinige(roh))) for nr, roh in lade_seiten(verzeichnis)]
