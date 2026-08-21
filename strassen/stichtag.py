"""Namensstand zu einem Stichtag bestimmen und die Konkordanz ableiten.

Stadien ohne verwertbares Datum werden übersprungen, nicht geschätzt; wo dadurch
kein Stadium bestimmbar ist, entsteht kein Konkordanzeintrag.
"""
import re
from collections import defaultdict


def _vergleichbar(stadium) -> str:
    """Datum in vergleichbarer Form; leer, wenn nicht verwertbar.

    'jahr'-Präzision UND 'vor'-Präzision (gueltig_ab trägt hier nur ein Jahr, bei
    'vor' zusätzlich mit der Bedeutung 'irgendwann vor diesem Jahr') werden hier
    gleich behandelt: beide liefern nur einen 4-stelligen Jahreswert, der
    konservativ auf Jahresende gelegt wird. Für 'vor' ist das unproblematisch, weil
    das tatsächliche Datum nur noch früher liegen kann als der Jahreswert — die
    Reihenfolge zu allen späteren, tatsächlich datierten Stadien bleibt also
    korrekt, und für Stichtags-Vergleiche weit in der Vergangenheit (wie hier) wirkt
    sich die Ungenauigkeit nicht aus."""
    wert = (stadium.get("gueltig_ab") or "").strip()
    if not wert:
        return ""
    if len(wert) == 4:            # nur Jahr: konservativ auf Jahresende legen
        return f"{wert}-12-31"
    return wert


# Klammerzusatz am Namensende (Dickhoffs Vermerke wie "(Verl.)", "(Umb.)", "(tlw.)"),
# auch OCR-Varianten mit vertauschtem Klammertyp ("{tlw.)") oder verstümmeltem Inhalt
# ("(t!w.)"): öffnende Klammer beliebig ( oder {, schließende beliebig ) oder }.
_ZUSATZ_MUSTER = re.compile(r"\s*[\(\{][^)}]*[\)\}]\s*$")


def _trenne_zusatz(name: str):
    """Trennt einen Klammerzusatz vom Namensende ab, damit der reine Straßenname für
    den Adressbuch-Abgleich und den Kollisions-Check nutzbar wird. Gibt
    (name_ohne_zusatz, zusatz) zurück; zusatz ist '', wenn keiner vorhanden ist."""
    m = _ZUSATZ_MUSTER.search(name)
    if not m:
        return name.strip(), ""
    return name[:m.start()].strip(), m.group().strip()


