"""Zwei Stände von daten/strassen.csv und daten/namen.csv vergleichen.

Sicherung für Parser-Änderungen (Spec 2026-09-11, Abschnitt 5.1): Jede Änderung
gegenüber dem vorigen Stand wird je Schlüsselnummer ausgewiesen, damit nichts
stillschweigend kippt. Aufruf:

  git show HEAD:daten/strassen.csv > /tmp/alt/strassen.csv   (analog namen.csv)
  python3 -m strassen.differenz /tmp/alt daten --ausgabe docs/regression/<datum>.md
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

_KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe"]

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


def vergleiche(alt_dir, neu_dir) -> dict:
    alt_s, alt_n = _lade(alt_dir)
    neu_s, neu_n = _lade(neu_dir)
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
        # Paarweise nach Position; überzählige Stadien sind gewonnen/verloren.
        for i in range(max(len(alt_st), len(neu_st))):
            if i >= len(alt_st):
                d["stadium_gewonnen"].append({**basis, "neu": _stadium_text(neu_st[i])})
            elif i >= len(neu_st):
                d["stadium_verloren"].append({**basis, "alt": _stadium_text(alt_st[i])})
            else:
                x, y = alt_st[i], neu_st[i]
                if (x["gueltig_ab"], x["datum_praezision"]) != (y["gueltig_ab"], y["datum_praezision"]):
                    d["datum_veraendert"].append({**basis, "stadium": x["stadium"],
                                                  "alt": f"{x['gueltig_ab']} ({x['datum_praezision']})",
                                                  "neu": f"{y['gueltig_ab']} ({y['datum_praezision']})"})
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
