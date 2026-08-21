"""Gesamtlauf: OCR-Seiten → strassen.csv, namen.csv, pruefung.csv.

pruefung.csv ist das Sichtbarkeits-Netz (precision-first): lieber ein Eintrag
zu viel darin als einer, der stillschweigend verloren geht oder unmarkiert
veröffentlicht wird. Ein Eintrag mit mindestens einem Grund bekommt
status="unsicher" statt "automatisch" — Kennzeichnung, kein Ausschluss: er
bleibt in strassen.csv/namen.csv erhalten. Gründe:
  - "Anker ohne Lemma": die Segmentierung fand eine Schlüsselnummer-Angabe,
    aber kein davorstehendes Lemma (segmentierung.segmentiere(verworfene=...)).
  - "keine Schlüsselnummer lesbar": parse_kopf() fand keinen Kopf im Rumpf
    (der Eintrag entfällt komplett, kein schl_nr zum Verknüpfen vorhanden).
  - "Lemma auffällig (Länge)": das Lemma ist ungewöhnlich lang (>4 Wörter oder
    >40 Zeichen).
  - "Lemma auffällig (Form)": das Lemma beginnt nicht mit Großbuchstabe/Umlaut
    oder enthält Zeichen, die in einem Straßennamen nicht vorkommen —
    typisches Symptom einer bei der Segmentierung abgeschnittenen oder
    verunreinigten Lemma-Erkennung.
  - "kein Namensstadium erkannt": der Kopf ist lesbar, aber weder ein
    Namensstadium noch ein Verweis ("Siehe ...") im Kopfbereich (die ersten
    _VERWEIS_KOPF_FENSTER Zeichen des Rumpfs) ließ sich finden. Ein "Siehe"
    tief in einer inhaltlich unabhängigen Erläuterung zählt dabei NICHT als
    Ersatz für ein fehlendes Stadium — sonst verschwinden Einträge mit
    verstümmeltem Datum still, nur weil zufällig weiter hinten ein "Siehe"
    auf eine andere Straße verweist (s. _VERWEIS_KOPF_FENSTER unten).
  - "Namensstadium auffällig": mindestens ein erkanntes Namensstadium ist zu
    kurz/lang oder enthält Nicht-Namenszeichen bzw. eine lange Ziffernfolge
    (OCR-Bildrauschen, das als Stadium fehlinterpretiert wurde).
  - "Feld auffällig (Länge)": strassenklasse ist ungewöhnlich lang
    (>60 Zeichen) ODER namensgruppe ist auffällig (>150 Zeichen, enthält
    Rauschzeichen oder einen Ziffern-Cluster ≥3 Stellen) — typisches
    Symptom eines nicht erkannten Feldmarkers, dessen Wert dadurch
    Folgetext verschluckt. Die Schwellen unterscheiden sich zwischen den
    beiden Feldern, weil namensgruppe im Material legitim lange,
    mehrteilige Kategorien-Listen enthält (z. B. 'Person, Mann, Deutscher,
    Philosoph, ...'), während strassenklasse solche langen, aber sauberen
    Werte nicht kennt (Fix-Runde 1, Teil 2 — Ruling 3, s. task-5-report.md).
  - "Schlüsselnummer mehrfach": dieselbe schl_nr kommt bei mehreren Einträgen
    vor — welcher davon die "echte" Nummer trägt, wird nicht geraten,
    sondern beide werden zur manuellen Prüfung markiert.
"""
import re
import sys
from collections import Counter
from pathlib import Path

from strassen.aufbereitung import aufbereiten
from strassen.segmentierung import segmentiere
from strassen.kopf import parse_kopf
from strassen.namen import parse_namenskette
from strassen.ausgabe import schreibe_strassen, schreibe_namen, schreibe_pruefung

_VERWEIS = re.compile(r"Siehe\s+([A-ZÄÖÜ][^.,;]{2,60})")
# Fenster (Zeichen ab Rumpfanfang), in dem ein 'Siehe X' als Ersatz für ein
# fehlendes Namensstadium gilt (reiner Verweis-Eintrag ohne eigene Namenskette,
# z. B. 'Schl.-Nr.: ..., Str.-Gr.: ..., 01. Januar 1900, Kurzverweis. Siehe
# Zielstraße.' — das Datum ist hier OCR-verstümmelt, aber 'Siehe' folgt direkt
# im Kopfbereich). Ein 'Siehe' TIEF in einer Erläuterung (z. B. ein beiläufiger
# Verweis auf eine andere, thematisch verwandte Straße nach einer langen,
# inhaltlich unabhängigen Worterklärung) ist dagegen KEIN Ersatz dafür — sonst
# verschwinden Einträge mit ebenfalls verstümmeltem Datum still aus pruefung.csv,
# nur weil zufällig irgendwo weiter hinten ein 'Siehe' auf eine andere Straße
# steht (reale stille Verluste: 00685, 00864, 02845). Empirisch trennt 120
# Zeichen die echten Kurz-Verweise (Position 102/107) sauber von diesen Fällen
# (Position 127/198/253). Betrifft NUR diese Prüfung — verweis_auf selbst wird
# weiterhin über den ganzen Rumpf gesucht (223 belegte Fälle, auch mit langer
# Erläuterung vor einem berechtigten 'Siehe').
_VERWEIS_KOPF_FENSTER = 120

