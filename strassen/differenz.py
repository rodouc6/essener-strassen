"""Zwei Stände von daten/strassen.csv und daten/namen.csv vergleichen.

Sicherung für Parser-Änderungen (Spec 2026-09-11, Abschnitt 5.1): Jede Änderung
gegenüber dem vorigen Stand wird je Schlüsselnummer ausgewiesen, damit nichts
stillschweigend kippt. Aufruf:

  git show HEAD:daten/strassen.csv > /tmp/alt/strassen.csv   (analog namen.csv)
  python3 -m strassen.differenz /tmp/alt daten --ausgabe docs/regression/<datum>.md

vergleiche(alt, neu) akzeptiert je Seite ein Verzeichnis oder ein Tupel
(strassen, namen) mit strassen als Liste/Dict und namen als Liste/Dict.

Stadien-Zuordnung je schl_nr: zuerst werden Stadien mit identischer Signatur
(gueltig_ab, datum_praezision, name, ist_urspruenglich) zwischen alt und neu
gepaart und aus dem Vergleich entfernt (Multimengen-Zuordnung — jedes Vorkommen
einzeln). Die verbleibenden, nicht per Signatur zuordenbaren Stadien werden in
ihrer ursprünglichen Reihenfolge paarweise verglichen (datum_veraendert /
name_veraendert); überzählige Reststadien gelten als gewonnen bzw. verloren.
So wird eine mittendrin eingefügte oder entfallene Zeile nicht fälschlich als
Änderung einer unveränderten Nachbarzeile gewertet.
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

_KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf", "buchseite"]

_KATEGORIEN = [
    ("eintrag_neu", "Eintrag neu"),
    ("eintrag_entfallen", "Eintrag entfallen"),
    ("stadium_gewonnen", "Stadium gewonnen"),
    ("stadium_verloren", "Stadium verloren"),
    ("datum_veraendert", "Datum verändert"),
    ("name_veraendert", "Name verändert"),
    ("kopffeld_veraendert", "Kopffeld verändert"),
    ("status_zu_unsicher", "Status automatisch → unsicher"),
    ("status_zu_automatisch", "Status unsicher → automatisch"),
]


def als_struktur(strassen, namen):
    """Listen oder Dicts in die interne Form: strassen[schl_nr] -> Zeile,
    namen[schl_nr] -> Stadien sortiert nach 'stadium'."""
    if not isinstance(strassen, dict):
        strassen = {z["schl_nr"]: z for z in strassen}
    if not isinstance(namen, dict):
        gruppen = defaultdict(list)
        for z in namen:
            gruppen[z["schl_nr"]].append(z)
        namen = gruppen
    for stadien in namen.values():
        stadien.sort(key=lambda z: int(z["stadium"]))
    return strassen, namen


def _lade_oder_uebernimm(quelle):
    if isinstance(quelle, tuple):
        return als_struktur(*quelle)
    return _lade(quelle)


def _lade(verzeichnis):
    verzeichnis = Path(verzeichnis)
    with open(verzeichnis / "strassen.csv", encoding="utf-8", newline="") as f:
        strassen = {z["schl_nr"]: z for z in csv.DictReader(f)}
    namen = defaultdict(list)
    with open(verzeichnis / "namen.csv", encoding="utf-8", newline="") as f:
        for z in csv.DictReader(f):
            namen[z["schl_nr"]].append(z)
    for stadien in namen.values():
        stadien.sort(key=lambda z: int(z["stadium"]))
    return strassen, namen


def _stadium_text(z):
    return f"{z['gueltig_ab']} {z['name']}".strip()


def _stadium_signatur(z):
    return (z["gueltig_ab"], z["datum_praezision"], z["name"], z["ist_urspruenglich"])


def _datum_text(z):
    zusatz = ", urspr." if z["ist_urspruenglich"] == "wahr" else ""
    return f"{z['gueltig_ab']} ({z['datum_praezision']}{zusatz})"


def _paare_stadien(alt_st, neu_st):
    """Signatur-Matching (Multimenge) zuerst, Rest paarweise nach Reihenfolge."""
    neu_index_je_signatur = defaultdict(list)
    for i, z in enumerate(neu_st):
        neu_index_je_signatur[_stadium_signatur(z)].append(i)

    zugeordnet_alt, zugeordnet_neu = set(), set()
    for i, z in enumerate(alt_st):
        kandidaten = neu_index_je_signatur.get(_stadium_signatur(z))
        if kandidaten:
            zugeordnet_neu.add(kandidaten.pop(0))
            zugeordnet_alt.add(i)

    alt_rest = [z for i, z in enumerate(alt_st) if i not in zugeordnet_alt]
    neu_rest = [z for i, z in enumerate(neu_st) if i not in zugeordnet_neu]
    return alt_rest, neu_rest


def vergleiche(alt, neu) -> dict:
    alt_s, alt_n = _lade_oder_uebernimm(alt)
    neu_s, neu_n = _lade_oder_uebernimm(neu)
    d = {k: [] for k, _ in _KATEGORIEN}

    for schl in sorted(set(alt_s) | set(neu_s)):
        if schl not in alt_s:
            d["eintrag_neu"].append({"schl_nr": schl, "lemma": neu_s[schl]["lemma"]})
            continue
        if schl not in neu_s:
            d["eintrag_entfallen"].append({"schl_nr": schl, "lemma": alt_s[schl]["lemma"]})
            continue
        a, n = alt_s[schl], neu_s[schl]
        basis = {"schl_nr": schl, "lemma": a["lemma"]}

        for feld in _KOPFFELDER:
            if a[feld] != n[feld]:
                d["kopffeld_veraendert"].append({**basis, "feld": feld, "alt": a[feld], "neu": n[feld]})
        if a["status"] == "automatisch" and n["status"] == "unsicher":
            d["status_zu_unsicher"].append(basis)
        elif a["status"] == "unsicher" and n["status"] == "automatisch":
            d["status_zu_automatisch"].append(basis)

        alt_st, neu_st = alt_n.get(schl, []), neu_n.get(schl, [])
        alt_rest, neu_rest = _paare_stadien(alt_st, neu_st)
        # Reststadien (ohne Signatur-Treffer) paarweise nach Reihenfolge;
        # überzählige Reststadien sind gewonnen/verloren.
        for i in range(max(len(alt_rest), len(neu_rest))):
            if i >= len(alt_rest):
                d["stadium_gewonnen"].append({**basis, "neu": _stadium_text(neu_rest[i])})
            elif i >= len(neu_rest):
                d["stadium_verloren"].append({**basis, "alt": _stadium_text(alt_rest[i])})
            else:
                x, y = alt_rest[i], neu_rest[i]
                if (x["gueltig_ab"], x["datum_praezision"], x["ist_urspruenglich"]) != \
                   (y["gueltig_ab"], y["datum_praezision"], y["ist_urspruenglich"]):
                    d["datum_veraendert"].append({**basis, "stadium": x["stadium"],
                                                  "alt": _datum_text(x), "neu": _datum_text(y)})
                if x["name"] != y["name"]:
                    d["name_veraendert"].append({**basis, "stadium": x["stadium"],
                                                 "alt": x["name"], "neu": y["name"]})
    return d


def formatiere_bericht(diff: dict) -> str:
    zeilen = ["# Differenzbericht\n", "| Kategorie | Anzahl |", "|---|--:|"]
    for k, titel in _KATEGORIEN:
        zeilen.append(f"| {titel} | {len(diff[k])} |")
    for k, titel in _KATEGORIEN:
        if not diff[k]:
            continue
        zeilen += ["", f"## {titel}\n"]
        for e in diff[k]:
            rest = "; ".join(f"{f}: {e[f]}" for f in e if f not in ("schl_nr", "lemma"))
            zeilen.append(f"- {e['schl_nr']} {e['lemma']}" + (f" — {rest}" if rest else ""))
    return "\n".join(zeilen) + "\n"


def _cli():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("alt_dir")
    p.add_argument("neu_dir")
    p.add_argument("--ausgabe", help="Markdown-Datei; ohne Angabe nur Konsole")
    a = p.parse_args()
    bericht = formatiere_bericht(vergleiche(a.alt_dir, a.neu_dir))
    if a.ausgabe:
        Path(a.ausgabe).parent.mkdir(parents=True, exist_ok=True)
        Path(a.ausgabe).write_text(bericht, encoding="utf-8")
    print(bericht)


if __name__ == "__main__":
    _cli()
