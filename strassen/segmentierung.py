"""Fortlaufenden Text in einzelne Straßeneinträge schneiden.

Der Anker ist die Schlüsselnummer-Angabe. Sie wird tolerant erkannt, weil das OCR
sie in 122 von 3340 Fällen entstellt ('Sch!.-Nr.:', 'Scht.-Nr.:', 'Schi.-Nr.:').
Das Lemma steht unmittelbar davor, abgetrennt durch einen Doppelpunkt.

Statt der Lemma-Suche in einem festen Zeichenfenster vor jedem Anker (heuristisch,
kann bei langen Rümpfen daneben liegen) wird die Lemma-Position je Anker exakt im
Text zwischen dem Ende des vorigen Ankers und dem Beginn des aktuellen bestimmt.
Der Rumpf des Vorgängers endet dann exakt am Lemma-Beginn des Nachfolgers — es
gibt keine Lücke und keine Überlappung zwischen den Einträgen.
"""
import re
from typing import NamedTuple

# Sch + bis zu drei fehlgelesene Zeichen + optionaler Punkt/Bindestrich + Nr + Doppelpunkt
ANKER = re.compile(r"Sch[a-zA-Z!|]{0,3}\.?\s*-?\s*Nr\.?\s*:")
# Lemma: das Stichwort unmittelbar vor dem Anker, abgetrennt durch einen Doppelpunkt,
# der als letztes Nicht-Leerzeichen vor der Suchfenstergrenze steht. Das Komma ist
# ausgeschlossen, weil Seiten mit einem Komma enden können (Fortsetzung auf der
# Folgeseite, z. B. "...Siehe Kruppallee," am Ende von Seite 210) — ohne den
# Ausschluss würde die Lemma-Suche über das Komma hinweg rückwärts weiterlaufen
# und Reste des vorigen Rumpfs ins Lemma ziehen.
_LEMMA = re.compile(r"([^.,;:]{2,60}?)\s*:\s*$")


class Eintrag(NamedTuple):
    lemma_roh: str
    rumpf: str
    buchseite: int


def segmentiere(seiten) -> list:
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
    kandidaten = []  # (lemma, lemma_start, anker_ende)
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
            kandidaten.append((lemma, lemma_start, m.end()))
        fenster_start = m.end()

    eintraege = []
    for i, (lemma, lemma_start, anker_ende) in enumerate(kandidaten):
        ende = kandidaten[i + 1][1] if i + 1 < len(kandidaten) else len(volltext)
        rumpf = volltext[anker_ende:ende].strip()
        eintraege.append(Eintrag(lemma_roh=lemma, rumpf=rumpf,
                                  buchseite=buchseite_von(lemma_start)))
    return eintraege