# Auffälliges Lemma (Länge): die weit überwiegende Mehrheit echter
# Straßennamen ist kurz. Alles darüber wird nicht verworfen, sondern nur zur
# manuellen Prüfung markiert — precision-first heißt hier: sichtbar machen
# statt schweigend zu vertrauen.
_LEMMA_MAX_WOERTER = 4
_LEMMA_MAX_ZEICHEN = 40

# Erlaubte Zeichen in Lemma und Namensstadium, zusätzlich zu Buchstaben und
# Ziffern (beide über str.isalnum(), unicode-fähig, deckt auch Ä/Ö/Ü/ß ab):
# Leerzeichen sowie die im Material vorkommende Namens-Interpunktion. Alles
# andere (§, %, *, {, }, ¤, …) ist ein starkes Indiz für OCR-Bildrauschen
# statt eines echten Namens.
_ERLAUBTE_SONDERZEICHEN = set(" .-()'’/&„\"")
# Eine Ziffernfolge ab 5 Stellen kommt in einem Straßennamen nicht vor
# (Hausnummern/Jahreszahlen sind kürzer) — zusätzliches Indiz für Rauschen,
# das die reine Zeichen-Erlaubnisliste allein nicht abdeckt (Ziffern selbst
# sind grundsätzlich erlaubt, z. B. '(tlw. 2. Hälfte)').
_ZIFFERNFOLGE_LANG = re.compile(r"\d{5,}")

_NAME_MIN_ZEICHEN = 3
_NAME_MAX_ZEICHEN = 60
_FELD_MAX_ZEICHEN = 60

# namensgruppe-Heuristik (Ruling 3): eigene, großzügigere Erlaubnisliste, da
# namensgruppe im Material legitim kommagetrennte Kategorien führt (anders
# als Lemma/Namensstadium, wo ein Komma nie zum Namen gehört) — Komma ist
# hier deshalb zusätzlich erlaubt. Ein Ziffern-Cluster ab 3 Stellen
# (Jahreszahl) ist dagegen ein Fehlerindiz: der Altendorfer-Bleed-Fall
# ('etwa 1921: Nelkenstraße' in strassenklasse) zeigt, dass eine Jahreszahl
# in diesen Feldern nie legitim vorkommt, sondern immer aus einer
# verrutschten Namenskette stammt.
_ERLAUBTE_SONDERZEICHEN_GRUPPE = set(" ,.-()'’/&„\"")
_ZIFFERNFOLGE_GRUPPE = re.compile(r"\d{3,}")
_NAMENSGRUPPE_MAX_ZEICHEN = 150


def _lemma_auffaellig(lemma: str) -> bool:
    return len(lemma) > _LEMMA_MAX_ZEICHEN or len(lemma.split()) > _LEMMA_MAX_WOERTER


def _hat_nur_namenszeichen(text: str) -> bool:
    return all(ch.isalnum() or ch in _ERLAUBTE_SONDERZEICHEN for ch in text)


def _lemma_form_auffaellig(lemma: str) -> bool:
    if not lemma or not lemma[0].isupper():
        return True
    return not _hat_nur_namenszeichen(lemma)


def _name_auffaellig(name: str) -> bool:
    if not (_NAME_MIN_ZEICHEN <= len(name) <= _NAME_MAX_ZEICHEN):
        return True
    if not _hat_nur_namenszeichen(name):
        return True
    return bool(_ZIFFERNFOLGE_LANG.search(name))


def _feld_zu_lang(text: str) -> bool:
    return len(text) > _FELD_MAX_ZEICHEN


def _namensgruppe_auffaellig(text: str) -> bool:
    if len(text) > _NAMENSGRUPPE_MAX_ZEICHEN:
        return True
    if not all(ch.isalnum() or ch in _ERLAUBTE_SONDERZEICHEN_GRUPPE for ch in text):
        return True
    return bool(_ZIFFERNFOLGE_GRUPPE.search(text))


