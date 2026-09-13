"""Fortlaufenden Text in einzelne Straßeneinträge schneiden.

Der Anker ist die Schlüsselnummer-Angabe. Sie wird tolerant erkannt, weil das OCR
sie in 122 von 3340 Fällen entstellt ('Sch!.-Nr.:', 'Scht.-Nr.:', 'Schi.-Nr.:').
Das Lemma steht unmittelbar davor, abgetrennt durch einen Doppelpunkt.

Statt der Lemma-Suche in einem festen Zeichenfenster vor jedem Anker (heuristisch,
kann bei langen Rümpfen daneben liegen) wird die Lemma-Position je Anker exakt im
Text zwischen dem Ende des vorigen Ankers und dem Beginn des aktuellen bestimmt.
Der Rumpf des Vorgängers endet dann exakt am Lemma-Beginn des Nachfolgers — es
gibt keine Lücke und keine Überlappung zwischen den Einträgen.

Ein Anker ohne davorstehendes Lemma-Muster wird nicht stillschweigend verworfen:
mit dem optionalen Parameter verworfene (eine übergebene Liste) wird er als
(buchseite, kontext_ausschnitt) angehängt, sichtbar für erschliessen.main.
"""
import re
from typing import NamedTuple

# Anker: kanonisch 'Schl.-Nr.:'. Toleriert: OCR-Buchstaben nach 'Sch' (auch '}' ')'),
# 'N.' statt 'Nr.', führender Bindestrich, ';' statt ':' (Spec 2026-09-13, R6). Komma
# statt Punkt ('Schl,-Nr.:', 11 Fälle im Material, z. B. Herkendell S. 156) fehlte in
# der ersten Fassung — der Eintrag wurde dadurch komplett verpasst und sein Text
# blutete in den rest des Vorgängers.
# Ein einzelner Großbuchstabe plus Leerraum vor 'Sch...' wird toleriert (S. 298,
# 02834 Schulte-Hinsel-Straße: 'Schulte-Hinsel-Straße:  S Schl.-Nr.:' — nach
# verbinde_zeilen ein verirrtes OCR-'S' zwischen Trenner und Anker; ohne diese
# Toleranz schlug die Lemma-Suche fehl und der Eintrag landete als "Anker ohne
# Lemma"). Der Bekannt-Vergleich unten erkennt das eingeschobene 'S' als Abweichung
# und meldet HINWEIS_ANKER_KORRIGIERT.
ANKER = re.compile(r"(?:[A-Z]\s+)?-?\s*Sch[a-zA-Z!|}\)]{0,3}[.,]?\s*-?\s*N(?:r)?\.?\s*[:;]")
# Bekannt-gute Formen: die ALTE Toleranz (OCR-Buchstaben nach 'Sch', optional
# Punkt/Komma/Bindestrich, optionaler Punkt nach 'Nr') aus der ersten Fassung dieses
# Moduls — 122 der 3340 Einträge im Material, unauffällig und schon vor R6 als
# 'automatisch' mit korrektem Kopf/Kette bestätigt. Hinweis nur für die am
# 2026-09-13 (R6) NEU ergänzten Toleranzen: '}'/')' nach 'Sch', 'N.' statt 'Nr.',
# führender Bindestrich, ';' statt ':', versprengter Großbuchstabe vor dem Anker.
# (Fix Runde 2: der erste Anlauf verglich gegen die einzige kanonische Form
# 'Schl.-Nr.:' und markierte dadurch auch die alten, längst bekannt-guten Varianten
# als Hinweis — 102 Einträge wurden dadurch ohne Präzisionsgewinn von 'automatisch'
# auf 'unsicher' verschoben, reiner Konkordanz-Verlust 426 → 406.) Whitespace ist
# vor dem Vergleich bereits entfernt, führender Bindestrich bzw. ein versprengter
# Großbuchstabe werden bewusst NICHT vorher abgeschnitten — sie sollen weiterhin als
# Abweichung erkannt werden.
_ANKER_BEKANNT = re.compile(r"^Sch[a-zA-Z!|]{0,3}[.,]?-?Nr\.?:$")
HINWEIS_ANKER_KORRIGIERT = "Anker OCR-korrigiert"
# Lemma: das Stichwort unmittelbar vor dem Anker, abgetrennt durch einen Doppelpunkt
# oder Semikolon (auch ':;', R6), der als letztes Nicht-Leerzeichen vor der
# Suchfenstergrenze steht. Komma, Semikolon und Doppelpunkt beenden die
# Rückwärtssuche innerhalb des Lemmas immer. Ein Punkt tut das nur, wenn er NICHT
# Teil einer Abkürzung ist (Bindestrich oder Buchstabe folgt direkt, z. B.
# 'St.-Ingbert-Höhe') — sonst schnitt die alte, jeden Punkt ausschließende Fassung
# Lemmata mit Abkürzungspunkt auf den Teil nach dem Punkt zusammen (>=21 betroffene
# Zeilen im Material, z. B. '-Ingbert-Höhe' statt 'St.-Ingbert-Höhe'). Ein echter
# Satzende-Punkt (gefolgt von Leerzeichen, nicht Bindestrich/Buchstabe) bricht wie
# bisher ab — ohne den Ausschluss würde die Lemma-Suche über das Komma bzw. den
# Satzpunkt hinweg rückwärts weiterlaufen und Reste des vorigen Rumpfs ins Lemma
# ziehen. Ein Punkt nach 'St', 'I', 'II', 'III', 'IV' oder 'Ill' ('St. Annental',
# 'I. Buschlandweg') ist ebenfalls Abkürzungs-/Ordnungspunkt und beendet die
# Rückwärtssuche nicht (Goldstandard 02727; R4, Prüfliste S. 86). 'Ill' ist die
# OCR-Lesart von 'III' (S. 283 Ill. Ruschenfeld, S. 315 Ill. Stiege, S. 321 Ill.
# Terwestenweg, Fix Runde 1) — absichtlich NICHT über datum._KEIN_ABKUERZUNGSPUNKT
# importiert, weil dessen (?<!\d)-Ausschluss einen echten Satzende-Punkt nach einer
# Jahreszahl ('…gegründet 1913. Lemma') fälschlich am Abbrechen hindern würde; die
# beiden Module lösen unterschiedliche Probleme und teilen sich die Regel bewusst
# nicht. Die Trenner-Gruppe (?::;?|;) zählt genau die drei in der Spec
# vorgesehenen Trenner auf — ':', ';' und ':;' — und ist damit enger als ein
# offenes [:;]+, das auch Ketten wie '::;;' oder ';;;' schlucken würde
# (precision-first: nur belegte Formen tolerieren, nichts darüber hinaus).
_LEMMA = re.compile(
    r"((?:(?!,|;|:|(?<!\bSt)(?<!\bI)(?<!\bII)(?<!\bIII)(?<!\bIV)(?<!\bIll)\.(?!-|[A-Za-zÄÖÜäöüß]))[^\n]){2,60}?)"
    r"\s*(?::;?|;)\s*$"
)


