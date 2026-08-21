"""Stufe 3+4 deterministisch ausführen: Selbstprüfungen und Konkordanz-Ableitung aus
den Pipeline-Ausgaben (`daten/strassen.csv`, `daten/namen.csv`) und zwei externen
Referenzquellen des Kartenprojekts erzeugen.

Vier Artefakte, byte-identisch reproduzierbar bei unveränderten Eingaben:
  - `docs/qualitaet.md`              (Selbstprüfungen, strassen/validierung.py)
  - `daten/konkordanz_1936.csv`      (Konkordanz zum Erhebungsstand 1936)
  - `daten/pruefung_konkordanz.csv`  (Konkordanz-Prüffälle)
  - `docs/erhebungsstand.md`         (Erhebungsstand-Messung, jährlich + monatsscharf)

Die Konkordanz wird bewusst NUR aus Straßen mit `status=automatisch` gebaut — der
Filter stand bisher nur in einer nicht versionierten Kommandozeile (verloren, sobald
das Terminal schließt), jetzt hier im Code: Straßen mit `status=unsicher` haben
selbst kein belastbares heutiges Lemma, ein daraus abgeleiteter Konkordanzeintrag
wäre nicht vertrauenswürdig. Dieselbe Filterung gilt für `pruefe_konkordanz`, damit
beide Funktionen (wie in `stichtag.py` dokumentiert) exakt komplementär bleiben.
"""
import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

from strassen.validierung import (
    pruefe_schluesselnummern, pruefe_alphabet, pruefe_gegen_amtlich,
    lade_amtliche, schreibe_bericht,
)
from strassen.stichtag import (
    baue_konkordanz, pruefe_konkordanz, messe_erhebungsstand,
    messe_erhebungsstand_monatlich,
)

# Externe Quellen des Kartenprojekts (nicht Teil dieses Repos, s. README,
# Abschnitt „Externe Eingaben") — Konstanten mit den bekannten Pfaden, per
# argparse überschreibbar (--adressbuch / --amtliches-verzeichnis).
ADRESSBUCH_PFAD = "/home/christos/Projekte/AdressbuchEssen-v2/data/essen1936.csv"
AMTLICHES_VERZEICHNIS_PFAD = "/home/christos/Projekte/AdressbuchEssen-v2/shared/strassen_aktuell.csv"

# Arbeitswert, begründet in docs/erhebungsstand.md (s. u.): das Fenster
# Februar 1936 bis Januar 1937 ist stabil (keine vom Adressbuch reflektierte
# Umbenennung mehr), 1936-06-30 liegt komfortabel darin.
STICHTAG = "1936-06-30"
MONATSSCHARF_VON = "1935-01"
MONATSSCHARF_BIS = "1937-12"

FELDER_KONKORDANZ = ["stadtteil", "ehemalig", "heutig", "schl_nr",
                      "datum_praezision", "quelle", "zusatz", "eindeutig"]
FELDER_PRUEFUNG_KONKORDANZ = ["buchseite", "lemma", "grund", "befund"]

# Straßenname aus der Adresse-Spalte des Adressbuchs: alles vor der ersten auf
# Whitespace folgenden Ziffer (Hausnummer), z. B. 'Grenzstr. 25' -> 'Grenzstr.'.
_STRASSENNAME_AUS_ADRESSE = re.compile(r"^(.*?)\s+\d")