def main(ocr_dir="ocr/seiten", ausgabe_dir="daten"):
    ziel = Path(ausgabe_dir)
    ziel.mkdir(parents=True, exist_ok=True)

    verworfene = []
    eintraege = segmentiere(aufbereiten(ocr_dir), verworfene=verworfene)

    strassen, namen, pruefung = [], [], []

    for buchseite, kontext in verworfene:
        pruefung.append({"buchseite": buchseite, "lemma_roh": "",
                         "grund": "Anker ohne Lemma", "rohtext": kontext[:200]})

    for e in eintraege:
        k = parse_kopf(e.rumpf)
        if k is None:
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": "keine Schlüsselnummer lesbar",
                             "rohtext": e.rumpf[:200]})
            continue

        mv = _VERWEIS.search(e.rumpf)
        mv_kopf = _VERWEIS.search(e.rumpf[:_VERWEIS_KOPF_FENSTER])
        stadien = parse_namenskette(k.rest)
        stadtteile_str = "; ".join(k.stadtteile)
        klasse_str = "; ".join(k.strassenklassen)

        # Jeder zutreffende Grund wird einzeln in pruefung.csv sichtbar — ein
        # Eintrag kann mehrere Gründe gleichzeitig haben (z. B. auffälliges
        # Lemma UND auffälliges Namensstadium).
        gruende = []
        if _lemma_auffaellig(e.lemma_roh):
            gruende.append("Lemma auffällig (Länge)")
        if _lemma_form_auffaellig(e.lemma_roh):
            gruende.append("Lemma auffällig (Form)")
        if not stadien and not mv_kopf:
            gruende.append("kein Namensstadium erkannt")
        rauschnamen = [s.name for s in stadien if _name_auffaellig(s.name)]
        if rauschnamen:
            gruende.append("Namensstadium auffällig")
        if _feld_zu_lang(klasse_str) or _namensgruppe_auffaellig(k.namensgruppe):
            gruende.append("Feld auffällig (Länge)")

        for grund in gruende:
            rohtext = ("; ".join(rauschnamen)[:200] if grund == "Namensstadium auffällig"
                       else e.rumpf[:200])
            pruefung.append({"buchseite": e.buchseite, "lemma_roh": e.lemma_roh,
                             "grund": grund, "rohtext": rohtext})

        strassen.append({
            "schl_nr": k.schl_nr, "lemma": e.lemma_roh,
            "stadtteile": stadtteile_str,
            "strassenklasse": klasse_str,
            "namensgruppe": k.namensgruppe,
            "verweis_auf": mv.group(1).strip() if mv else "",
            "buchseite": e.buchseite,
            "status": "unsicher" if gruende else "automatisch"})
        for s in stadien:
            namen.append({"schl_nr": k.schl_nr, "stadium": s.stadium,
                          "gueltig_ab": s.gueltig_ab,
                          "datum_praezision": s.datum_praezision, "name": s.name,
                          "ist_urspruenglich": "wahr" if s.ist_urspruenglich else "falsch"})

    # Schlüsselnummer-Dubletten: erst jetzt erkennbar, wenn alle Einträge
    # gesammelt sind. Beide (bzw. alle) Einträge mit derselben schl_nr werden
    # markiert — welcher davon die echte Nummer trägt, wird nicht geraten.
    zaehler = Counter(z["schl_nr"] for z in strassen)
    for z in strassen:
        if zaehler[z["schl_nr"]] > 1:
            z["status"] = "unsicher"
            pruefung.append({"buchseite": z["buchseite"], "lemma_roh": z["lemma"],
                             "grund": "Schlüsselnummer mehrfach", "rohtext": ""})

    schreibe_strassen(strassen, ziel / "strassen.csv")
    schreibe_namen(namen, ziel / "namen.csv")
    schreibe_pruefung(pruefung, ziel / "pruefung.csv")
    kennzahlen = {"eintraege": len(eintraege), "strassen": len(strassen),
                  "namensstadien": len(namen), "pruefung": len(pruefung)}
    print(kennzahlen)
    return kennzahlen


if __name__ == "__main__":
    kennzahlen = main()
    # Exitcode 1, wenn kein einziger Straßeneintrag erzeugt wurde (leeres oder
    # falsch adressiertes ocr_dir, kaputte Segmentierung) — ein stiller
    # Erfolg (Exit 0) bei null Ergebniszeilen wäre irreführend.
    sys.exit(0 if kennzahlen["strassen"] else 1)
