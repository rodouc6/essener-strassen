"""Antworten der LLM-Lesung mit dem Parser vergleichen (Spec 2026-09-12, Abschnitt 3.3).

Die Modelle sind unabhängige zweite Leser; sie ändern nie den Status. Ausgaben:
daten/pruefung_llm.csv (eine Zeile je abweichendem Feld, Eingabemaske für Korrekturen),
docs/llm_lesung.md (Kennzahlen), docs/goldstandard/ergebnis_llm.md (Messung).

  python3 -m strassen.llm_vergleich pruefliste  [--antworten-dir DIR]
  python3 -m strassen.llm_vergleich goldstandard --modell NAME
  python3 -m strassen.llm_vergleich uebernehmen [--datum JJJJ-MM-TT]
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from strassen.datum import lese_text
from strassen.differenz import als_struktur, vergleiche
from strassen.goldstandard import formatiere_datum
from strassen.korrekturen import FELDER_KORREKTUREN

WURZEL = Path(__file__).resolve().parent.parent
ANTWORTEN_DIR = WURZEL / "llm" / "antworten"
DATEN_DIR = WURZEL / "daten"
PRUEFLISTE_PFAD = DATEN_DIR / "pruefung_llm.csv"
KENNZAHLEN_PFAD = WURZEL / "docs" / "llm_lesung.md"
STATUS_MODELL = "modell"
KURZNAMEN = ("qwen", "mistral")
KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf"]
GRUND_DATUM = "Datum nicht normalisierbar"
GRUND_STADIEN = "Stadien nicht als Liste"

_UNVOLLSTAENDIG = "_unvollstaendig"   # interne Markierung, wird nicht geschrieben


def kurzname(modell: str) -> str:
    for k in KURZNAMEN:
        if k in modell.lower():
            return k
    raise ValueError(f"kein Kurzname für Modell {modell!r} (erwartet: {', '.join(KURZNAMEN)})")


def _text(wert) -> str:
    if isinstance(wert, list):
        return "; ".join(str(w).strip() for w in wert if str(w).strip())
    return str(wert or "").strip()


def _schl_nr(wert) -> str:
    t = _text(wert)
    return t.zfill(5) if t.isdigit() else t     # führende Nullen sind Formatierung, keine Lesung


def ist_unvollstaendig(strasse: dict) -> bool:
    return bool(strasse.get(_UNVOLLSTAENDIG))


def normalisiere_antwort(antwort: dict):
    """Eine Antwortdatei -> (strassen, namen, probleme) in Datensatzform."""
    eintraege = antwort.get("eintraege")
    buchseite = int(antwort.get("buchseite") or 0)
    if not eintraege:
        return [], [], []
    strassen, namen, probleme = [], [], []
    for e in eintraege:
        schl = _schl_nr(e.get("schl_nr"))
        strassen.append({
            "schl_nr": schl, "lemma": _text(e.get("lemma")),
            "stadtteile": _text(e.get("stadtteile")), "strassenklasse": _text(e.get("strassenklasse")),
            "namensgruppe": _text(e.get("namensgruppe")), "verweis_auf": _text(e.get("verweis_auf")),
            "buchseite": buchseite, "status": STATUS_MODELL,
            _UNVOLLSTAENDIG: bool(e.get("unvollstaendig"))})
        stadien = e.get("stadien") or []
        if not isinstance(stadien, list):
            probleme.append({"schl_nr": schl, "buchseite": buchseite, "feld": "stadien",
                             "text": str(stadien)[:200], "grund": GRUND_STADIEN})
            continue
        for i, s in enumerate(stadien, 1):
            if not isinstance(s, dict):
                probleme.append({"schl_nr": schl, "buchseite": buchseite, "feld": f"stadium_{i}",
                                 "text": str(s)[:200], "grund": GRUND_STADIEN})
                continue
            text = _text(s.get("datum"))
            d = lese_text(text)
            if d is None:
                probleme.append({"schl_nr": schl, "buchseite": buchseite, "feld": f"stadium_{i}_datum",
                                 "text": text, "grund": GRUND_DATUM})
                gueltig_ab, praezision = "", "unbekannt"
            else:
                gueltig_ab, praezision = d.gueltig_ab, d.praezision
            namen.append({"schl_nr": schl, "stadium": i, "gueltig_ab": gueltig_ab,
                          "datum_praezision": praezision, "name": _text(s.get("name")),
                          "ist_urspruenglich": "wahr" if s.get("urspruenglich") else "falsch"})
    return strassen, namen, probleme


def lade_antworten(antworten_dir, modell: str) -> dict:
    """Buchseite -> Antwortdatei (nur vorhandene Seiten)."""
    ordner = Path(antworten_dir) / modell
    antworten = {}
    for pfad in sorted(ordner.glob("s*.json")):
        a = json.loads(pfad.read_text(encoding="utf-8"))
        antworten[int(pfad.stem.lstrip("s"))] = a
    return antworten


FELDER_PRUEFLISTE = ["schl_nr", "buchseite", "feld", "wert_parser", "wert_qwen", "wert_mistral",
                     "status_parser", "einig", "korrektur", "beleg"]
_EINIG_RANG = {"beide": 0, "eines": 1, "unlesbar": 2}
_STADIUMFELD = re.compile(r"^stadium_(\d+)(?:_(datum|name|urspruenglich))?$")


def _stadium_text(z) -> str:
    return f"{formatiere_datum(z['datum_praezision'], z['gueltig_ab'])} {z['name']}".strip()


def _stadium_text_roh(z) -> str:
    """Wie differenz._stadium_text: unformatiertes gueltig_ab (ohne datum_praezision).
    Zum Abgleich von stadium_gewonnen/stadium_verloren, deren e['alt']/e['neu'] genau
    so gebildet werden — formatiere_datum() liefert dort ein anderes Klartext-Ergebnis
    (z. B. Präfix 'vor'/'nach' oder '(urspr., kein Datum)'), das nie träfe."""
    return f"{z['gueltig_ab']} {z['name']}".strip()


def feldwert(strassen: dict, namen: dict, schl_nr: str, feld: str):
    """Wert eines Prüffelds in der Form der Goldstandard-Stichprobe; None wenn fehlend."""
    s = strassen.get(schl_nr)
    if s is None:
        return None
    if feld == "eintrag":
        return s["lemma"]
    m = _STADIUMFELD.match(feld)
    if not m:
        return s.get(feld)
    n, art = int(m.group(1)), m.group(2)
    stadien = namen.get(schl_nr, [])
    if n > len(stadien):
        return None
    z = stadien[n - 1]
    if art == "datum":
        return formatiere_datum(z["datum_praezision"], z["gueltig_ab"])
    if art == "name":
        return z["name"]
    if art == "urspruenglich":
        return z["ist_urspruenglich"]
    return _stadium_text(z)


def _abweichungen(parser_s, parser_n, modell_s, modell_n) -> dict:
    """(schl_nr, feld) -> True für jedes Feld, in dem das Modell vom Parser abweicht.
    Nutzt differenz.vergleiche (Parser = alt, Modell = neu)."""
    d = vergleiche((parser_s, parser_n), (modell_s, modell_n))
    abw = {}
    for e in d["eintrag_neu"] + d["eintrag_entfallen"]:
        abw[(e["schl_nr"], "eintrag")] = True
    for e in d["kopffeld_veraendert"]:
        if e["feld"] != "buchseite":
            abw[(e["schl_nr"], e["feld"])] = True
    for e in d["datum_veraendert"]:
        # e['alt']/e['neu'] sind differenz._datum_text: 'gueltig_ab (praezision[, urspr.])'.
        # 'datum_veraendert' feuert auch, wenn nur ist_urspruenglich abweicht (Kernteil ohne
        # den ', urspr.'-Zusatz dann aber gleich) — das darf keine Phantom-Datumszeile ergeben.
        n = e["stadium"]
        alt_kern = e["alt"].replace(", urspr.", "")
        neu_kern = e["neu"].replace(", urspr.", "")
        if alt_kern != neu_kern:
            abw[(e["schl_nr"], f"stadium_{n}_datum")] = True
        if (", urspr." in e["alt"]) != (", urspr." in e["neu"]):
            abw[(e["schl_nr"], f"stadium_{n}_urspruenglich")] = True
    for e in d["name_veraendert"]:
        abw[(e["schl_nr"], f"stadium_{e['stadium']}_name")] = True
    for e in d["stadium_verloren"]:
        n = _stadium_index(parser_n.get(e["schl_nr"], []), e["alt"])
        abw[(e["schl_nr"], f"stadium_{n}")] = True
    for e in d["stadium_gewonnen"]:
        n = _stadium_index(modell_n.get(e["schl_nr"], []), e["neu"])
        abw[(e["schl_nr"], f"stadium_{n}")] = True
    return abw


def _stadium_index(stadien, text) -> str:
    for z in stadien:
        if _stadium_text_roh(z) == text:
            return str(int(z["stadium"]))
    return "?"   # nicht zuordenbar — sichtbar kennzeichnen statt eine falsche Nummer zu raten


def _ist_abweichung(abw: dict, schl: str, feld: str) -> bool:
    """(schl, feld) gegen abw prüfen; ein verlorenes/gewonnenes ganzes Stadium
    (Schlüssel 'stadium_N' ohne Suffix) deckt dabei auch dessen Teilfelder
    ('stadium_N_datum' usw.) ab."""
    if (schl, feld) in abw:
        return True
    m = _STADIUMFELD.match(feld)
    return bool(m and m.group(2) and (schl, f"stadium_{m.group(1)}") in abw)


def _felder_des_eintrags(strassen, namen, schl_nr, nur_kopf=False) -> list:
    felder = list(KOPFFELDER)
    if not nur_kopf:
        for z in namen.get(schl_nr, []):
            felder += [f"stadium_{z['stadium']}_datum", f"stadium_{z['stadium']}_name"]
    return felder


def _modell_aufbereiten(m: dict):
    """Antworten eines Modells laden und normalisieren.
    -> (m_s, m_n, gelesen: set[int], unlesbar: int, probleme: list)."""
    strassen, namen, probleme = [], [], []
    gelesen = set()
    unlesbar = 0
    for buchseite, antwort in m["antworten"].items():
        if antwort.get("fehler") == "unlesbar" or antwort.get("eintraege") is None:
            unlesbar += 1
            continue
        gelesen.add(int(buchseite))
        s, n, pr = normalisiere_antwort(antwort)
        strassen += s; namen += n; probleme += pr
    m_s, m_n = als_struktur(strassen, namen)
    return m_s, m_n, gelesen, unlesbar, probleme


def _kennzahlen(p_s_teil, p_n_teil, m_s, unvollst, abw, gelesen, unlesbar, probleme) -> dict:
    ueber = defaultdict(lambda: defaultdict(lambda: {"verglichen": 0, "gleich": 0}))
    for schl, z in p_s_teil.items():
        if schl not in m_s:
            continue
        for feld in _felder_des_eintrags(p_s_teil, p_n_teil, schl, nur_kopf=schl in unvollst):
            typ = re.sub(r"^stadium_\d+_", "stadium_", feld)
            e = ueber[z["status"]][typ]
            e["verglichen"] += 1
            e["gleich"] += not _ist_abweichung(abw, schl, feld)
    return {
        "seiten_gelesen": len(gelesen), "seiten_unlesbar": unlesbar,
        "eintraege_modell": len(m_s),
        "eintraege_fehlend": sum(1 for schl in p_s_teil if schl not in m_s),
        "eintraege_nur_modell": sum(1 for schl in m_s if schl not in p_s_teil),
        "datum_nicht_normalisierbar": len(probleme),
        "uebereinstimmung": {st: dict(f) for st, f in ueber.items()},
    }


def _zeile(schl, feld, p_s, p_n, seite_je_schl, daten, gelesen, problem_werte) -> dict:
    buchseite = seite_je_schl.get(schl) or next(
        (int(daten[k][0][schl]["buchseite"]) for k in daten if schl in daten[k][0]), "")
    zeile = {"schl_nr": schl, "buchseite": buchseite, "feld": feld,
             "wert_parser": feldwert(p_s, p_n, schl, feld) or "",
             "status_parser": p_s[schl]["status"] if schl in p_s else "",
             "korrektur": "", "beleg": ""}
    werte, lesbar = {}, True
    for kurz in KURZNAMEN:
        if kurz not in daten or int(buchseite or 0) not in gelesen.get(kurz, set()):
            werte[kurz] = ""
            lesbar = False
        else:
            ersatz = problem_werte.get(kurz, {}).get((schl, feld))
            werte[kurz] = ersatz if ersatz is not None else (feldwert(*daten[kurz], schl, feld) or "")
        zeile[f"wert_{kurz}"] = werte[kurz]
    if not lesbar:
        zeile["einig"] = "unlesbar"
    elif len(set(werte.values())) == 1 and werte[KURZNAMEN[0]] != zeile["wert_parser"]:
        zeile["einig"] = "beide"
    else:
        zeile["einig"] = "eines"
    return zeile


def baue_pruefliste(parser, modelle: dict):
    """parser = (strassen, namen) des Parsers; modelle = Kurzname -> {"antworten": {buchseite: antwort}}.
    Liefert (zeilen, kennzahlen). Verglichen werden nur Buchseiten, die das jeweilige Modell
    gelesen hat; unlesbare Seiten zählen als nicht gelesen. Nicht normalisierbare Modelldaten
    (Datum, Stadien-Struktur) erscheinen unabhängig von 'unvollstaendig' als eigene Zeile."""
    p_s, p_n = als_struktur(*parser)
    seite_je_schl = {schl: int(z["buchseite"]) for schl, z in p_s.items()}
    daten, kennzahlen, gelesen, abweichungen, problem_werte = {}, {}, {}, {}, {}

    for kurz, m in modelle.items():
        m_s, m_n, gelesen[kurz], unlesbar, probleme = _modell_aufbereiten(m)
        daten[kurz] = (m_s, m_n)
        # Parser-Ausschnitt: nur gelesene Seiten; Modellketten unvollständiger Einträge ausblenden
        p_s_teil = {schl: z for schl, z in p_s.items() if seite_je_schl[schl] in gelesen[kurz]}
        p_n_teil = {schl: p_n.get(schl, []) for schl in p_s_teil}
        unvollst = {schl for schl, z in m_s.items() if ist_unvollstaendig(z)}
        m_n_vgl = {schl: ([] if schl in unvollst else st) for schl, st in m_n.items()}
        p_n_vgl = {schl: ([] if schl in unvollst else st) for schl, st in p_n_teil.items()}
        abweichungen[kurz] = _abweichungen(p_s_teil, p_n_vgl, m_s, m_n_vgl)

        problem_werte[kurz] = {}
        for p in probleme:
            schluessel = (p["schl_nr"], p["feld"])
            anzeige = (f"{p['text']} (nicht normalisierbar)" if p["grund"] == GRUND_DATUM
                      else f"{p['text']} (nicht als Liste)")
            abweichungen[kurz][schluessel] = True
            problem_werte[kurz][schluessel] = anzeige

        kennzahlen[kurz] = _kennzahlen(p_s_teil, p_n_teil, m_s, unvollst, abweichungen[kurz],
                                       gelesen[kurz], unlesbar, probleme)

    alle = set().union(*abweichungen.values()) if abweichungen else set()
    zeilen = [_zeile(schl, feld, p_s, p_n, seite_je_schl, daten, gelesen, problem_werte)
             for schl, feld in alle]
    zeilen.sort(key=lambda z: (_EINIG_RANG[z["einig"]], z["schl_nr"], z["feld"]))
    return zeilen, kennzahlen


def schreibe_pruefliste(zeilen, pfad=PRUEFLISTE_PFAD):
    Path(pfad).parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FELDER_PRUEFLISTE, extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def formatiere_kennzahlen_md(kennzahlen: dict) -> str:
    z = ["# Unabhängige LLM-Lesung — Kennzahlen\n",
         "Zwei bildfähige Modelle haben die Buchseiten unabhängig vom Parser gelesen (nur das",
         "Seitenbild, kein OCR-Text). Die Modelle **verändern den Status nicht** (Option A der",
         "Spec 2026-09-12); Abweichungen stehen in `daten/pruefung_llm.csv` zur manuellen Prüfung.",
         "Beim Modell fehlende Einträge zählen in `eintraege_fehlend`, nicht in der",
         "Übereinstimmungsquote — diese misst nur Felder beiderseits vorhandener Einträge.\n"]
    for kurz, k in kennzahlen.items():
        z += [f"## Modell `{kurz}`\n",
              f"- Seiten gelesen: {k['seiten_gelesen']}, unlesbar: {k['seiten_unlesbar']}",
              f"- Einträge beim Modell: {k['eintraege_modell']}, beim Parser fehlend im Modell: "
              f"{k['eintraege_fehlend']}, nur beim Modell: {k['eintraege_nur_modell']}",
              f"- Daten nicht normalisierbar: {k['datum_nicht_normalisierbar']}\n",
              "| Status (Parser) | Feldtyp | verglichen | gleich | Übereinstimmung |", "|---|---|--:|--:|--:|"]
        for status, felder in sorted(k["uebereinstimmung"].items()):
            for typ, e in sorted(felder.items()):
                quote = e["gleich"] / e["verglichen"] * 100 if e["verglichen"] else 0.0
                z.append(f"| {status} | {typ} | {e['verglichen']} | {e['gleich']} | {quote:.1f} % |")
        z.append("")
    return "\n".join(z) + "\n"


QUELLE_LLM = "llm-lauf"


def _feldtyp(feld: str) -> str:
    return re.sub(r"^stadium_\d+_", "stadium_", feld)


def messe_goldstandard(stichprobe: list, modell) -> dict:
    """Jedes geprüfte Feld der Stichprobe (soll = korrektur bei korrekt=nein, sonst wert)
    gegen den Modellwert. Nachgetragene Zeilen (wert leer) zählen als 'fehlend' und gelten
    als gefunden, wenn das Modell den Sollwert liefert."""
    m_s, m_n = modell
    ausgefuellt = [z for z in stichprobe if (z.get("korrekt") or "").strip()]
    je_feldtyp = defaultdict(lambda: {"geprueft": 0, "korrekt": 0})
    je_status = defaultdict(lambda: {"geprueft": 0, "korrekt": 0})
    fehler, fehlend_gesamt, fehlend_gefunden = [], 0, 0
    for z in ausgefuellt:
        nein = z["korrekt"].strip().lower() == "nein"
        soll = z["korrektur"] if nein else z["wert"]
        ist = feldwert(m_s, m_n, z["schl_nr"], z["feld"])
        treffer = ist == soll
        if nein and not (z.get("wert") or "").strip():
            fehlend_gesamt += 1
            fehlend_gefunden += treffer
        for d in (je_feldtyp[_feldtyp(z["feld"])], je_status[z.get("status", "")]):
            d["geprueft"] += 1
            d["korrekt"] += treffer
        if not treffer:
            fehler.append({"schl_nr": z["schl_nr"], "lemma": z["lemma"], "status": z.get("status", ""),
                           "feld": z["feld"], "soll": soll, "ist": ist})

    def _q(d):
        return {**d, "fehlerquote": (d["geprueft"] - d["korrekt"]) / d["geprueft"] * 100 if d["geprueft"] else 0.0}

    gesamt = {"geprueft": len(ausgefuellt), "korrekt": len(ausgefuellt) - len(fehler)}
    return {"je_feldtyp": {k: _q(v) for k, v in sorted(je_feldtyp.items())},
            "je_status": {k: _q(v) for k, v in sorted(je_status.items())},
            "gesamt": _q(gesamt), "fehler": fehler,
            "fehlend_gesamt": fehlend_gesamt, "fehlend_gefunden": fehlend_gefunden}


def formatiere_ergebnis_llm_md(statistiken: dict) -> str:
    z = ["# Goldstandard-Messung der LLM-Leser\n",
         "Jedes geprüfte Feld der Goldstandard-Stichprobe (Seed 1936, menschlich geprüft) gegen den",
         "Wert des jeweiligen Modells. Der Prompt wurde an anderen Seiten entwickelt und nach dieser",
         "Messung nicht mehr verändert (Spec 2026-09-12, Abschnitt 4).\n"]
    for kurz, st in statistiken.items():
        g = st["gesamt"]
        z += [f"## Modell `{kurz}`\n",
              f"Gesamt: {g['geprueft']} Felder, {g['korrekt']} korrekt, Fehlerquote {g['fehlerquote']:.1f} %. "
              f"Vom Parser ausgelassene Felder: {st['fehlend_gefunden']} von {st['fehlend_gesamt']} vom Modell gefunden.\n",
              "| Schicht/Feldtyp | geprüft | korrekt | Fehlerquote |", "|---|--:|--:|--:|"]
        for k, v in list(st["je_status"].items()) + list(st["je_feldtyp"].items()):
            z.append(f"| {k} | {v['geprueft']} | {v['korrekt']} | {v['fehlerquote']:.1f} % |")
        if st["fehler"]:
            z += ["", "### Abweichungen\n", "| schl_nr | Lemma | Feld | soll | Modell |", "|---|---|---|---|---|"]
            for f in st["fehler"]:
                z.append(f"| {f['schl_nr']} | {f['lemma']} | {f['feld']} | {f['soll']} | {'—' if f['ist'] is None else f['ist']} |")
        z.append("")
    return "\n".join(z) + "\n"


def uebernehmen(pruefliste: list, korrekturen_vorhanden: list, datum: str) -> list:
    """Ausgefüllte korrektur-Spalten der Prüfliste -> neue Zeilen für daten/korrekturen.csv.
    'stadium_N' (ganzes Stadium) erwartet 'DATUM | NAME' und wird zu zwei Nachtragszeilen.
    'eintrag' ohne Parser-Wert ist eine Parser-Auslassung — nicht per Overlay behebbar."""
    vorhanden = {(k["schl_nr"], k["feld"], k["wert_neu"]) for k in korrekturen_vorhanden}
    neu = []

    def _zeile(schl, feld, alt, wert_neu, beleg):
        if (schl, feld, wert_neu) in vorhanden:
            return
        vorhanden.add((schl, feld, wert_neu))
        neu.append({"schl_nr": schl, "feld": feld, "wert_alt": alt, "wert_neu": wert_neu,
                    "beleg": beleg, "quelle": QUELLE_LLM, "datum": datum})

    for z in pruefliste:
        korr = (z.get("korrektur") or "").strip()
        if not korr:
            continue
        schl, feld, alt, beleg = z["schl_nr"], z["feld"], z.get("wert_parser", ""), z.get("beleg", "")
        if feld == "eintrag":
            if not alt:
                raise ValueError(f"{schl}: Eintrag fehlt beim Parser — Parser-Auslassung, nicht per Overlay behebbar")
            raise ValueError(f"{schl}: 'eintrag' korrigiert man über die einzelnen Felder")
        m = _STADIUMFELD.match(feld)
        if m and m.group(2) is None:
            if alt:
                raise ValueError(f"{schl} {feld}: Parser hat das Stadium — bei Bestätigung keine Korrektur eintragen")
            if "|" not in korr:
                raise ValueError(f"{schl} {feld}: erwartet 'DATUM | NAME'")
            d, n = (t.strip() for t in korr.split("|", 1))
            _zeile(schl, f"{feld}_datum", "", d, beleg)
            _zeile(schl, f"{feld}_name", "", n, beleg)
            continue
        _zeile(schl, feld, alt, korr, beleg)
    return neu


def _lade_parser(daten_dir=DATEN_DIR):
    with open(Path(daten_dir) / "strassen.csv", encoding="utf-8", newline="") as f:
        strassen = list(csv.DictReader(f))
    with open(Path(daten_dir) / "namen.csv", encoding="utf-8", newline="") as f:
        namen = list(csv.DictReader(f))
    return strassen, namen


def _modelle(antworten_dir) -> dict:
    modelle = {}
    for ordner in sorted(Path(antworten_dir).glob("*/")):
        modelle[kurzname(ordner.name)] = {"antworten": lade_antworten(antworten_dir, ordner.name)}
    return modelle


def _cli():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="befehl", required=True)
    p1 = sub.add_parser("pruefliste"); p1.add_argument("--antworten-dir", default=str(ANTWORTEN_DIR))
    p1.add_argument("--daten", default=str(DATEN_DIR)); p1.add_argument("--kennzahlen", default=str(KENNZAHLEN_PFAD))
    p2 = sub.add_parser("goldstandard"); p2.add_argument("--antworten-dir", default=str(ANTWORTEN_DIR))
    p2.add_argument("--ausgabe", default=str(WURZEL / "docs" / "goldstandard" / "ergebnis_llm.md"))
    p3 = sub.add_parser("uebernehmen"); p3.add_argument("--daten", default=str(DATEN_DIR))
    p3.add_argument("--datum", default=date.today().isoformat())
    a = p.parse_args()

    if a.befehl == "pruefliste":
        zeilen, kz = baue_pruefliste(_lade_parser(a.daten), _modelle(a.antworten_dir))
        schreibe_pruefliste(zeilen, Path(a.daten) / "pruefung_llm.csv")
        Path(a.kennzahlen).write_text(formatiere_kennzahlen_md(kz), encoding="utf-8")
        print(f"{len(zeilen)} Prüfzeilen; Kennzahlen -> {a.kennzahlen}")
    elif a.befehl == "goldstandard":
        from strassen.goldstandard import lade_stichprobe
        stichprobe = lade_stichprobe()
        statistiken = {}
        for kurz, m in _modelle(a.antworten_dir).items():
            s, n = [], []
            for antwort in m["antworten"].values():
                si, ni, _ = normalisiere_antwort(antwort); s += si; n += ni
            statistiken[kurz] = messe_goldstandard(stichprobe, als_struktur(s, n))
        Path(a.ausgabe).write_text(formatiere_ergebnis_llm_md(statistiken), encoding="utf-8")
        for kurz, st in statistiken.items():
            print(f"{kurz}: Fehlerquote {st['gesamt']['fehlerquote']:.1f} % ({st['gesamt']['geprueft']} Felder)")
    else:
        from strassen.korrekturen import KORREKTUREN_PFAD, lade_korrekturen
        with open(Path(a.daten) / "pruefung_llm.csv", encoding="utf-8", newline="") as f:
            pruefliste = list(csv.DictReader(f))
        vorhanden = lade_korrekturen(KORREKTUREN_PFAD)
        neu = uebernehmen(pruefliste, vorhanden, a.datum)
        with open(KORREKTUREN_PFAD, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FELDER_KORREKTUREN)
            if not vorhanden and f.tell() == 0:
                w.writeheader()
            w.writerows(neu)
        print(f"{len(neu)} Korrekturzeilen übernommen -> {KORREKTUREN_PFAD}")


if __name__ == "__main__":
    _cli()