def _norm_vergleich(name: str) -> str:
    """Normalisiert für den mechanischen Konsistenz-Check zwischen dem chronologisch
    letzten Stadium und dem aktuellen Lemma: kleinschreiben, Whitespace
    vereinheitlichen, ß/ss angleichen, 'str.'/'straße' vereinheitlichen."""
    s = (name or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("ß", "ss")
    s = re.sub(r"str\.?$", "strasse", s)
    return s


def _letztes_datiertes_stadium(stadien):
    """Das chronologisch letzte Stadium mit verwertbarem Datum, oder None, wenn kein
    Stadium ein Datum trägt."""
    datiert = [(s, _vergleichbar(s)) for s in stadien]
    datiert = [(s, d) for s, d in datiert if d]
    if not datiert:
        return None
    return max(datiert, key=lambda sd: sd[1])[0]


def _norm_strasse(s: str) -> str:
    """Normalisiert einen Straßennamen für den Adressbuch-Abgleich: kleinschreiben
    und 'str.'/'straße' vereinheitlichen (Adressbuch-Einträge sind oft abgekürzt)."""
    s = (s or "").strip().lower()
    s = re.sub(r"str\.?$", "straße", s)
    return s


def name_am_stichtag(stadien, stichtag: str):
    gueltig = None
    for s in sorted(stadien, key=lambda x: _vergleichbar(x) or "9999"):
        d = _vergleichbar(s)
        if not d:
            continue
        if d <= stichtag:
            gueltig = s
    return gueltig


def messe_erhebungsstand(stadien_je_strasse, adressbuch_namen) -> dict:
    """Zählt je Jahr, ob das Adressbuch die alte oder die neue Namensform nutzt."""
    adressbuch_norm = {_norm_strasse(n) for n in adressbuch_namen}
    befund = defaultdict(lambda: {"alt": 0, "neu": 0})
    for stadien in stadien_je_strasse.values():
        geordnet = sorted(stadien, key=lambda x: _vergleichbar(x) or "9999")
        for i in range(1, len(geordnet)):
            d = _vergleichbar(geordnet[i])
            if not d:
                continue
            jahr = int(d[:4])
            alt = _norm_strasse(geordnet[i - 1]["name"])
            neu = _norm_strasse(geordnet[i]["name"])
            if alt in adressbuch_norm and neu not in adressbuch_norm:
                befund[jahr]["alt"] += 1
            elif neu in adressbuch_norm and alt not in adressbuch_norm:
                befund[jahr]["neu"] += 1
    return dict(sorted(befund.items()))


def messe_erhebungsstand_monatlich(stadien_je_strasse, adressbuch_namen,
                                    von: str, bis: str) -> dict:
    """Wie messe_erhebungsstand, aber monatsscharf (Schlüssel 'JJJJ-MM'), begrenzt
    auf den Bereich [von, bis] (je 'JJJJ-MM'). Nutzt NUR Stadien mit Tagespräzision:
    Jahrespräzision liefert keinen echten Monat — der würde sonst geraten (auf
    Dezember gelegt) statt aus den Daten zu stammen, was gegen precision-first
    verstieße. In den hier ausgewerteten Jahren (1935-1937) sind ohnehin alle
    tatsächlichen Umbenennungs-Übergänge tagesgenau datiert."""
    adressbuch_norm = {_norm_strasse(n) for n in adressbuch_namen}
    befund = defaultdict(lambda: {"alt": 0, "neu": 0})
    for stadien in stadien_je_strasse.values():
        geordnet = sorted(stadien, key=lambda x: _vergleichbar(x) or "9999")
        for i in range(1, len(geordnet)):
            d = _vergleichbar(geordnet[i])
            praezision = geordnet[i].get("datum_praezision", "")
            if not d or praezision != "tag":
                continue
            monat = d[:7]
            if not (von <= monat <= bis):
                continue
            alt = _norm_strasse(geordnet[i - 1]["name"])
            neu = _norm_strasse(geordnet[i]["name"])
            if alt in adressbuch_norm and neu not in adressbuch_norm:
                befund[monat]["alt"] += 1
            elif neu in adressbuch_norm and alt not in adressbuch_norm:
                befund[monat]["neu"] += 1
    return dict(sorted(befund.items()))


_GRUND_KETTE_UNVOLLSTAENDIG = "Namenskette unvollständig (letztes Stadium ≠ Lemma)"


def _kandidat_oder_pruefung(strasse, stadien, stichtag: str):
    """Kernlogik für einen einzelnen Straßendatensatz: liefert ('kandidat', dict)
    für einen möglichen Konkordanzeintrag, ('pruefen', dict) für einen Fall, den das
    mechanische Konsistenz-Netz (Fix-Runde 1, Ruling C) zurückweist, oder None, wenn
    am Stichtag ohnehin kein Namenswandel vorliegt bzw. keine Daten verfügbar sind.

    Das Konsistenz-Netz vergleicht das chronologisch LETZTE datierte Stadium einer
    Straße (zusatzbereinigt) mit dem heutigen Lemma. Stimmen sie nicht überein, ist
    entweder die Namenskette unvollständig (ein Stadium fehlt) oder ein Wert ist
    korrupt (OCR/Erschließung) — in beiden Fällen wäre der abgeleitete historische
    Name nicht vertrauenswürdig, also kein Konkordanzeintrag, sondern ein Prüffall.
    Das ist unabhängig vom Stichtag selbst; es hängt hier trotzdem am Stichtag, weil
    nur die Straßen relevant sind, die am Stichtag überhaupt einen (potenziellen)
    Konkordanzeintrag erzeugen würden."""
    treffer = name_am_stichtag(stadien, stichtag)
    if not treffer:
        return None

    # Zusatz-Abtrennung (Ruling A) VOR dem 'unverändert'-Check: manche Stadien
    # unterscheiden sich vom Lemma nur durch einen Klammerzusatz wie '(Verl.)' —
    # nach dessen Abtrennung ist der Name in Wahrheit unverändert und braucht
    # keinen Konkordanzeintrag (sonst entstünden sinnentleerte Zeilen mit
    # ehemalig == heutig, die keine echte Umbenennung mehr abbilden).
    ehemalig, zusatz_ehemalig = _trenne_zusatz(treffer["name"].strip())
    heutig, zusatz_heutig = _trenne_zusatz(strasse["lemma"].strip())
    if ehemalig == heutig:
        return None                       # Name unverändert — kein Konkordanzeintrag

    letztes = _letztes_datiertes_stadium(stadien)
    letztes_roh = letztes["name"].strip() if letztes else ""
    letztes_bereinigt = _trenne_zusatz(letztes_roh)[0] if letztes else ""
    if letztes is None or _norm_vergleich(letztes_bereinigt) != _norm_vergleich(strasse["lemma"]):
        befund = (f"letztes Stadium '{letztes_roh}'" if letztes else "kein datiertes Stadium")
        befund += f" ≠ Lemma '{strasse['lemma'].strip()}' (schl_nr {strasse['schl_nr']})"
        return ("pruefen", {
            "buchseite": strasse.get("buchseite", ""),
            "lemma": strasse["lemma"].strip(),
            "grund": _GRUND_KETTE_UNVOLLSTAENDIG,
            "befund": befund,
        })

    zusatz = zusatz_ehemalig
    if zusatz_heutig:
        zusatz = f"{zusatz} / heutig:{zusatz_heutig}" if zusatz else f"heutig:{zusatz_heutig}"
    return ("kandidat", {
        "stadtteil": strasse.get("stadtteile", "").split(";")[0].strip(),
        "ehemalig": ehemalig,
        "heutig": heutig,
        "schl_nr": strasse["schl_nr"],
        "datum_praezision": treffer.get("datum_praezision", ""),
        "quelle": "Dickhoff 2015",
        "zusatz": zusatz,
    })


def baue_konkordanz(strassen, namen, stichtag: str) -> list:
    je_nr = defaultdict(list)
    for z in namen:
        je_nr[z["schl_nr"]].append(z)

    kandidaten = []
    for s in strassen:
        ergebnis = _kandidat_oder_pruefung(s, je_nr.get(s["schl_nr"], []), stichtag)
        if ergebnis and ergebnis[0] == "kandidat":
            kandidaten.append(ergebnis[1])

    # Kollisionen markieren: mehrere Straßen, gleicher Stadtteil, gleicher
    # (zusatzbereinigter) historischer Name — der Adressbuch-Abgleich kann sie nicht
    # unterscheiden, ein Consumer darf sie nicht still ineinander überschreiben.
    gruppen = defaultdict(list)
    for k in kandidaten:
        gruppen[(k["stadtteil"], k["ehemalig"])].append(k)
    for gruppe in gruppen.values():
        eindeutig = "ja" if len(gruppe) == 1 else "nein"
        for k in gruppe:
            k["eindeutig"] = eindeutig

    return kandidaten


def pruefe_konkordanz(strassen, namen, stichtag: str) -> list:
    """Prüffälle, die baue_konkordanz wegen des mechanischen Konsistenz-Netzes NICHT
    in die Konkordanz aufnimmt (letztes datiertes Stadium ≠ aktuelles Lemma).
    Dieselbe Kandidaten-Logik wie baue_konkordanz, nur die andere Ausgabe-Hälfte —
    damit beide Funktionen exakt komplementär sind."""
    je_nr = defaultdict(list)
    for z in namen:
        je_nr[z["schl_nr"]].append(z)

    prueffaelle = []
    for s in strassen:
        ergebnis = _kandidat_oder_pruefung(s, je_nr.get(s["schl_nr"], []), stichtag)
        if ergebnis and ergebnis[0] == "pruefen":
            prueffaelle.append(ergebnis[1])
    return prueffaelle
