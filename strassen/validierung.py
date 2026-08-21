"""Drei unabhängige Selbstprüfungen des Datensatzes.

Die Schlüsselnummern sind amtlich und weitgehend fortlaufend, das Lexikon ist
alphabetisch geordnet, und die heutigen Straßennamen stehen im amtlichen
Verzeichnis. Jede Abweichung ist ein Kandidat für einen Parse- oder OCR-Fehler.
"""
import csv
import unicodedata
from collections import Counter
from pathlib import Path


_UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


def _sortierschluessel(lemma: str) -> str:
    """Wörterbuchübliche Umlaut-Expansion (ä→ae, ö→oe, ü→ue, ß→ss) statt bloßem
    Diakritika-Strip — sonst sortiert z. B. 'Lünink' wie 'Lunink' ein und bricht
    an Nachbarn wie 'Luftschacht' fälschlich die Alphabet-Prüfung (Task-6-Fund)."""
    s = lemma.lower()
    for a, b in _UMLAUTE.items():
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def pruefe_schluesselnummern(strassen) -> dict:
    nummern = [int(z["schl_nr"]) for z in strassen if str(z["schl_nr"]).isdigit()]
    zaehler = Counter(z["schl_nr"] for z in strassen)
    vorhanden = set(nummern)
    luecken = [n for n in range(min(nummern), max(nummern) + 1) if n not in vorhanden]
    return {"bereich": (min(nummern), max(nummern)),
            "anzahl": len(nummern),
            "luecken": luecken,
            "dubletten": [k for k, v in zaehler.items() if v > 1]}


def pruefe_alphabet(strassen) -> list:
    """Bekannte Grenze: vergleicht nur direkte Nachbarn (i-1, i, i+1). Zwei
    aufeinanderfolgende, in derselben falschen Reihenfolge falsch sortierte
    Lemmata bleiben unentdeckt, weil dann keines von beiden lokal aus der
    Ordnung fällt (Interface bindend, nicht umgebaut — Ruling Fix-Runde 1)."""
    auffaellig = []
    schluessel = [(_sortierschluessel(z["lemma"]), z) for z in strassen]
    for i in range(1, len(schluessel) - 1):
        vor, akt, nach = schluessel[i - 1][0], schluessel[i][0], schluessel[i + 1][0]
        if akt < vor and akt < nach and vor <= nach:
            auffaellig.append(schluessel[i][1])
    return auffaellig


def pruefe_gegen_amtlich(strassen, amtliche) -> dict:
    bestaetigt, unbekannt = 0, []
    for z in strassen:
        if _sortierschluessel(z["lemma"]) in {_sortierschluessel(a) for a in amtliche}:
            bestaetigt += 1
        else:
            unbekannt.append(z["lemma"])
    return {"bestaetigt": bestaetigt, "unbekannt": unbekannt}


def lade_amtliche(pfad) -> set:
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        return {r["strasse"].strip() for r in csv.DictReader(f) if r.get("strasse")}


def schreibe_bericht(ergebnisse: dict, pfad):
    alphabet = ergebnisse["alphabet"]
    bereits_unsicher = [z for z in alphabet if z.get("status") == "unsicher"]
    neu_auffaellig = [z for z in alphabet if z.get("status") != "unsicher"]
    z = ["# Qualitätsbericht\n",
         "Drei unabhängige Selbstprüfungen des erschlossenen Datensatzes. Die "
         "konkreten Ausreißer (Lemma, Schlüsselnummer, Grund; ohne Textzitate) "
         "stehen in [`daten/pruefung_validierung.csv`](../daten/pruefung_validierung.csv).\n",
         "## 1. Schlüsselnummern\n",
         f"- Bereich: {ergebnisse['nummern']['bereich'][0]}–"
         f"{ergebnisse['nummern']['bereich'][1]}",
         f"- erfasst: {ergebnisse['nummern']['anzahl']}",
         f"- Lücken: {len(ergebnisse['nummern']['luecken'])}",
         f"- Dubletten: {len(ergebnisse['nummern']['dubletten'])}\n",
         "## 2. Alphabetische Ordnung\n",
         f"- aus der Sortierung fallende Lemmata: {len(alphabet)}",
         f'  - davon bereits als „unsicher" gekennzeichnet: {len(bereits_unsicher)}',
         f'  - davon neu auffällig (bisher „automatisch"): {len(neu_auffaellig)}',
         "  (bekannte Grenze: die Prüfung vergleicht nur direkte Nachbarn — "
         "zwei aufeinanderfolgende, gleichsinnig falsch sortierte Lemmata "
         "bleiben unentdeckt; Fälle in daten/pruefung_validierung.csv, "
         "grund=Alphabet)\n",
         "## 3. Abgleich mit dem amtlichen Straßenverzeichnis\n",
         f"- bestätigt: {ergebnisse['amtlich']['bestaetigt']}",
         f"- nicht im Verzeichnis: {len(ergebnisse['amtlich']['unbekannt'])}",
         "  (erwartbar bei aufgehobenen Straßen — nicht automatisch ein Fehler; "
         "Fälle in daten/pruefung_validierung.csv, "
         "grund=„nicht im amtlichen Verzeichnis\")\n"]
    Path(pfad).write_text("\n".join(z) + "\n", encoding="utf-8")