def _lade_csv(pfad) -> list:
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _schreibe_csv(zeilen, pfad, felder):
    with open(Path(pfad), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=felder, extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def lade_adressbuch_strassennamen(pfad) -> set:
    """Straßennamen aus der (Tab-getrennten) Adresse-Spalte des Adressbuchs."""
    namen = set()
    with open(Path(pfad), encoding="utf-8", newline="") as f:
        for zeile in csv.DictReader(f, delimiter="\t"):
            adresse = (zeile.get("Adresse") or "").strip()
            if not adresse:
                continue
            m = _STRASSENNAME_AUS_ADRESSE.match(adresse)
            name = (m.group(1) if m else adresse).strip()
            if name:
                namen.add(name)
    return namen


def _schreibe_erhebungsstand(jaehrlich, monatlich, stichtag: str, von: str, bis: str,
                              strassen, strassen_automatisch, konkordanz,
                              pruefung_konkordanz, pfad):
    eindeutig_ja = sum(1 for k in konkordanz if k["eindeutig"] == "ja")
    eindeutig_nein = sum(1 for k in konkordanz if k["eindeutig"] == "nein")
    mit_zusatz = sum(1 for k in konkordanz if k["zusatz"])
    unsicher = len(strassen) - len(strassen_automatisch)

    z = [
        "# Erhebungsstand des Adressbuchs Essen 1936\n",
        "Misst, welchen Namensstand das Adressbuch Essen 1936 (Adressbuch-Datensatz "
        "des Kartenprojekts, siehe README, Abschnitt „Externe Eingaben\") tatsächlich "
        "abbildet, und leitet daraus die Konkordanz für das Kartenprojekt ab "
        "(`strassen/stichtag.py`, `strassen/veroeffentlichen.py`, "
        "`tests/test_stichtag.py`). Erzeugt von `python3 -m strassen.veroeffentlichen` "
        "— bei unveränderten Eingaben byte-identisch reproduzierbar.\n",
        "## Methode\n",
        "Für jede Umbenennung (Übergang von einem Namensstadium zum nächsten in "
        "`daten/namen.csv`) wird geprüft, ob das Adressbuch die alte oder die neue "
        "Namensform verwendet (Straßennamen kleingeschrieben, „str.\"/„straße\" "
        "vereinheitlicht). Stadien ohne verwertbares Datum (`datum_praezision` "
        "`unbekannt`) werden übersprungen, nie geschätzt. Für die **monatsscharfe** "
        "Auswertung zählen nur Stadien mit Tagespräzision — Jahrpräzision liefert "
        "keinen echten Monat, das würde sonst einen Monat erfinden statt ihn aus den "
        "Daten zu lesen.\n",
        "## Jährliche Auswertung\n",
        "| Jahr | alt (Adressbuch nutzt alten Namen) | neu (Adressbuch nutzt neuen Namen) |",
        "|-----:|------------------------------------:|-------------------------------------:|",
    ]
    for jahr, w in jaehrlich.items():
        z.append(f"| {jahr} | {w['alt']} | {w['neu']} |")
    z += [
        "",
        f"## Monatsscharfe Auswertung ({von} bis {bis})\n",
        "| Monat | alt | neu |",
        "|-------|----:|----:|",
    ]
    for monat, w in monatlich.items():
        z.append(f"| {monat} | {w['alt']} | {w['neu']} |")
    z += [
        "",
        "(Nur Jahre/Monate mit mindestens einer verwertbar datierten Umbenennung "
        "sind aufgeführt; für die monatsscharfe Tabelle zusätzlich nur solche mit "
        "Tagespräzision.)\n",
        "## Interpretation\n",
        "Ab Umbenennungen ab Februar 1936 reflektiert das Adressbuch keine einzige "
        "mehr — das grenzt den tatsächlichen Erhebungsschluss auf etwa **Ende 1935 "
        "bis Januar 1936** ein, plausibel für ein Werk mit Titeljahr 1936. Der als "
        f"Arbeitswert verwendete Stichtag **{stichtag}** liegt komfortabel im "
        "gesamten Zeitfenster (Februar 1936 bis Januar 1937), in dem keine weitere "
        "Umbenennung mehr auf den Datensatz einwirkt — eine engere Festlegung wäre "
        "durch die Daten nicht gedeckt und würde das Ergebnis der Konkordanz nicht "
        "ändern.\n",
        f"## Konkordanz-Ableitung (`daten/konkordanz_1936.csv`, Stichtag {stichtag})\n",
        "Die Konkordanz wird **nur aus Straßen mit `status=automatisch`** gebaut; "
        "unsichere Lemmata (`status=unsicher`) gehören nicht in die produktive "
        "Konkordanz, da ihr heutiger Name selbst nicht belastbar ist. Einträge, "
        "deren Namenskette intern widersprüchlich ist (letztes Stadium ≠ Lemma "
        "nach Zusatz-Abtrennung, mechanisches Konsistenz-Netz), landen nicht in "
        "der Konkordanz, sondern als Prüffall in `daten/pruefung_konkordanz.csv`.\n",
        f"- Straßen gesamt: {len(strassen)}",
        f"- davon `status=automatisch` (Basis der Konkordanz): {len(strassen_automatisch)}",
        f"- davon `status=unsicher` (ausgeschlossen): {unsicher}",
        f"- Konkordanzeinträge: **{len(konkordanz)}**",
        f"  - davon `eindeutig=ja`: {eindeutig_ja} / `eindeutig=nein` (Kollisionen): {eindeutig_nein}",
        f"  - davon mit Klammerzusatz (z. B. „(tlw.)\", „(Verl.)\"): {mit_zusatz}",
        f"- Prüffälle (`daten/pruefung_konkordanz.csv`): **{len(pruefung_konkordanz)}**\n",
        "Methodische Begründung der Konkordanz-Ableitung (Klammerzusätze abtrennen, "
        "Kollisionen markieren, mechanisches Konsistenz-Netz gegen unvollständige "
        "Namensketten, „(tlw.)\"-Teilangaben als informationstragend behalten): "
        "siehe die Docstrings in `strassen/stichtag.py` "
        "(`_trenne_zusatz`, `_ist_teil_zusatz`, `_kandidat_oder_pruefung`, "
        "`baue_konkordanz`).\n",
    ]
    Path(pfad).write_text("\n".join(z) + "\n", encoding="utf-8")


def main(daten_dir="daten", docs_dir="docs", adressbuch=ADRESSBUCH_PFAD,
         amtliches_verzeichnis=AMTLICHES_VERZEICHNIS_PFAD, stichtag=STICHTAG,
         monatsscharf_von=MONATSSCHARF_VON, monatsscharf_bis=MONATSSCHARF_BIS):
    daten = Path(daten_dir)
    docs = Path(docs_dir)
    docs.mkdir(parents=True, exist_ok=True)

    strassen = _lade_csv(daten / "strassen.csv")
    namen = _lade_csv(daten / "namen.csv")

    # --- Stufe 3: Validierung --------------------------------------------------
    amtliche = lade_amtliche(amtliches_verzeichnis)
    ergebnisse = {
        "nummern": pruefe_schluesselnummern(strassen),
        "alphabet": pruefe_alphabet(strassen),
        "amtlich": pruefe_gegen_amtlich(strassen, amtliche),
    }
    schreibe_bericht(ergebnisse, docs / "qualitaet.md")

    # --- Stufe 4: Konkordanz-Ableitung ------------------------------------------
    strassen_automatisch = [s for s in strassen if s.get("status") == "automatisch"]

    konkordanz = baue_konkordanz(strassen_automatisch, namen, stichtag)
    _schreibe_csv(konkordanz, daten / "konkordanz_1936.csv", FELDER_KONKORDANZ)

    pruefung_konkordanz = pruefe_konkordanz(strassen_automatisch, namen, stichtag)
    _schreibe_csv(pruefung_konkordanz, daten / "pruefung_konkordanz.csv",
                  FELDER_PRUEFUNG_KONKORDANZ)

    stadien_je_strasse = defaultdict(list)
    for z in namen:
        stadien_je_strasse[z["schl_nr"]].append(z)
    adressbuch_namen = lade_adressbuch_strassennamen(adressbuch)
    jaehrlich = messe_erhebungsstand(stadien_je_strasse, adressbuch_namen)
    monatlich = messe_erhebungsstand_monatlich(
        stadien_je_strasse, adressbuch_namen, monatsscharf_von, monatsscharf_bis)
    _schreibe_erhebungsstand(jaehrlich, monatlich, stichtag, monatsscharf_von,
                              monatsscharf_bis, strassen, strassen_automatisch,
                              konkordanz, pruefung_konkordanz, docs / "erhebungsstand.md")

    kennzahlen = {
        "schluesselnummern_dubletten": len(ergebnisse["nummern"]["dubletten"]),
        "alphabet_auffaellig": len(ergebnisse["alphabet"]),
        "amtlich_bestaetigt": ergebnisse["amtlich"]["bestaetigt"],
        "amtlich_unbekannt": len(ergebnisse["amtlich"]["unbekannt"]),
        "strassen_automatisch": len(strassen_automatisch),
        "konkordanz": len(konkordanz),
        "pruefung_konkordanz": len(pruefung_konkordanz),
    }
    print(kennzahlen)
    return kennzahlen


def _cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--daten-dir", default="daten")
    p.add_argument("--docs-dir", default="docs")
    p.add_argument("--adressbuch", default=ADRESSBUCH_PFAD)
    p.add_argument("--amtliches-verzeichnis", default=AMTLICHES_VERZEICHNIS_PFAD)
    p.add_argument("--stichtag", default=STICHTAG)
    p.add_argument("--monatsscharf-von", default=MONATSSCHARF_VON)
    p.add_argument("--monatsscharf-bis", default=MONATSSCHARF_BIS)
    a = p.parse_args()
    main(daten_dir=a.daten_dir, docs_dir=a.docs_dir, adressbuch=a.adressbuch,
         amtliches_verzeichnis=a.amtliches_verzeichnis, stichtag=a.stichtag,
         monatsscharf_von=a.monatsscharf_von, monatsscharf_bis=a.monatsscharf_bis)


if __name__ == "__main__":
    _cli()
