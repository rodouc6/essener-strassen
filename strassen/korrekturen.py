"""Korrektur-Overlay: manuell gegen den Scan geprüfte Korrekturen aus daten/korrekturen.csv
auf die Parser-Ausgabe anwenden (Spec 2026-09-12, Abschnitt 3.4).

Konvention: Wer eine Zeile einträgt, hat den GANZEN Eintrag (Kopf und Kette) gegen den
Scan geprüft. Deshalb bekommt jeder Eintrag mit mindestens einer Korrektur- oder
Bestätigungszeile status=geprueft — die höchste Stufe.

Spalten: schl_nr, feld, wert_alt, wert_neu, beleg, quelle, datum
  feld      lemma | stadtteile | strassenklasse | namensgruppe | verweis_auf
            | stadium_N_datum | stadium_N_name | stadium_N_urspruenglich | eintrag
  wert_alt  aktueller Parser-Wert in Stichprobenform (Datum z. B. 'vor 1898', '1902-05-16');
            weicht er ab, bricht der Lauf ab — die Stelle muss neu geprüft werden.
            Leer bei stadium_N_*: Stadium an Position N NACHTRAGEN (datum UND name nötig).
  wert_neu  neuer Wert; bei stadium_N_datum der GEDRUCKTE Text ('29.08.1927', 'um 1900'),
            normalisiert über datum.lese_text. Leer bei beiden Feldern eines Stadiums: STREICHEN.
  eintrag   wert_alt und wert_neu leer: Bestätigung, nur Statuswechsel.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

from strassen.datum import HINWEIS_OHNE_DOPPELPUNKT, lese_text
from strassen.goldstandard import formatiere_datum

WURZEL = Path(__file__).resolve().parent.parent
KORREKTUREN_PFAD = WURZEL / "daten" / "korrekturen.csv"
FELDER_KORREKTUREN = ["schl_nr", "feld", "wert_alt", "wert_neu", "beleg", "quelle", "datum"]
STATUS_GEPRUEFT = "geprueft"
KOPFFELDER = ("lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf")
_STADIUM = re.compile(r"^stadium_(\d+)_(datum|name|urspruenglich)$")


class KorrekturFehler(ValueError):
    pass


def lade_korrekturen(pfad=KORREKTUREN_PFAD) -> list:
    pfad = Path(pfad)
    if not pfad.is_file():
        return []
    with open(pfad, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        zeilen = list(reader)
        if reader.fieldnames != FELDER_KORREKTUREN:
            raise KorrekturFehler(
                f"korrekturen.csv: erwartete Spalten {FELDER_KORREKTUREN}, gefunden {reader.fieldnames}")
        return zeilen


def _ist(z, art):
    if art == "datum":
        return formatiere_datum(z["datum_praezision"], z["gueltig_ab"])
    if art == "name":
        return z["name"]
    return z["ist_urspruenglich"]


def _setze(z, art, wert_neu, schl, feld):
    if art == "datum":
        d = lese_text(wert_neu)
        if d is None:
            raise KorrekturFehler(f"{schl} {feld}: Datum {wert_neu!r} nicht normalisierbar")
        # precision-first: lese_text stuft unsaubere Datumsangaben zurück (ungültiger Tag,
        # OCR-korrigierter Monat) statt sie zu verwerfen. Im Overlay wäre das ein stiller
        # Datenverlust — und der Eintrag bekäme trotzdem status=geprueft.
        if [h for h in d.hinweis.split("; ") if h and h != HINWEIS_OHNE_DOPPELPUNKT]:
            raise KorrekturFehler(f"{schl} {feld}: Datum {wert_neu!r} nicht sauber lesbar "
                                  f"({d.hinweis}) — gegen den Scan prüfen")
        z["gueltig_ab"], z["datum_praezision"] = d.gueltig_ab, d.praezision
    elif art == "name":
        z["name"] = wert_neu
    else:
        if wert_neu not in ("wahr", "falsch"):
            raise KorrekturFehler(f"{schl} {feld}: erwartet 'wahr' oder 'falsch'")
        z["ist_urspruenglich"] = wert_neu


def _pruefe_alt(schl, feld, ist, soll_alt):
    if (ist or "") != (soll_alt or ""):
        raise KorrekturFehler(f"{schl} {feld}: wert_alt {soll_alt!r} ≠ Parser-Wert {ist!r} — "
                              f"Parser liest die Stelle inzwischen anders, Korrektur neu prüfen")


def wende_an(strassen: list, namen: list, korrekturen: list) -> dict:
    """Wendet alle Korrekturen an (strassen-Zeilen werden mutiert, namen in place ersetzt).

    Feldänderungen (stadium_N_datum/name/urspruenglich mit gefülltem wert_alt)
    adressieren die PARSER-Nummerierung — Position N, wie sie VOR Streichen/Einfügen
    in namen.csv steht. Nachträge (wert_alt leer) adressieren dagegen die gedruckte
    ZIEL-Position — die Nummer, die das Stadium im Ergebnis NACH Streichen/Einfügen
    tragen soll.

    Bricht eine Korrektur mit KorrekturFehler ab, können frühere Einträge dieses oder
    vorheriger Durchläufe bereits mutiert sein (kein Rollback) — Aufrufer werten das
    Ergebnis nur aus, wenn kein Fehler geworfen wurde.

    Rückgabe: {"eintraege": korrigierte Einträge, "korrekturen": angewandte Zeilen}."""
    if not korrekturen:
        return {"eintraege": 0, "korrekturen": 0}
    index = defaultdict(list)
    for z in strassen:
        index[z["schl_nr"]].append(z)
    stadien = defaultdict(list)
    for z in namen:
        stadien[z["schl_nr"]].append(z)
    for st in stadien.values():
        st.sort(key=lambda z: int(z["stadium"]))

    je_schl = defaultdict(list)
    for k in korrekturen:
        je_schl[k["schl_nr"]].append(k)

    for schl, liste in je_schl.items():
        if schl not in index:
            raise KorrekturFehler(f"{schl}: Schlüsselnummer nicht im Datensatz")
        if len(index[schl]) > 1:
            raise KorrekturFehler(f"{schl}: Schlüsselnummer mehrdeutig (Dublette) — nicht korrigierbar")
        strasse = index[schl][0]
        st = stadien[schl]
        nachtrag = defaultdict(dict)       # N -> {"datum": ..., "name": ...}
        streichen = defaultdict(set)       # N -> {"datum", "name"}
        for k in liste:
            feld, alt, neu = k["feld"], k.get("wert_alt", ""), k.get("wert_neu", "")
            if feld == "eintrag":
                if alt or neu:
                    raise KorrekturFehler(f"{schl} eintrag: Bestätigung braucht leere wert_alt/wert_neu")
                continue
            if feld in KOPFFELDER:
                _pruefe_alt(schl, feld, strasse.get(feld, ""), alt)
                strasse[feld] = neu
                continue
            m = _STADIUM.match(feld)
            if not m:
                raise KorrekturFehler(f"{schl}: unbekanntes Feld {feld!r}")
            n, art = int(m.group(1)), m.group(2)
            if n < 1:
                raise KorrekturFehler(f"{schl} {feld}: Stadiumsnummer muss ≥ 1 sein")
            if alt == "" and art in ("datum", "name"):
                nachtrag[n][art] = neu
                continue
            if n > len(st):
                raise KorrekturFehler(f"{schl} {feld}: Stadium {n} existiert nicht ({len(st)} vorhanden)")
            z = st[n - 1]
            _pruefe_alt(schl, feld, _ist(z, art), alt)
            if neu == "" and art in ("datum", "name"):
                streichen[n].add(art)
                continue
            _setze(z, art, neu, schl, feld)
        for n, arten in streichen.items():
            if arten != {"datum", "name"}:
                raise KorrekturFehler(f"{schl} stadium_{n}: Streichen braucht datum UND name mit leerem wert_neu")
        for n, teile in nachtrag.items():
            if set(teile) != {"datum", "name"}:
                raise KorrekturFehler(f"{schl} stadium_{n}: Nachtragen braucht datum UND name (wert_alt leer)")
            if not teile["datum"] or not teile["name"]:
                raise KorrekturFehler(f"{schl} stadium_{n}: Nachtragen braucht Datum und Name mit Wert")
        st = [z for i, z in enumerate(st, 1) if i not in streichen]
        for n in sorted(nachtrag):
            if n > len(st) + 1:
                raise KorrekturFehler(
                    f"{schl} stadium_{n}: Nachtragen nur bis Position {len(st) + 1} möglich "
                    f"({len(st)} Stadien vorhanden, davon ggf. bereits nachgetragen)")
            z = {"schl_nr": schl, "stadium": n, "gueltig_ab": "", "datum_praezision": "unbekannt",
                 "name": "", "ist_urspruenglich": "falsch"}
            _setze(z, "datum", nachtrag[n]["datum"], schl, f"stadium_{n}_datum")
            _setze(z, "name", nachtrag[n]["name"], schl, f"stadium_{n}_name")
            st.insert(min(n - 1, len(st)), z)
        for i, z in enumerate(st, 1):
            z["stadium"] = i
        stadien[schl] = st
        strasse["status"] = STATUS_GEPRUEFT

    reihenfolge = []
    gesehen = set()
    for z in namen:
        if z["schl_nr"] not in gesehen:
            gesehen.add(z["schl_nr"]); reihenfolge.append(z["schl_nr"])
    for schl in je_schl:
        if schl not in gesehen:
            gesehen.add(schl); reihenfolge.append(schl)
    namen[:] = [z for schl in reihenfolge for z in stadien[schl]]
    return {"eintraege": len(je_schl), "korrekturen": len(korrekturen)}