class Eintrag(NamedTuple):
    lemma_roh: str
    rumpf: str
    buchseite: int
    hinweise: tuple = ()


def segmentiere(seiten, verworfene=None) -> list:
    # Seiten aneinanderhängen und merken, wo jede beginnt, um den Beleg zu bestimmen.
    text_teile, grenzen, position = [], [], 0
    for nummer, text in seiten:
        grenzen.append((position, nummer))
        text_teile.append(text)
        position += len(text) + 1
    volltext = " ".join(text_teile)

    def buchseite_von(offset: int) -> int:
        seite = grenzen[0][1]
        for start, nummer in grenzen:
            if start <= offset:
                seite = nummer
            else:
                break
        return seite

    # Je Anker das unmittelbar davorstehende Lemma suchen. Das Suchfenster reicht
    # vom Ende des vorigen Ankers (bzw. Textanfang) bis zum Beginn des aktuellen —
    # so wird nie über einen anderen Anker hinweg gesucht, aber auch keine
    # willkürliche Zeichengrenze gezogen.
    treffer = list(ANKER.finditer(volltext))
    kandidaten = []  # (lemma, lemma_start, anker_ende, hinweise)
    fenster_start = 0
    for m in treffer:
        vorlauf = volltext[fenster_start:m.start()]
        lemma_treffer = _LEMMA.search(vorlauf)
        if lemma_treffer:
            roh = lemma_treffer.group(1)
            lemma = roh.strip()
            # Führende Leerzeichen der Gruppe gehören noch zur vorigen Seite, wenn
            # der Seitenumbruch genau dorthin fällt (Fuge zwischen den mit " "
            # verbundenen Seiten). Für den Seitenbeleg zählt der erste tatsächliche
            # Lemma-Buchstabe, nicht das Leerzeichen davor.
            versatz = len(roh) - len(roh.lstrip())
            lemma_start = fenster_start + lemma_treffer.start(1) + versatz
            # Anker-Text ohne Whitespace gegen die bekannt-guten (alten) Formen
            # geprüft — nur die am 2026-09-13 (R6) neu ergänzten Toleranzen
            # (verunstaltete Klammer-Buchstaben, 'N.' statt 'Nr.', führender
            # Bindestrich, ';' statt ':', versprengter Großbuchstabe) lösen den
            # Hinweis aus, die alte, längst bekannte Toleranz nicht (Fix Runde 2,
            # s. Kommentar bei _ANKER_BEKANNT).
            anker_text = re.sub(r"\s+", "", volltext[m.start():m.end()])
            hinweise = () if _ANKER_BEKANNT.match(anker_text) else (HINWEIS_ANKER_KORRIGIERT,)
            kandidaten.append((lemma, lemma_start, m.end(), hinweise))
        elif verworfene is not None:
            # Kein auffindbares Lemma vor diesem Anker: der Eintrag geht sonst
            # stillschweigend verloren. Statt ihn zu verwerfen, wird er sichtbar
            # gemacht — precision-first, siehe erschliessen.main (grund="Anker
            # ohne Lemma"). Der Kontext-Ausschnitt dient der manuellen Prüfung.
            kontext = (vorlauf[-80:] + volltext[m.start():m.end()]).strip()
            verworfene.append((buchseite_von(m.start()), kontext))
        fenster_start = m.end()

    eintraege = []
    for i, (lemma, lemma_start, anker_ende, hinweise) in enumerate(kandidaten):
        ende = kandidaten[i + 1][1] if i + 1 < len(kandidaten) else len(volltext)
        rumpf = volltext[anker_ende:ende].strip()
        eintraege.append(Eintrag(lemma_roh=lemma, rumpf=rumpf,
                                  buchseite=buchseite_von(lemma_start),
                                  hinweise=hinweise))
    return eintraege
