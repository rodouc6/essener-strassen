# Unabhängige LLM-Lesung und Korrektur-Overlay — Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zwei bildfähige Open-Weight-Modelle lesen alle 388 Buchseiten unabhängig vom Parser; die Abweichungen werden als Prüfliste ausgegeben, menschlich bestätigte Korrekturen fließen über ein versioniertes Overlay (`daten/korrekturen.csv`, Status `geprueft`) in den Datensatz.

**Architecture:** Vier neue Module in `strassen/`: `seiten.py` (Buchseiten als PNG), `llm_leser.py` (OpenAI-kompatible Anfrage je Seite, Rohantworten gecacht), `llm_vergleich.py` (Antworten in Datensatzform, Vergleich über `differenz.vergleiche`, Prüfliste, Goldstandard-Messung), `korrekturen.py` (Overlay, angewandt in `erschliessen.main`). Kleine Erweiterungen in `goldstandard.py` (dpi-Parameter), `differenz.py` (Struktur-Eingang), `datum.py` (`lese_text`), `veroeffentlichen.py` (`geprueft` gleichrangig mit `automatisch`).

**Tech Stack:** Python ≥ 3.12, Standardbibliothek (`urllib`, `json`, `csv`, `re`, `base64`); numpy/Pillow/pdftoppm nur fürs Rendering (wie bisher). Tests mit pytest (Funktionsstil wie in `tests/`), kein Netzzugriff.

**Spec:** `docs/specs/2026-09-12-llm-lesung-design.md`

**Abweichungen von der Spec (im Plan festgelegt):**
1. Kennzahlen des Laufs schreibt `llm_vergleich` nach `docs/llm_lesung.md` (eigene Datei) statt als Abschnitt in `docs/qualitaet.md`, das `validierung.schreibe_bericht` vollständig erzeugt. README verlinkt beide.
2. Die Normalisierung eines gedruckten Datumstexts wird als `datum.lese_text(text)` ergänzt, damit Vergleich und Overlay dieselbe Funktion nutzen.
3. `pruefung.csv` (Parser-Protokoll) bleibt von Korrekturen unberührt; „Prüfgründe verfallen" heißt: der Eintrag trägt `status=geprueft`, der Status ist die einzige Stelle, an der Gründe im Datensatz wirken.
4. Parser-Auslassungen (Eintrag nur beim Modell) kann das Overlay nicht beheben (kein Eintrag zum Korrigieren); sie werden in der Prüfliste ausgewiesen und sind Anlass für eine Parser-Runde.

## Global Constraints

- Antwortsprache, Bezeichner, Kommentare, Docstrings: Deutsch (Code-Konvention des Repos).
- Nur Standardbibliothek; numpy/Pillow/pdftoppm ausschließlich in `seiten.py`/`goldstandard.py`.
- Kein Netzzugriff in Tests; `urlopen` wird nie in Tests aufgerufen.
- `llm/` (Seitenbilder, Rohantworten) und `.env` sind gitignored und werden nie committet. Rohantworten enthalten Transkriptionen der Quelle.
- Modelle ändern niemals `status`; `geprueft` entsteht ausschließlich über `daten/korrekturen.csv`.
- Beim Anwenden einer Korrektur muss `wert_alt` exakt dem aktuellen Parser-Wert entsprechen, sonst Abbruch mit `KorrekturFehler`.
- Commit-Trailer exakt: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
- Jeder Task: Test zuerst, Fehlschlag sehen, minimal implementieren, `python3 -m pytest -q` grün, committen.
- Arbeit auf einem Feature-Branch `llm-lesung` ab `parser-und-validierung`.

---

### Task 1: Seitenbilder (`strassen/seiten.py`, dpi-Parameter)

**Files:**
- Modify: `strassen/goldstandard.py:154-176` (`rendere_ausschnitt` bekommt `dpi`)
- Create: `strassen/seiten.py`
- Modify: `.gitignore`
- Test: `tests/test_seiten.py`

**Interfaces:**
- Produces: `seiten.seiten_dateiname(buchseite) -> str` (`s023.png`), `seiten.parse_seitenbereich(text|None) -> list[int]`, `seiten.rendere_seiten(seiten, ziel_dir, quelle_dir, dpi, render) -> list[Path]`, Konstanten `seiten.SEITEN_DIR`, `seiten.DPI = 300`.
- `goldstandard.rendere_ausschnitt(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi=150)`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_seiten.py
from pathlib import Path

from strassen import seiten


def test_seiten_dateiname_dreistellig():
    assert seiten.seiten_dateiname(23) == "s023.png"
    assert seiten.seiten_dateiname("7") == "s007.png"


def test_parse_seitenbereich_bereich_und_liste():
    assert seiten.parse_seitenbereich("23-25") == [23, 24, 25]
    assert seiten.parse_seitenbereich("23,45") == [23, 45]
    assert seiten.parse_seitenbereich("23-24,45") == [23, 24, 45]


def test_parse_seitenbereich_ohne_angabe_alle_buchseiten():
    alle = seiten.parse_seitenbereich(None)
    assert alle[0] == 2 and alle[-1] == 388 and len(alle) == 387


def test_rendere_seiten_ueberspringt_vorhandene_und_reicht_dpi_durch(tmp_path):
    aufrufe = []

    def render(band, pdf_seite, haelfte, quelle_dir, ziel_png, dpi):
        aufrufe.append((band, pdf_seite, haelfte, ziel_png.name, dpi))
        Path(ziel_png).write_bytes(b"png")

    (tmp_path / "s023.png").write_bytes(b"alt")
    neu = seiten.rendere_seiten([23, 24], tmp_path, "/quelle", dpi=300, render=render)
    assert [p.name for p in neu] == ["s024.png"]
    assert aufrufe == [(1, 12, "links", "s024.png", 300)]
```

- [ ] **Step 2: Run, expect ImportError**

Run: `python3 -m pytest tests/test_seiten.py -q`

- [ ] **Step 3: dpi-Parameter in `goldstandard.rendere_ausschnitt`**

Signatur ändern zu `def rendere_ausschnitt(band, pdf_seite, haelfte, quelle_dir, ziel_png: Path, dpi: int = 150) -> None:`; im `pdftoppm`-Aufruf `"-r", str(dpi)`; Docstring „Rendert die PDF-Seite bei `dpi` (Standard 150)…". Aufrufer in `ziehen` unverändert.

- [ ] **Step 4: `strassen/seiten.py`**

```python
"""Buchseiten als Graustufen-PNG für die unabhängige LLM-Lesung rendern.

Spec 2026-09-12, Abschnitt 3.1. Eine Datei je Buchseite unter llm/seiten/sNNN.png
(gitignored — Seitenbilder sind urheberrechtlich geschützt). Idempotent: vorhandene
Dateien werden übersprungen.

  python3 -m strassen.seiten [--quelle DIR] [--seiten 23-30,45]
"""
import argparse
from pathlib import Path

from strassen.goldstandard import QUELLE_PFAD, buchseite_zu_scan, rendere_ausschnitt

WURZEL = Path(__file__).resolve().parent.parent
SEITEN_DIR = WURZEL / "llm" / "seiten"
ERSTE_SEITE, LETZTE_SEITE = 2, 388   # Scan-Umfang, s. README „Quelle"
DPI = 300                            # 150 dpi (Goldstandard-Ausschnitte) reichen
                                     # den Modellen für 'Str.-Kl.:' und Stempel nicht


def seiten_dateiname(buchseite) -> str:
    return f"s{int(buchseite):03d}.png"


def parse_seitenbereich(text) -> list:
    """'23-30' -> 23..30, '23,45' -> [23, 45], None/leer -> alle Buchseiten."""
    if not text:
        return list(range(ERSTE_SEITE, LETZTE_SEITE + 1))
    seiten = []
    for teil in text.split(","):
        teil = teil.strip()
        if "-" in teil:
            a, b = teil.split("-", 1)
            seiten.extend(range(int(a), int(b) + 1))
        else:
            seiten.append(int(teil))
    return seiten


def rendere_seiten(seiten, ziel_dir=SEITEN_DIR, quelle_dir=QUELLE_PFAD, dpi=DPI,
                   render=rendere_ausschnitt) -> list:
    """Rendert alle noch fehlenden Buchseiten; gibt die neu erzeugten Pfade zurück."""
    ziel_dir = Path(ziel_dir)
    ziel_dir.mkdir(parents=True, exist_ok=True)
    neu = []
    for buchseite in seiten:
        ziel = ziel_dir / seiten_dateiname(buchseite)
        if ziel.exists():
            continue
        band, pdf_seite, haelfte = buchseite_zu_scan(buchseite)
        render(band, pdf_seite, haelfte, quelle_dir, ziel, dpi=dpi)
        neu.append(ziel)
    return neu


def _cli():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quelle", default=QUELLE_PFAD, help="Verzeichnis mit den beiden Dickhoff-PDFs")
    p.add_argument("--seiten", help="Buchseiten, z. B. 23-30,45 (Standard: alle)")
    p.add_argument("--ziel", default=str(SEITEN_DIR))
    a = p.parse_args()
    neu = rendere_seiten(parse_seitenbereich(a.seiten), a.ziel, a.quelle)
    print(f"{len(neu)} Seiten neu gerendert nach {a.ziel}")


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 5: `.gitignore` ergänzen**

```
# LLM-Lesung (Spec 2026-09-12): Seitenbilder und Rohantworten enthalten geschützte
# Inhalte bzw. Transkriptionen der Quelle; Zugangsdaten in .env.
llm/
.env
```

- [ ] **Step 6: Tests grün, dann Gesamtsuite**

Run: `python3 -m pytest -q` — erwartet: alle grün (233 + 4).

- [ ] **Step 7: Commit**

```bash
git add strassen/seiten.py strassen/goldstandard.py tests/test_seiten.py .gitignore
git commit -m "seiten.py: Buchseiten als 300-dpi-PNG für die LLM-Lesung; rendere_ausschnitt mit dpi-Parameter

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Leser — Konfiguration, Prompt, Anfrage, JSON-Extraktion

**Files:**
- Create: `strassen/llm_leser.py` (Teil 1), `strassen/llm_prompt.md`
- Test: `tests/test_llm_leser.py`

**Interfaces:**
- Produces: `lade_env(pfad) -> dict` (setzt `os.environ.setdefault`), `konfiguration() -> tuple[str, str]` (`LLM_BASE_URL`, `LLM_API_KEY`; `KonfigurationsFehler` wenn fehlend), `lade_prompt(pfad=PROMPT_PFAD) -> str`, `prompt_hash(prompt) -> str` (12 Hex), `baue_anfrage(modell, prompt, png_bytes, max_tokens=8000) -> dict`, `extrahiere_json(text) -> list` (`JsonFehler`), Ausnahmen `KonfigurationsFehler`, `JsonFehler`, `HttpFehler(status)`, `LaufAbbruch`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_llm_leser.py
import json

import pytest

from strassen import llm_leser as ll


def test_lade_env_setzt_nur_fehlende_variablen(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# Kommentar\nLLM_BASE_URL="https://inferenz.example/v1"\nLLM_API_KEY=geheim\n\n',
                   encoding="utf-8")
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "aus-umgebung")
    werte = ll.lade_env(env)
    assert werte == {"LLM_BASE_URL": "https://inferenz.example/v1", "LLM_API_KEY": "geheim"}
    base_url, key = ll.konfiguration()
    assert base_url == "https://inferenz.example/v1"
    assert key == "aus-umgebung"          # Umgebung schlägt .env


def test_konfiguration_ohne_werte_bricht_ab(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ll.KonfigurationsFehler):
        ll.konfiguration()


def test_baue_anfrage_traegt_bild_als_base64_und_temperatur_null():
    anfrage = ll.baue_anfrage("inferenz-qwen3-8-27b", "Lies.", b"\x89PNG", max_tokens=123)
    assert anfrage["model"] == "inferenz-qwen3-8-27b"
    assert anfrage["temperature"] == 0
    assert anfrage["max_tokens"] == 123
    inhalt = anfrage["messages"][0]["content"]
    assert inhalt[0] == {"type": "text", "text": "Lies."}
    assert inhalt[1]["image_url"]["url"] == "data:image/png;base64,iVBORw=="


def test_extrahiere_json_aus_code_fence_und_umgebendem_text():
    text = 'Hier die Einträge:\n```json\n[{"schl_nr": "00001"}]\n```\nFertig.'
    assert ll.extrahiere_json(text) == [{"schl_nr": "00001"}]


def test_extrahiere_json_nacktes_array():
    assert ll.extrahiere_json('[{"a": 1}, {"a": 2}]') == [{"a": 1}, {"a": 2}]


@pytest.mark.parametrize("text", ["kein json", '{"a": 1}', "[{'a': 1}]", "[1, 2"])
def test_extrahiere_json_verlangt_liste_von_objekten(text):
    with pytest.raises(ll.JsonFehler):
        ll.extrahiere_json(text)


def test_prompt_datei_existiert_und_hash_stabil():
    prompt = ll.lade_prompt()
    assert "Schl.-Nr." in prompt and "JSON" in prompt
    assert ll.prompt_hash(prompt) == ll.prompt_hash(prompt)
    assert len(ll.prompt_hash(prompt)) == 12
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: `strassen/llm_prompt.md`** (wörtlich; wird später in Task 11 nur an Entwicklungsseiten nachgeschärft)

````markdown
Du transkribierst eine Seite aus einem gedruckten Straßenlexikon (Essen, 2015). Jeder
Eintrag beginnt mit dem heutigen Straßennamen als fett gedrucktes Stichwort, dann folgen
Kopfangaben (`Schl.-Nr.:` fünfstellige Schlüsselnummer, `Stadtteil:` oder `Stadtteile:`,
`Str.-Kl.:` Straßenklasse, `Str.-Gr.:` Namensgruppe), dann die Namenskette (Datum,
Doppelpunkt, Name; mehrere durch Komma/Semikolon), danach ein Erläuterungstext in Prosa.
Manche Einträge bestehen nur aus `Siehe <Name>`.

Regeln:
1. Transkribiere ausschließlich, was auf der Seite steht. Nichts ergänzen, nichts
   modernisieren, keine Rechtschreibung „verbessern". Unleserliches als `?` markieren.
2. Gib GENAU EINE JSON-Liste zurück, ohne Text davor oder danach. Ein Objekt je Eintrag,
   der auf dieser Seite mit einem Stichwort BEGINNT. Einträge, die von der Vorseite
   hereinlaufen (kein Stichwort oben auf der Seite), auslassen.
3. Felder je Objekt (alle immer angeben, leer als "" bzw. []):
   - "schl_nr": Schlüsselnummer wie gedruckt, fünfstellig, z. B. "00417"
   - "lemma": das Stichwort
   - "stadtteile": Liste der Stadtteile, jeder einzeln, z. B. ["Frohnhausen", "Holsterhausen"]
   - "strassenklasse": Liste, z. B. ["Gemeindestraße"]
   - "namensgruppe": Text nach `Str.-Gr.:`
   - "verweis_auf": nur bei `Siehe <Name>` der Name, sonst ""
   - "stadien": Liste der Namensstadien in gedruckter Reihenfolge, je
     {"datum": "<Datum WÖRTLICH wie gedruckt, z. B. '29.08.1927', '16. Mai 1902', 'um 1900',
     'vor 1898', 'im 16. Jahrhundert', '1927'>", "name": "<Name wie gedruckt, inkl.
     Klammerzusätzen wie '(tlw.)'>", "urspruenglich": true wenn 'urspr.'/'ursprünglich'
     davor steht, sonst false}
     Ein Stadium ohne Datum: "datum": "".
   - "unvollstaendig": true, wenn der Eintrag am Seitenende abbricht, sonst false
4. Den Erläuterungstext NICHT transkribieren.
5. Kein Eintrag darf fehlen; die Schlüsselnummern laufen auf der Seite fortlaufend.

Beispiel eines Objekts:
{"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": ["Frohnhausen"],
 "strassenklasse": ["Gemeindestraße"], "namensgruppe": "Stadt und Ort", "verweis_auf": "",
 "stadien": [{"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": false},
             {"datum": "16.05.1902", "name": "Aachener Straße", "urspruenglich": false}],
 "unvollstaendig": false}
````

- [ ] **Step 4: `strassen/llm_leser.py` (Teil 1)**

```python
"""Unabhängige LLM-Lesung: je Buchseite das Seitenbild an ein bildfähiges Modell
schicken und die Antwort als JSON sichern (Spec 2026-09-12, Abschnitt 3.2).

Das Modell sieht NUR das Bild — keinen OCR-Text, keine Parser-Werte. Rohantworten
liegen gitignored unter llm/antworten/<modell>/sNNN.json; ein Wiederholungslauf
überspringt vorhandene Antworten.

  python3 -m strassen.llm_leser --modell inferenz-qwen3-8-27b [--seiten 23-30] [--neu]

Konfiguration über Umgebungsvariablen LLM_BASE_URL (OpenAI-kompatibler Endpunkt, ohne
'/chat/completions') und LLM_API_KEY; eine .env in der Repo-Wurzel wird gelesen,
gesetzte Umgebungsvariablen haben Vorrang.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
PROMPT_PFAD = WURZEL / "strassen" / "llm_prompt.md"
ANTWORTEN_DIR = WURZEL / "llm" / "antworten"
ENV_PFAD = WURZEL / ".env"
MAX_TOKENS = 8000
MAX_JSON_VERSUCHE = 3      # 1 Versuch + 2 Wiederholungen bei unlesbarem JSON
MAX_HTTP_VERSUCHE = 5      # 429/5xx: exponentielles Warten, dann Abbruch des Laufs


class KonfigurationsFehler(RuntimeError):
    pass


class JsonFehler(ValueError):
    pass


class HttpFehler(RuntimeError):
    def __init__(self, status: int, text: str = ""):
        super().__init__(f"HTTP {status}: {text[:200]}")
        self.status = status


class LaufAbbruch(RuntimeError):
    pass


def lade_env(pfad=ENV_PFAD) -> dict:
    """Einfacher KEY=WERT-Parser (Kommentare, Leerzeilen, Anführungszeichen); setzt nur
    Variablen, die in der Umgebung noch fehlen."""
    werte = {}
    pfad = Path(pfad)
    if not pfad.is_file():
        return werte
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        werte[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in werte.items():
        os.environ.setdefault(k, v)
    return werte


def konfiguration() -> tuple:
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("LLM_API_KEY", "")
    if not base_url or not api_key:
        raise KonfigurationsFehler("LLM_BASE_URL und LLM_API_KEY müssen gesetzt sein (.env oder Umgebung)")
    return base_url, api_key


def lade_prompt(pfad=PROMPT_PFAD) -> str:
    return Path(pfad).read_text(encoding="utf-8")


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]


def baue_anfrage(modell: str, prompt: str, png_bytes: bytes, max_tokens: int = MAX_TOKENS) -> dict:
    bild = base64.b64encode(png_bytes).decode("ascii")
    return {
        "model": modell,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{bild}"}},
        ]}],
    }


_CODE_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extrahiere_json(text: str) -> list:
    """JSON-Liste von Objekten aus einer Modellantwort: Code-Fence bevorzugt, sonst
    vom ersten '[' bis zum letzten ']'."""
    m = _CODE_FENCE.search(text)
    kern = m.group(1) if m else text
    anfang, ende = kern.find("["), kern.rfind("]")
    if anfang < 0 or ende < anfang:
        raise JsonFehler("keine JSON-Liste gefunden")
    try:
        daten = json.loads(kern[anfang:ende + 1])
    except json.JSONDecodeError as e:
        raise JsonFehler(str(e)) from e
    if not isinstance(daten, list) or not all(isinstance(e, dict) for e in daten):
        raise JsonFehler("erwartet: Liste von Objekten")
    return daten
```

- [ ] **Step 5: Tests grün; Commit**

```bash
git add strassen/llm_leser.py strassen/llm_prompt.md tests/test_llm_leser.py
git commit -m "llm_leser: Konfiguration, Prompt, Anfrage-Aufbau und JSON-Extraktion

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Leser — Senden, Wiederholung, Cache, CLI

**Files:**
- Modify: `strassen/llm_leser.py` (Teil 2, anhängen)
- Test: `tests/test_llm_leser.py` (ergänzen)

**Interfaces:**
- Produces: `sende(anfrage, base_url, api_key, timeout=300) -> str` (Antworttext), `lies_seite(buchseite, modell, png_pfad, prompt, sende_fn, ziel_dir=ANTWORTEN_DIR, neu=False, schlafen=time.sleep) -> dict`, `antwort_pfad(ziel_dir, modell, buchseite) -> Path`.
- Antwortdatei (JSON): `{"buchseite": int, "modell": str, "zeitstempel": ISO, "prompt_hash": str, "rohtext": str, "eintraege": list|None, "fehler": ""|"unlesbar"}`.
- `sende_fn(anfrage: dict) -> str`; wirft `HttpFehler`.

- [ ] **Step 1: Failing tests (anhängen)**

```python
def _png(tmp_path):
    p = tmp_path / "s023.png"
    p.write_bytes(b"\x89PNG")
    return p


def test_lies_seite_speichert_eintraege_und_metadaten(tmp_path):
    antworten = tmp_path / "antworten"
    gesendet = []

    def sende_fn(anfrage):
        gesendet.append(anfrage)
        return '```json\n[{"schl_nr": "00001", "lemma": "Aachener Straße"}]\n```'

    erg = ll.lies_seite(23, "m", _png(tmp_path), "PROMPT", sende_fn, ziel_dir=antworten)
    assert erg["eintraege"] == [{"schl_nr": "00001", "lemma": "Aachener Straße"}]
    assert erg["fehler"] == "" and erg["buchseite"] == 23 and erg["modell"] == "m"
    assert erg["prompt_hash"] == ll.prompt_hash("PROMPT")
    gespeichert = json.loads((antworten / "m" / "s023.json").read_text(encoding="utf-8"))
    assert gespeichert["eintraege"] == erg["eintraege"]
    assert len(gesendet) == 1 and gesendet[0]["model"] == "m"


def test_lies_seite_nutzt_vorhandene_antwort_ohne_zu_senden(tmp_path):
    antworten = tmp_path / "antworten"
    (antworten / "m").mkdir(parents=True)
    (antworten / "m" / "s023.json").write_text(json.dumps({"buchseite": 23, "eintraege": [], "fehler": ""}),
                                               encoding="utf-8")

    def sende_fn(anfrage):
        raise AssertionError("darf nicht senden")

    erg = ll.lies_seite(23, "m", _png(tmp_path), "P", sende_fn, ziel_dir=antworten)
    assert erg["eintraege"] == []


def test_lies_seite_neu_erzwingt_anfrage(tmp_path):
    antworten = tmp_path / "antworten"
    (antworten / "m").mkdir(parents=True)
    (antworten / "m" / "s023.json").write_text("{}", encoding="utf-8")
    erg = ll.lies_seite(23, "m", _png(tmp_path), "P", lambda a: "[]", ziel_dir=antworten, neu=True)
    assert erg["eintraege"] == []


def test_lies_seite_wiederholt_bei_unlesbarem_json_und_markiert_dann(tmp_path):
    aufrufe = []

    def sende_fn(anfrage):
        aufrufe.append(1)
        return "kein json"

    erg = ll.lies_seite(23, "m", _png(tmp_path), "P", sende_fn, ziel_dir=tmp_path / "a")
    assert len(aufrufe) == ll.MAX_JSON_VERSUCHE == 3
    assert erg["fehler"] == "unlesbar" and erg["eintraege"] is None
    assert erg["rohtext"] == "kein json"


def test_lies_seite_wartet_bei_429_und_bricht_nach_fuenf_versuchen_ab(tmp_path):
    pausen = []
    versuche = []

    def sende_fn(anfrage):
        versuche.append(1)
        raise ll.HttpFehler(429, "zu viele Anfragen")

    with pytest.raises(ll.LaufAbbruch):
        ll.lies_seite(23, "m", _png(tmp_path), "P", sende_fn, ziel_dir=tmp_path / "a",
                      schlafen=pausen.append)
    assert len(versuche) == ll.MAX_HTTP_VERSUCHE == 5
    assert pausen == [1, 2, 4, 8]          # exponentiell, vor jedem Wiederholungsversuch
    assert not (tmp_path / "a" / "m" / "s023.json").exists()


def test_lies_seite_reicht_4xx_ausser_429_sofort_durch(tmp_path):
    def sende_fn(anfrage):
        raise ll.HttpFehler(401, "unauthorized")

    with pytest.raises(ll.HttpFehler):
        ll.lies_seite(23, "m", _png(tmp_path), "P", sende_fn, ziel_dir=tmp_path / "a", schlafen=lambda s: None)


def test_sende_baut_openai_kompatible_anfrage(monkeypatch):
    erfasst = {}

    class Antwort:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "[]"}}]}).encode()

    def urlopen(req, timeout):
        erfasst["url"] = req.full_url
        erfasst["auth"] = req.get_header("Authorization")
        erfasst["body"] = json.loads(req.data)
        return Antwort()

    monkeypatch.setattr(ll.urllib.request, "urlopen", urlopen)
    text = ll.sende({"model": "m"}, "https://h/v1", "k")
    assert text == "[]"
    assert erfasst["url"] == "https://h/v1/chat/completions"
    assert erfasst["auth"] == "Bearer k"
    assert erfasst["body"] == {"model": "m"}
```

- [ ] **Step 2: Run, expect AttributeError für `lies_seite`/`sende`**

- [ ] **Step 3: Implementierung (anhängen)**

```python
def sende(anfrage: dict, base_url: str, api_key: str, timeout: int = 300) -> str:
    """POST an <base_url>/chat/completions; gibt den Antworttext des Modells zurück."""
    req = urllib.request.Request(
        f"{base_url}/chat/completions", data=json.dumps(anfrage).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise HttpFehler(e.code, e.read().decode("utf-8", errors="replace")) from e
    return daten["choices"][0]["message"]["content"]


def antwort_pfad(ziel_dir, modell: str, buchseite) -> Path:
    return Path(ziel_dir) / modell / f"s{int(buchseite):03d}.json"


def _sende_mit_wiederholung(anfrage: dict, sende_fn, schlafen) -> str:
    for versuch in range(MAX_HTTP_VERSUCHE):
        try:
            return sende_fn(anfrage)
        except HttpFehler as e:
            if e.status != 429 and e.status < 500:
                raise
            if versuch < MAX_HTTP_VERSUCHE - 1:
                schlafen(2 ** versuch)
    raise LaufAbbruch(f"{MAX_HTTP_VERSUCHE} Versuche gescheitert (429/5xx) — Lauf abgebrochen, "
                      f"fehlende Seiten werden beim nächsten Lauf nachgeholt")


def lies_seite(buchseite, modell: str, png_pfad, prompt: str, sende_fn,
               ziel_dir=ANTWORTEN_DIR, neu: bool = False, schlafen=time.sleep) -> dict:
    """Eine Buchseite lesen lassen. Vorhandene Antwort wird wiederverwendet (außer neu=True).
    Unlesbares JSON: bis MAX_JSON_VERSUCHE identische Anfragen, dann fehler='unlesbar'."""
    ziel = antwort_pfad(ziel_dir, modell, buchseite)
    if ziel.exists() and not neu:
        return json.loads(ziel.read_text(encoding="utf-8"))

    anfrage = baue_anfrage(modell, prompt, Path(png_pfad).read_bytes())
    rohtext, eintraege = "", None
    for _ in range(MAX_JSON_VERSUCHE):
        rohtext = _sende_mit_wiederholung(anfrage, sende_fn, schlafen)
        try:
            eintraege = extrahiere_json(rohtext)
            break
        except JsonFehler:
            continue

    ergebnis = {"buchseite": int(buchseite), "modell": modell,
                "zeitstempel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "prompt_hash": prompt_hash(prompt), "rohtext": rohtext,
                "eintraege": eintraege, "fehler": "" if eintraege is not None else "unlesbar"}
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1), encoding="utf-8")
    return ergebnis


def _cli():
    from strassen.seiten import SEITEN_DIR, parse_seitenbereich, seiten_dateiname
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modell", required=True)
    p.add_argument("--seiten", help="Buchseiten, z. B. 23-30 (Standard: alle mit Seitenbild)")
    p.add_argument("--neu", action="store_true", help="vorhandene Antworten neu anfordern")
    p.add_argument("--seiten-dir", default=str(SEITEN_DIR))
    p.add_argument("--antworten-dir", default=str(ANTWORTEN_DIR))
    a = p.parse_args()
    lade_env()
    base_url, api_key = konfiguration()
    sende_fn = partial(sende, base_url=base_url, api_key=api_key)
    prompt = lade_prompt()
    seiten = parse_seitenbereich(a.seiten)
    gelesen = unlesbar = 0
    for b in seiten:
        png = Path(a.seiten_dir) / seiten_dateiname(b)
        if not png.exists():
            continue
        erg = lies_seite(b, a.modell, png, prompt, sende_fn, a.antworten_dir, a.neu)
        gelesen += 1
        unlesbar += erg["fehler"] == "unlesbar"
        print(f"s{b:03d}: {len(erg['eintraege'] or [])} Einträge{' (unlesbar)' if erg['fehler'] else ''}",
              flush=True)
    print(f"{gelesen} Seiten, davon {unlesbar} unlesbar — Modell {a.modell}")


if __name__ == "__main__":
    _cli()
```

- [ ] **Step 4: Tests grün; Commit**

```bash
git add strassen/llm_leser.py tests/test_llm_leser.py
git commit -m "llm_leser: Senden mit Wiederholung, Antwort-Cache je Seite, CLI

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: `datum.lese_text` und Struktur-Eingang für `differenz.vergleiche`

**Files:**
- Modify: `strassen/datum.py` (nach `lese_datum`)
- Modify: `strassen/differenz.py:39-50, 83-84`
- Test: `tests/test_datum.py`, `tests/test_differenz.py` (ergänzen)

**Interfaces:**
- Produces: `datum.lese_text(text: str) -> Datum | None` — gedruckter Datumstext (ohne oder mit Trenner am Ende) → `Datum`; `None` wenn kein Stempelmuster passt; leerer Text → `Datum("", "unbekannt", "", "")`.
- `differenz.vergleiche(alt, neu)` akzeptiert je Seite ein Verzeichnis **oder** ein Tupel `(strassen, namen)` mit `strassen`: Liste oder Dict (`schl_nr` → Zeile), `namen`: Liste von Zeilen oder Dict (`schl_nr` → Liste). Neue Hilfsfunktion `differenz.als_struktur(strassen, namen) -> (dict, dict)`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_datum.py — anhängen
from strassen.datum import lese_text


def test_lese_text_tagesdatum_numerisch_und_wortform():
    assert lese_text("29.08.1927")[:2] == ("1927-08-29", "tag")
    assert lese_text("16. Mai 1902:")[:2] == ("1902-05-16", "tag")


def test_lese_text_qualifier_jahr_jahrhundert():
    assert lese_text("vor 1898")[:2] == ("1898", "vor")
    assert lese_text("um 1900")[:2] == ("1900", "jahr")
    assert lese_text("im 16. Jahrhundert")[:2] == ("1501", "jahrhundert")
    assert lese_text("1927")[:2] == ("1927", "jahr")


def test_lese_text_leer_und_unpassend():
    assert lese_text("")[:2] == ("", "unbekannt")
    assert lese_text("16. Jh.") is None
    assert lese_text("Frühjahr 1920") is None
```

```python
# tests/test_differenz.py — anhängen
def test_vergleiche_nimmt_strukturen_statt_verzeichnisse():
    alt = ([_s("00001", "A")], [_n("00001", 1, "1900", "A")])
    neu = ([_s("00001", "B")], [_n("00001", 1, "1900", "A")])
    d = vergleiche(alt, neu)
    assert d["kopffeld_veraendert"] == [{"schl_nr": "00001", "lemma": "A", "feld": "lemma", "alt": "A", "neu": "B"}]
```

(`_s`/`_n` sind die vorhandenen Fixture-Helfer der Datei; `_n(schl, stadium, gueltig_ab, name)` existiert dort — Signatur prüfen und ggf. anpassen.)

- [ ] **Step 2: Run, expect Fehler**

- [ ] **Step 3: `datum.lese_text`**

```python
def lese_text(text: str):
    """Gedruckter Datumstext ('29.08.1927', 'um 1900', 'im 16. Jahrhundert', auch mit
    Trenner am Ende) -> Datum; None, wenn kein Stempelmuster passt; leer -> unbekannt.
    Gemeinsame Funktion für LLM-Vergleich und Korrektur-Overlay (Spec 2026-09-12)."""
    t = (text or "").strip()
    if not t:
        return Datum("", "unbekannt", "", "")
    m = DATUMSSTEMPEL.fullmatch(t)
    return lese_datum(m) if m else None
```

- [ ] **Step 4: `differenz.als_struktur` und `vergleiche`**

```python
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
```

In `vergleiche`: `alt_s, alt_n = _lade_oder_uebernimm(alt_dir)` / analog neu; Parameter umbenennen zu `alt, neu`; Docstring des Moduls um den Struktur-Eingang ergänzen.

- [ ] **Step 5: Tests grün; Commit**

```bash
git add strassen/datum.py strassen/differenz.py tests/test_datum.py tests/test_differenz.py
git commit -m "datum.lese_text für gedruckte Datumstexte; differenz.vergleiche nimmt Strukturen entgegen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Vergleich — Antworten in Datensatzform

**Files:**
- Create: `strassen/llm_vergleich.py` (Teil 1)
- Create: `tests/fixtures/llm_antwort_beispiel.json` (synthetisch, Form der Antwortdatei aus Task 3)
- Test: `tests/test_llm_vergleich.py`

**Interfaces:**
- Produces: `normalisiere_antwort(antwort: dict) -> tuple[list, list, list]` → `(strassen, namen, probleme)`; `strassen`-Zeilen mit den Feldern von `ausgabe.FELDER_STRASSEN` (`status="modell"`), `namen`-Zeilen mit `ausgabe.FELDER_NAMEN`; `probleme`: `[{"schl_nr", "buchseite", "feld", "text", "grund"}]`; `lade_antworten(antworten_dir, modell) -> dict[int, dict]` (Buchseite → Antwortdatei); `kurzname(modell) -> str` (`qwen` | `mistral`, sonst `ValueError`).
- Konstante `STATUS_MODELL = "modell"`.

- [ ] **Step 1: Fixture**

```json
{"buchseite": 23, "modell": "inferenz-qwen3-8-27b", "zeitstempel": "2026-09-12T10:00:00+00:00",
 "prompt_hash": "abc", "rohtext": "", "fehler": "",
 "eintraege": [
  {"schl_nr": "1", "lemma": "Aachener Straße", "stadtteile": ["Frohnhausen"],
   "strassenklasse": ["Gemeindestraße"], "namensgruppe": "Stadt und Ort", "verweis_auf": "",
   "stadien": [{"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": false},
               {"datum": "16.05.1902:", "name": "Aachener Straße", "urspruenglich": false}],
   "unvollstaendig": false},
  {"schl_nr": "00002", "lemma": "Abteistraße", "stadtteile": ["Werden"],
   "strassenklasse": ["Bundesstraße"], "namensgruppe": "Lagebezeichnung", "verweis_auf": "",
   "stadien": [{"datum": "16. Jh.", "name": "Abteistraße", "urspruenglich": true}],
   "unvollstaendig": true},
  {"schl_nr": "00003", "lemma": "Achenbachstraße", "stadtteile": [], "strassenklasse": [],
   "namensgruppe": "", "verweis_auf": "Achenbachweg", "stadien": [], "unvollstaendig": false}
 ]}
```

- [ ] **Step 2: Failing tests**

```python
# tests/test_llm_vergleich.py
import json
from pathlib import Path

import pytest

from strassen import llm_vergleich as lv

FIXTURE = Path(__file__).parent / "fixtures" / "llm_antwort_beispiel.json"


def _antwort():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_normalisiere_kopffelder_in_datensatzform():
    strassen, namen, probleme = lv.normalisiere_antwort(_antwort())
    assert [s["schl_nr"] for s in strassen] == ["00001", "00002", "00003"]   # '1' -> '00001'
    a = strassen[0]
    assert a["lemma"] == "Aachener Straße" and a["stadtteile"] == "Frohnhausen"
    assert a["strassenklasse"] == "Gemeindestraße" and a["buchseite"] == 23
    assert a["status"] == lv.STATUS_MODELL
    assert strassen[2]["verweis_auf"] == "Achenbachweg"


def test_normalisiere_stadien_ueber_datum_lese_text():
    _, namen, _ = lv.normalisiere_antwort(_antwort())
    st = [n for n in namen if n["schl_nr"] == "00001"]
    assert [(n["stadium"], n["gueltig_ab"], n["datum_praezision"], n["name"], n["ist_urspruenglich"]) for n in st] == [
        (1, "1898", "vor", "Victoriastraße (tlw.)", "falsch"),
        (2, "1902-05-16", "tag", "Aachener Straße", "falsch")]


def test_normalisiere_meldet_nicht_normalisierbares_datum():
    _, namen, probleme = lv.normalisiere_antwort(_antwort())
    abtei = [n for n in namen if n["schl_nr"] == "00002"][0]
    assert (abtei["gueltig_ab"], abtei["datum_praezision"], abtei["ist_urspruenglich"]) == ("", "unbekannt", "wahr")
    assert probleme == [{"schl_nr": "00002", "buchseite": 23, "feld": "stadium_1_datum",
                         "text": "16. Jh.", "grund": "Datum nicht normalisierbar"}]


def test_normalisiere_markiert_unvollstaendige_eintraege():
    strassen, _, _ = lv.normalisiere_antwort(_antwort())
    assert lv.ist_unvollstaendig(strassen[1]) and not lv.ist_unvollstaendig(strassen[0])


def test_normalisiere_unlesbare_antwort_liefert_nichts():
    assert lv.normalisiere_antwort({"buchseite": 5, "eintraege": None, "fehler": "unlesbar"}) == ([], [], [])


def test_lade_antworten_indexiert_nach_buchseite(tmp_path):
    (tmp_path / "m").mkdir()
    (tmp_path / "m" / "s023.json").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    antworten = lv.lade_antworten(tmp_path, "m")
    assert list(antworten) == [23] and antworten[23]["buchseite"] == 23


@pytest.mark.parametrize("modell,kurz", [("inferenz-qwen3-8-27b", "qwen"), ("inferenz-mistral-small-4-119b", "mistral")])
def test_kurzname(modell, kurz):
    assert lv.kurzname(modell) == kurz


def test_kurzname_unbekannt():
    with pytest.raises(ValueError):
        lv.kurzname("gpt-x")
```

- [ ] **Step 3: Run, expect ImportError**

- [ ] **Step 4: Implementierung (Teil 1)**

```python
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

WURZEL = Path(__file__).resolve().parent.parent
ANTWORTEN_DIR = WURZEL / "llm" / "antworten"
DATEN_DIR = WURZEL / "daten"
PRUEFLISTE_PFAD = DATEN_DIR / "pruefung_llm.csv"
KENNZAHLEN_PFAD = WURZEL / "docs" / "llm_lesung.md"
STATUS_MODELL = "modell"
KURZNAMEN = ("qwen", "mistral")
KOPFFELDER = ["lemma", "stadtteile", "strassenklasse", "namensgruppe", "verweis_auf"]
GRUND_DATUM = "Datum nicht normalisierbar"

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
    buchseite = int(antwort.get("buchseite", 0))
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
        for i, s in enumerate(e.get("stadien") or [], 1):
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
```

- [ ] **Step 5: Tests grün; Commit**

```bash
git add strassen/llm_vergleich.py tests/test_llm_vergleich.py tests/fixtures/llm_antwort_beispiel.json
git commit -m "llm_vergleich: Modellantworten in Datensatzform (Kopffelder, Stadien über datum.lese_text)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Vergleich — Prüfliste und Kennzahlen

**Files:**
- Modify: `strassen/llm_vergleich.py` (Teil 2)
- Test: `tests/test_llm_vergleich.py` (ergänzen)

**Interfaces:**
- Produces: `feldwert(strassen: dict, namen: dict, schl_nr, feld) -> str | None` (Wert eines Prüffelds in Stichproben-Form; `None` wenn Eintrag/Stadium fehlt; `feld="eintrag"` → Lemma), `baue_pruefliste(parser: tuple, modelle: dict[str, dict]) -> tuple[list, dict]` → `(zeilen, kennzahlen)`; `modelle`: Kurzname → `{"antworten": {buchseite: antwortdatei}}`; `schreibe_pruefliste(zeilen, pfad)`; `formatiere_kennzahlen_md(kennzahlen) -> str`.
- `FELDER_PRUEFLISTE = ["schl_nr", "buchseite", "feld", "wert_parser", "wert_qwen", "wert_mistral", "status_parser", "einig", "korrektur", "beleg"]`.
- Feldnamen in `feld`: `lemma`…`verweis_auf`, `stadium_N_datum`, `stadium_N_name`, `stadium_N` (ganzes Stadium fehlt/überzählig; Wert `"<datum> <name>"`), `eintrag` (Eintrag fehlt/überzählig; Wert = Lemma).
- `einig` ∈ {`beide`, `eines`, `unlesbar`}.

- [ ] **Step 1: Failing tests (anhängen)**

```python
def _parser():
    strassen = [
        {"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausen", "strassenklasse": "Gemeindestraße",
         "namensgruppe": "Stadt und Ort", "verweis_auf": "", "buchseite": 23, "status": "automatisch"},
        {"schl_nr": "00002", "lemma": "Abteistraße", "stadtteile": "Werden", "strassenklasse": "Bundesstraße",
         "namensgruppe": "Lagebezeichnung", "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
        {"schl_nr": "00004", "lemma": "Nur Parser", "stadtteile": "", "strassenklasse": "", "namensgruppe": "",
         "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
        {"schl_nr": "00099", "lemma": "Andere Seite", "stadtteile": "X", "strassenklasse": "Y", "namensgruppe": "Z",
         "verweis_auf": "", "buchseite": 40, "status": "automatisch"},
    ]
    namen = [
        {"schl_nr": "00001", "stadium": 1, "gueltig_ab": "1898", "datum_praezision": "vor", "name": "Victoriastraße (tlw.)", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00001", "stadium": 2, "gueltig_ab": "1902-05-16", "datum_praezision": "tag", "name": "Aachener Straße", "ist_urspruenglich": "falsch"},
        {"schl_nr": "00002", "stadium": 1, "gueltig_ab": "1501", "datum_praezision": "jahrhundert", "name": "Abteistraße", "ist_urspruenglich": "wahr"},
    ]
    return strassen, namen


def _modell_antwort(**aenderungen):
    a = _antwort()
    for schl, felder in aenderungen.items():
        e = next(x for x in a["eintraege"] if lv._schl_nr(x["schl_nr"]) == schl)
        e.update(felder)
    return a


def test_feldwert_kopf_stadium_eintrag_und_fehlend():
    s, n = lv.als_struktur(*_parser())
    assert lv.feldwert(s, n, "00001", "lemma") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_1_datum") == "vor 1898"
    assert lv.feldwert(s, n, "00001", "stadium_2_name") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_2") == "1902-05-16 Aachener Straße"
    assert lv.feldwert(s, n, "00001", "eintrag") == "Aachener Straße"
    assert lv.feldwert(s, n, "00001", "stadium_3_name") is None
    assert lv.feldwert(s, n, "00007", "lemma") is None


def test_pruefliste_beide_modelle_einig_gegen_parser_steht_oben():
    qwen = _modell_antwort(**{"00001": {"lemma": "Aachenerstraße"}})
    mistral = _modell_antwort(**{"00001": {"lemma": "Aachenerstraße"}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: mistral}}})
    erste = zeilen[0]
    assert (erste["schl_nr"], erste["feld"], erste["einig"]) == ("00001", "lemma", "beide")
    assert (erste["wert_parser"], erste["wert_qwen"], erste["wert_mistral"]) == ("Aachener Straße", "Aachenerstraße", "Aachenerstraße")
    assert erste["status_parser"] == "automatisch" and erste["korrektur"] == "" and erste["beleg"] == ""


def test_pruefliste_nur_ein_modell_weicht_ab_fuellt_anderes_mit_eigenem_wert():
    qwen = _modell_antwort(**{"00001": {"stadtteile": ["Frohnhausen", "Holsterhausen"]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    z = next(x for x in zeilen if x["feld"] == "stadtteile" and x["schl_nr"] == "00001")
    assert z["einig"] == "eines"
    assert z["wert_qwen"] == "Frohnhausen; Holsterhausen" and z["wert_mistral"] == "Frohnhausen"


def test_pruefliste_vollstaendigkeit_je_gelesener_seite():
    zeilen, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    felder = {(z["schl_nr"], z["feld"]): z for z in zeilen}
    fehlt = felder[("00004", "eintrag")]          # Parser hat, Modelle nicht
    assert fehlt["wert_parser"] == "Nur Parser" and fehlt["wert_qwen"] == "" and fehlt["einig"] == "beide"
    nur_modell = felder[("00003", "eintrag")]     # Modelle haben, Parser nicht
    assert nur_modell["wert_parser"] == "" and nur_modell["wert_qwen"] == "Achenbachstraße"
    assert ("00099", "eintrag") not in felder      # Seite 40 wurde nicht gelesen
    assert kz["qwen"]["eintraege_fehlend"] == 1 and kz["qwen"]["eintraege_nur_modell"] == 1


def test_pruefliste_datum_und_name_je_stadium():
    qwen = _modell_antwort(**{"00001": {"stadien": [
        {"datum": "vor 1898", "name": "Victoriastraße (tlw.)", "urspruenglich": False},
        {"datum": "16.05.1920", "name": "Aachener Straße", "urspruenglich": False}]}})
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: qwen}}, "mistral": {"antworten": {23: _antwort()}}})
    z = next(x for x in zeilen if x["feld"] == "stadium_2_datum")
    assert (z["wert_parser"], z["wert_qwen"], z["wert_mistral"], z["einig"]) == ("1902-05-16", "1920-05-16", "1902-05-16", "eines")


def test_pruefliste_unlesbare_seite_eines_modells():
    zeilen, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _modell_antwort(**{"00001": {"lemma": "X"}})}},
                                                 "mistral": {"antworten": {23: {"buchseite": 23, "eintraege": None, "fehler": "unlesbar"}}}})
    z = next(x for x in zeilen if x["feld"] == "lemma" and x["schl_nr"] == "00001")
    assert z["einig"] == "unlesbar" and z["wert_mistral"] == ""
    assert kz["mistral"]["seiten_unlesbar"] == 1


def test_pruefliste_unvollstaendiger_eintrag_vergleicht_nur_kopf():
    # 00002 ist im Fixture unvollstaendig=true und hat dort nur 1 Stadium mit unlesbarem Datum
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    assert not [z for z in zeilen if z["schl_nr"] == "00002" and z["feld"].startswith("stadium")]


def test_kennzahlen_uebereinstimmung_je_feldtyp_und_status():
    _, kz = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _modell_antwort(**{"00001": {"lemma": "X"}})}},
                                            "mistral": {"antworten": {23: _antwort()}}})
    q = kz["qwen"]
    assert q["seiten_gelesen"] == 1 and q["eintraege_modell"] == 3
    assert q["uebereinstimmung"]["automatisch"]["lemma"] == {"verglichen": 1, "gleich": 0}
    assert q["uebereinstimmung"]["unsicher"]["lemma"] == {"verglichen": 1, "gleich": 1}   # 00002; 00004 fehlt beim Modell
    assert q["datum_nicht_normalisierbar"] == 1
    md = lv.formatiere_kennzahlen_md(kz)
    assert "qwen" in md and "Status" in md and "verändern den Status nicht" in md


def test_schreibe_pruefliste_spalten(tmp_path):
    zeilen, _ = lv.baue_pruefliste(_parser(), {"qwen": {"antworten": {23: _antwort()}}, "mistral": {"antworten": {23: _antwort()}}})
    pfad = tmp_path / "pruefung_llm.csv"
    lv.schreibe_pruefliste(zeilen, pfad)
    with open(pfad, encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        assert r.fieldnames == lv.FELDER_PRUEFLISTE
```

(`import csv` oben in der Testdatei ergänzen; `lv.als_struktur` per `from strassen.differenz import als_struktur` im Modul re-exportiert — im Test über `lv.als_struktur` erreichbar.)

- [ ] **Step 2: Run, expect AttributeError**

- [ ] **Step 3: Implementierung (Teil 2, anhängen)**

```python
FELDER_PRUEFLISTE = ["schl_nr", "buchseite", "feld", "wert_parser", "wert_qwen", "wert_mistral",
                     "status_parser", "einig", "korrektur", "beleg"]
_EINIG_RANG = {"beide": 0, "eines": 1, "unlesbar": 2}
_STADIUMFELD = re.compile(r"^stadium_(\d+)(?:_(datum|name))?$")


def _stadium_text(z) -> str:
    return f"{formatiere_datum(z['datum_praezision'], z['gueltig_ab'])} {z['name']}".strip()


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
        abw[(e["schl_nr"], f"stadium_{e['stadium']}_datum")] = True
    for e in d["name_veraendert"]:
        abw[(e["schl_nr"], f"stadium_{e['stadium']}_name")] = True
    for e in d["stadium_verloren"]:
        n = _stadium_index(parser_n[e["schl_nr"]], e["alt"])
        abw[(e["schl_nr"], f"stadium_{n}")] = True
    for e in d["stadium_gewonnen"]:
        n = _stadium_index(modell_n[e["schl_nr"]], e["neu"])
        abw[(e["schl_nr"], f"stadium_{n}")] = True
    return abw


def _stadium_index(stadien, text) -> int:
    for z in stadien:
        if _stadium_text(z) == text:
            return int(z["stadium"])
    return len(stadien)


def _felder_des_eintrags(strassen, namen, schl_nr, nur_kopf=False) -> list:
    felder = list(KOPFFELDER)
    if not nur_kopf:
        for z in namen.get(schl_nr, []):
            felder += [f"stadium_{z['stadium']}_datum", f"stadium_{z['stadium']}_name"]
    return felder


def baue_pruefliste(parser, modelle: dict):
    """parser = (strassen, namen) des Parsers; modelle = Kurzname -> {"antworten": {buchseite: antwort}}.
    Liefert (zeilen, kennzahlen). Verglichen werden nur Buchseiten, die das jeweilige Modell
    gelesen hat; unlesbare Seiten zählen als nicht gelesen."""
    p_s, p_n = als_struktur(*parser)
    seite_je_schl = {schl: int(z["buchseite"]) for schl, z in p_s.items()}
    daten, kennzahlen, gelesen = {}, {}, {}
    abweichungen = {}

    for kurz, m in modelle.items():
        strassen, namen, probleme = [], [], []
        gelesen[kurz] = set()
        unlesbar = 0
        for buchseite, antwort in m["antworten"].items():
            if antwort.get("fehler") == "unlesbar" or antwort.get("eintraege") is None:
                unlesbar += 1
                continue
            gelesen[kurz].add(int(buchseite))
            s, n, pr = normalisiere_antwort(antwort)
            strassen += s; namen += n; probleme += pr
        m_s, m_n = als_struktur(strassen, namen)
        daten[kurz] = (m_s, m_n)
        # Parser-Ausschnitt: nur gelesene Seiten; Modellketten unvollständiger Einträge ausblenden
        p_s_teil = {schl: z for schl, z in p_s.items() if seite_je_schl[schl] in gelesen[kurz]}
        p_n_teil = {schl: p_n.get(schl, []) for schl in p_s_teil}
        unvollst = {schl for schl, z in m_s.items() if ist_unvollstaendig(z)}
        m_n_vgl = {schl: ([] if schl in unvollst else st) for schl, st in m_n.items()}
        p_n_vgl = {schl: ([] if schl in unvollst else st) for schl, st in p_n_teil.items()}
        abweichungen[kurz] = _abweichungen(p_s_teil, p_n_vgl, m_s, m_n_vgl)

        ueber = defaultdict(lambda: defaultdict(lambda: {"verglichen": 0, "gleich": 0}))
        for schl, z in p_s_teil.items():
            if schl not in m_s:
                continue
            for feld in _felder_des_eintrags(p_s_teil, p_n_teil, schl, nur_kopf=schl in unvollst):
                typ = re.sub(r"^stadium_\d+_", "stadium_", feld)
                e = ueber[z["status"]][typ]
                e["verglichen"] += 1
                e["gleich"] += (schl, feld) not in abweichungen[kurz]
        kennzahlen[kurz] = {
            "seiten_gelesen": len(gelesen[kurz]), "seiten_unlesbar": unlesbar,
            "eintraege_modell": len(m_s),
            "eintraege_fehlend": sum(1 for schl in p_s_teil if schl not in m_s),
            "eintraege_nur_modell": sum(1 for schl in m_s if schl not in p_s),
            "datum_nicht_normalisierbar": len(probleme),
            "uebereinstimmung": {st: dict(f) for st, f in ueber.items()},
        }

    zeilen = []
    alle = set().union(*abweichungen.values()) if abweichungen else set()
    for schl, feld in alle:
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
                continue
            werte[kurz] = feldwert(*daten[kurz], schl, feld) or ""
            zeile[f"wert_{kurz}"] = werte[kurz]
        for kurz in KURZNAMEN:
            zeile.setdefault(f"wert_{kurz}", "")
        if not lesbar:
            zeile["einig"] = "unlesbar"
        elif len(set(werte.values())) == 1 and werte[KURZNAMEN[0]] != zeile["wert_parser"]:
            zeile["einig"] = "beide"
        else:
            zeile["einig"] = "eines"
        zeilen.append(zeile)
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
         "Spec 2026-09-12); Abweichungen stehen in `daten/pruefung_llm.csv` zur manuellen Prüfung.\n"]
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
```

- [ ] **Step 4: Tests grün** — bei Abweichungen zwischen Testerwartung und Implementierung gilt die Spec (Abschnitt 3.3); Testerwartungen nur anpassen, wenn sie der Spec widersprechen, und das im Report benennen.

- [ ] **Step 5: Commit**

```bash
git add strassen/llm_vergleich.py tests/test_llm_vergleich.py
git commit -m "llm_vergleich: Prüfliste je abweichendem Feld, Vollständigkeitsabgleich, Kennzahlen

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Vergleich — Goldstandard-Messung, `uebernehmen`, CLI

**Files:**
- Modify: `strassen/llm_vergleich.py` (Teil 3)
- Test: `tests/test_llm_vergleich.py` (ergänzen)

**Interfaces:**
- Produces: `messe_goldstandard(stichprobe: list, modell: tuple) -> dict` (Statistik wie `goldstandard.berechne_statistik`: `je_feldtyp`, `je_status`, `gesamt`, `fehler`, `fehlend_gefunden`, `fehlend_gesamt`), `formatiere_ergebnis_llm_md(statistiken: dict[str, dict]) -> str`, `uebernehmen(pruefliste: list, korrekturen_vorhanden: list, datum: str) -> list` (neue Korrekturzeilen), CLI-Unterbefehle `pruefliste`, `goldstandard`, `uebernehmen`.
- Konsumiert `korrekturen.FELDER_KORREKTUREN` (Task 8) — deshalb importiert `uebernehmen` erst zur Laufzeit; im Test wird die Feldliste hier definiert: `["schl_nr", "feld", "wert_alt", "wert_neu", "beleg", "quelle", "datum"]`.

- [ ] **Step 1: Failing tests (anhängen)**

```python
def _stichprobe():
    basis = {"lemma": "Aachener Straße", "status": "automatisch", "buchseite": "23"}
    return [
        {**basis, "schl_nr": "00001", "feld": "lemma", "wert": "Aachener Straße", "korrekt": "ja", "korrektur": ""},
        {**basis, "schl_nr": "00001", "feld": "stadium_2_datum", "wert": "1902-05-16", "korrekt": "ja", "korrektur": ""},
        {**basis, "schl_nr": "00001", "feld": "stadtteile", "wert": "Frohnhausn", "korrekt": "nein", "korrektur": "Frohnhausen"},
        {**basis, "schl_nr": "00001", "feld": "stadium_3_name", "wert": "", "korrekt": "nein", "korrektur": "Neuer Name"},   # nachgetragen
        {**basis, "schl_nr": "00001", "feld": "verweis_auf", "wert": "", "korrekt": "", "korrektur": ""},                   # ungeprüft
    ]


def test_messe_goldstandard_zaehlt_treffer_gegen_soll():
    s, n, _ = lv.normalisiere_antwort(_antwort())
    st = lv.messe_goldstandard(_stichprobe(), lv.als_struktur(s, n))
    assert st["gesamt"] == {"geprueft": 4, "korrekt": 3, "fehlerquote": 25.0}
    assert st["je_feldtyp"]["stadium_datum"]["korrekt"] == 1
    assert st["fehlend_gesamt"] == 1 and st["fehlend_gefunden"] == 0
    assert st["fehler"] == [{"schl_nr": "00001", "lemma": "Aachener Straße", "status": "automatisch",
                             "feld": "stadium_3_name", "soll": "Neuer Name", "ist": None}]


def test_formatiere_ergebnis_llm_md_je_modell():
    s, n, _ = lv.normalisiere_antwort(_antwort())
    st = lv.messe_goldstandard(_stichprobe(), lv.als_struktur(s, n))
    md = lv.formatiere_ergebnis_llm_md({"qwen": st})
    assert "## Modell `qwen`" in md and "25,0 %" in md.replace(".", ",") or "25.0" in md


def test_uebernehmen_erzeugt_korrekturzeilen_und_ueberspringt_dubletten():
    pruefliste = [
        {"schl_nr": "00001", "feld": "lemma", "wert_parser": "Aachener Straße", "korrektur": "Aachenerstraße", "beleg": "Aachenerstraße"},
        {"schl_nr": "00001", "feld": "stadium_2_datum", "wert_parser": "1902-05-16", "korrektur": "", "beleg": ""},
        {"schl_nr": "00002", "feld": "stadium_2", "wert_parser": "", "korrektur": "1930 | Neuer Name", "beleg": "1930: Neuer Name"},
    ]
    vorhanden = [{"schl_nr": "00001", "feld": "lemma", "wert_alt": "Aachener Straße", "wert_neu": "Aachenerstraße",
                  "beleg": "", "quelle": "llm-lauf", "datum": "2026-09-01"}]
    neu = lv.uebernehmen(pruefliste, vorhanden, datum="2026-09-13")
    assert neu == [
        {"schl_nr": "00002", "feld": "stadium_2_datum", "wert_alt": "", "wert_neu": "1930", "beleg": "1930: Neuer Name", "quelle": "llm-lauf", "datum": "2026-09-13"},
        {"schl_nr": "00002", "feld": "stadium_2_name", "wert_alt": "", "wert_neu": "Neuer Name", "beleg": "1930: Neuer Name", "quelle": "llm-lauf", "datum": "2026-09-13"},
    ]


def test_uebernehmen_lehnt_korrektur_fuer_fehlenden_parser_eintrag_ab():
    with pytest.raises(ValueError):
        lv.uebernehmen([{"schl_nr": "00003", "feld": "eintrag", "wert_parser": "", "korrektur": "Achenbachstraße", "beleg": ""}], [], "2026-09-13")
```

- [ ] **Step 2: Run, expect AttributeError**

- [ ] **Step 3: Implementierung (Teil 3, anhängen)**

```python
FELDER_KORREKTUREN = ["schl_nr", "feld", "wert_alt", "wert_neu", "beleg", "quelle", "datum"]
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
```

CLI (anhängen):

```python
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
```

- [ ] **Step 4: Tests grün; Commit**

```bash
git add strassen/llm_vergleich.py tests/test_llm_vergleich.py
git commit -m "llm_vergleich: Goldstandard-Messung je Modell, Übernahme geprüfter Korrekturen, CLI

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 8: Korrektur-Overlay (`strassen/korrekturen.py`) und Anwendung im Parser

**Files:**
- Create: `strassen/korrekturen.py`
- Modify: `strassen/erschliessen.py:197` (Signatur `main`) und vor `schreibe_strassen` (ca. Zeile 294)
- Test: `tests/test_korrekturen.py`, `tests/test_erschliessen.py` (ein Integrationstest)

**Interfaces:**
- Produces: `FELDER_KORREKTUREN`, `KORREKTUREN_PFAD = WURZEL/"daten"/"korrekturen.csv"`, `STATUS_GEPRUEFT = "geprueft"`, `class KorrekturFehler(ValueError)`, `lade_korrekturen(pfad) -> list` (leer, wenn Datei fehlt), `wende_an(strassen: list, namen: list, korrekturen: list) -> dict` — mutiert `strassen`-Zeilen und ersetzt den Inhalt von `namen` in place (`namen[:] = …`), Protokoll `{"eintraege": n, "korrekturen": m}`.
- `erschliessen.main(ocr_dir, ausgabe_dir, korrekturen_pfad="")`: leer → keine Korrekturen (Standard, damit die bestehenden Mini-Tests und der Regressionstest den reinen Parser messen); der `__main__`-Block ruft `main(korrekturen_pfad=KORREKTUREN_PFAD)` auf, so dass der normale Lauf `python3 -m strassen.erschliessen` das Overlay anwendet. Kennzahl `korrigiert`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_korrekturen.py
import pytest

from strassen import korrekturen as ko


def _daten():
    strassen = [{"schl_nr": "00001", "lemma": "Aachener Straße", "stadtteile": "Frohnhausn", "strassenklasse": "Gemeindestraße",
                 "namensgruppe": "Stadt und Ort", "verweis_auf": "", "buchseite": 23, "status": "unsicher"},
                {"schl_nr": "00002", "lemma": "Abteistraße", "stadtteile": "Werden", "strassenklasse": "Bundesstraße",
                 "namensgruppe": "Lagebezeichnung", "verweis_auf": "", "buchseite": 23, "status": "automatisch"}]
    namen = [{"schl_nr": "00001", "stadium": 1, "gueltig_ab": "1898", "datum_praezision": "vor", "name": "Victoriastraße (tlw.)", "ist_urspruenglich": "falsch"},
             {"schl_nr": "00001", "stadium": 2, "gueltig_ab": "1902-05-16", "datum_praezision": "tag", "name": "Aachener Straße", "ist_urspruenglich": "falsch"},
             {"schl_nr": "00002", "stadium": 1, "gueltig_ab": "1501", "datum_praezision": "jahrhundert", "name": "Abteistraße", "ist_urspruenglich": "wahr"}]
    return strassen, namen


def _k(schl, feld, alt, neu, **rest):
    return {"schl_nr": schl, "feld": feld, "wert_alt": alt, "wert_neu": neu, "beleg": rest.get("beleg", "x"),
            "quelle": rest.get("quelle", "goldstandard"), "datum": "2026-09-12"}


def test_kopffeld_korrigieren_setzt_status_geprueft():
    s, n = _daten()
    prot = ko.wende_an(s, n, [_k("00001", "stadtteile", "Frohnhausn", "Frohnhausen")])
    assert s[0]["stadtteile"] == "Frohnhausen" and s[0]["status"] == "geprueft"
    assert s[1]["status"] == "automatisch"
    assert prot == {"eintraege": 1, "korrekturen": 1}


def test_wert_alt_muss_zum_parser_passen():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00001.*stadtteile"):
        ko.wende_an(s, n, [_k("00001", "stadtteile", "Frohnhausen", "Holsterhausen")])


def test_unbekannte_schl_nr_bricht_ab():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="00099"):
        ko.wende_an(s, n, [_k("00099", "lemma", "A", "B")])


def test_stadium_datum_und_name_aendern():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "16.05.1920"),
                       _k("00001", "stadium_2_name", "Aachener Straße", "Aachener Str.")])
    st = [z for z in n if z["schl_nr"] == "00001"]
    assert (st[1]["gueltig_ab"], st[1]["datum_praezision"], st[1]["name"]) == ("1920-05-16", "tag", "Aachener Str.")


def test_stadium_datum_wert_alt_in_stichprobenform():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler):
        ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "1898", "vor 1897")])   # ist 'vor 1898'
    ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "vor 1898", "vor 1897")])
    assert n[0]["gueltig_ab"] == "1897" and n[0]["datum_praezision"] == "vor"


def test_stadium_nachtragen_rueckt_folgende_auf():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "", "1900"), _k("00001", "stadium_2_name", "", "Zwischenname")])
    st = [(z["stadium"], z["gueltig_ab"], z["name"]) for z in n if z["schl_nr"] == "00001"]
    assert st == [(1, "1898", "Victoriastraße (tlw.)"), (2, "1900", "Zwischenname"), (3, "1902-05-16", "Aachener Straße")]


def test_stadium_nachtragen_braucht_datum_und_name():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="stadium_2"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_name", "", "Nur Name")])


def test_stadium_streichen_nummeriert_neu():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_1_datum", "vor 1898", ""), _k("00001", "stadium_1_name", "Victoriastraße (tlw.)", "")])
    st = [(z["stadium"], z["name"]) for z in n if z["schl_nr"] == "00001"]
    assert st == [(1, "Aachener Straße")]


def test_urspruenglich_aendern():
    s, n = _daten()
    ko.wende_an(s, n, [_k("00001", "stadium_1_urspruenglich", "falsch", "wahr")])
    assert n[0]["ist_urspruenglich"] == "wahr"


def test_bestaetigung_setzt_nur_status():
    s, n = _daten()
    prot = ko.wende_an(s, n, [_k("00001", "eintrag", "", "")])
    assert s[0]["status"] == "geprueft" and s[0]["stadtteile"] == "Frohnhausn"
    assert prot == {"eintraege": 1, "korrekturen": 1}


def test_bestaetigung_mit_werten_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler):
        ko.wende_an(s, n, [_k("00001", "eintrag", "", "x")])


def test_nicht_normalisierbares_datum_ist_fehler():
    s, n = _daten()
    with pytest.raises(ko.KorrekturFehler, match="normalisierbar"):
        ko.wende_an(s, n, [_k("00001", "stadium_2_datum", "1902-05-16", "Frühjahr 1902")])


def test_dublette_der_schl_nr_ist_mehrdeutig():
    s, n = _daten()
    s.append(dict(s[0]))
    with pytest.raises(ko.KorrekturFehler, match="mehrdeutig"):
        ko.wende_an(s, n, [_k("00001", "lemma", "Aachener Straße", "X")])


def test_lade_korrekturen_fehlende_datei_leer(tmp_path):
    assert ko.lade_korrekturen(tmp_path / "gibt_es_nicht.csv") == []
```

Integrationstest in `tests/test_erschliessen.py` (anhängen; die Datei hat bereits Fixtures, die `main` auf einem Mini-OCR-Verzeichnis laufen lassen — die vorhandene Helferfunktion wiederverwenden, die eine Seite `s023.txt` mit einem Eintrag schreibt; falls keine passende existiert, eine anlegen mit einem realen kurzen OCR-Ausschnitt aus einem bestehenden Test derselben Datei):

```python
def test_main_wendet_korrekturen_an_und_zaehlt(tmp_path, ...):
    # Mini-OCR mit einem Eintrag schl_nr X (Fixture der Datei) -> main ohne Korrekturen, schl_nr und lemma auslesen
    # korrekturen.csv mit einer Bestätigungszeile (feld=eintrag) schreiben
    # main(..., korrekturen_pfad=str(korr)) -> strassen.csv: status == "geprueft"; kennzahlen["korrigiert"] == 1
    # main(..., korrekturen_pfad="") -> status unverändert
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: `strassen/korrekturen.py`**

```python
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

from strassen.datum import lese_text
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
        return list(csv.DictReader(f))


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
        st = [z for i, z in enumerate(st, 1) if i not in streichen]
        for n in sorted(nachtrag):
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
```

Hinweis für den Test „nachtragen rückt auf": `st.insert(n-1, …)` nach dem Streichen; die Stadien-Nummern werden anschließend neu vergeben.

- [ ] **Step 4: Anwendung in `erschliessen.main`**

Signatur: `def main(ocr_dir="ocr/seiten", ausgabe_dir="daten", korrekturen_pfad=""):`. Import `from strassen.korrekturen import KORREKTUREN_PFAD, lade_korrekturen, wende_an`. Nach dem Dubletten-Block, vor `schreibe_strassen`:

```python
    # Korrektur-Overlay (Spec 2026-09-12, 3.4): manuell geprüfte Korrekturen, status=geprueft.
    # Leerer Pfad -> keine Korrekturen (Standard für Tests und Regressionsmessung des
    # reinen Parsers); der Skriptaufruf unten übergibt die Standarddatei.
    protokoll = wende_an(strassen, namen, lade_korrekturen(korrekturen_pfad) if korrekturen_pfad else [])
```

Kennzahlen: `"korrigiert": protokoll["eintraege"]`. Im `__main__`-Block: `kennzahlen = main(korrekturen_pfad=KORREKTUREN_PFAD)`.

- [ ] **Step 5: Tests grün (auch `test_goldstandard_regression`, wenn `ocr/seiten/` vorliegt); Commit**

```bash
git add strassen/korrekturen.py strassen/erschliessen.py tests/test_korrekturen.py tests/test_erschliessen.py
git commit -m "korrekturen.py: Korrektur-Overlay mit status=geprueft, angewandt in erschliessen.main

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 9: `geprueft` in der Veröffentlichung gleichrangig

**Files:**
- Modify: `strassen/veroeffentlichen.py:11, 117, 165, 172, 210-236`
- Test: `tests/test_veroeffentlichen.py:59` (umbenennen/erweitern)

**Interfaces:**
- `veroeffentlichen.STATUS_BELASTBAR = ("automatisch", "geprueft")`; Variable `strassen_automatisch` → `strassen_belastbar`; Kennzahl `strassen_automatisch` → `strassen_belastbar` plus `strassen_geprueft`.

- [ ] **Step 1: Failing test** — den bestehenden Test `test_konkordanz_nutzt_nur_status_automatisch` umbenennen in `test_konkordanz_nutzt_automatisch_und_geprueft` und um einen Eintrag mit `status=geprueft` erweitern, der in der Konkordanz erscheinen muss, während `unsicher` weiterhin fehlt. Kennzahl-Assertion `strassen_belastbar`.

- [ ] **Step 2: Run, expect Fehler**

- [ ] **Step 3: Implementieren** — Filter, Variablennamen, Texte in `_schreibe_erhebungsstand` („`status=automatisch` oder `geprueft`"), Modul-Docstring Zeile 11.

- [ ] **Step 4: Tests grün; Commit**

```bash
git add strassen/veroeffentlichen.py tests/test_veroeffentlichen.py
git commit -m "veroeffentlichen: status=geprueft gleichrangig mit automatisch (Konkordanz, Erhebungsstand, Kennzahlen)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 10: Schema und Dokumentation

**Files:**
- Modify: `datapackage.json` (Ressource `korrekturen`; `status`-Beschreibung)
- Modify: `README.md` (Methode, Data Dictionary `korrekturen.csv`, Bezifferte Qualität → „Unabhängige LLM-Lesung", Abhängigkeiten, Publikationsumfang)
- Modify: `docs/goldstandard/ANLEITUNG.md` (Abschnitt „Korrekturen in den Datensatz bringen")
- Create: `daten/korrekturen.csv` (nur Kopfzeile)
- Test: `tests/test_datapackage.py` (ergänzen)

- [ ] **Step 1: Failing tests**

```python
def test_datapackage_hat_korrekturen_ressource_mit_feldern():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    r = next(r for r in paket["resources"] if r["name"] == "korrekturen")
    assert r["path"] == "daten/korrekturen.csv"
    assert [f["name"] for f in r["schema"]["fields"]] == ["schl_nr", "feld", "wert_alt", "wert_neu", "beleg", "quelle", "datum"]


def test_status_beschreibung_nennt_alle_drei_werte():
    paket = json.loads(Path("datapackage.json").read_text(encoding="utf-8"))
    strassen = next(r for r in paket["resources"] if r["name"] == "strassen")
    feld = next(f for f in strassen["schema"]["fields"] if f["name"] == "status")
    assert feld["constraints"]["enum"] == ["automatisch", "geprueft", "unsicher"]
    assert "geprueft" in feld.get("description", "") and "Overlay" in feld["description"]


def test_korrekturen_csv_hat_kopfzeile():
    kopf = Path("daten/korrekturen.csv").read_text(encoding="utf-8").splitlines()[0]
    assert kopf == "schl_nr,feld,wert_alt,wert_neu,beleg,quelle,datum"
```

- [ ] **Step 2: Run, expect Fehler**

- [ ] **Step 3: `datapackage.json`**

`status`-Feld: `"description": "automatisch = Parser ohne Prüfgrund; unsicher = Parser mit Prüfgrund (Wert übernommen, gekennzeichnet); geprueft = Eintrag vollständig gegen den Scan geprüft, Korrekturen über das Overlay daten/korrekturen.csv angewandt (höchste Stufe)"`. Neue Ressource:

```json
{
  "name": "korrekturen",
  "path": "daten/korrekturen.csv",
  "format": "csv",
  "encoding": "utf-8",
  "description": "Manuell gegen den Scan geprüfte Korrekturen, die erschliessen.main als letzten Schritt auf die Parser-Ausgabe anwendet; betroffene Einträge erhalten status=geprueft.",
  "schema": {
    "fields": [
      {"name": "schl_nr", "type": "string", "description": "Fremdschlüssel auf strassen.csv"},
      {"name": "feld", "type": "string", "description": "lemma | stadtteile | strassenklasse | namensgruppe | verweis_auf | stadium_N_datum | stadium_N_name | stadium_N_urspruenglich | eintrag (Bestätigung ohne Wertänderung)"},
      {"name": "wert_alt", "type": "string", "description": "Parser-Wert zum Prüfzeitpunkt (Datum in Stichprobenform, z. B. 'vor 1898'); leer = Stadium nachtragen. Weicht er beim Anwenden ab, bricht der Lauf ab."},
      {"name": "wert_neu", "type": "string", "description": "korrigierter Wert; bei Daten der gedruckte Text ('29.08.1927'); leer bei beiden Feldern eines Stadiums = streichen"},
      {"name": "beleg", "type": "string", "description": "gedruckter Wortlaut der Stelle, ≤ 200 Zeichen"},
      {"name": "quelle", "type": "string", "constraints": {"enum": ["goldstandard", "llm-lauf"]}},
      {"name": "datum", "type": "date", "description": "Tag der Prüfung"}
    ]
  }
}
```

- [ ] **Step 4: README**

- „Methode": Absatz „Stufe 5 — Unabhängige LLM-Lesung und Korrektur-Overlay": zwei Modelle lesen die Seitenbilder unabhängig (kein OCR-Text), Abweichungen → `daten/pruefung_llm.csv`, Mensch prüft, Korrekturen → `daten/korrekturen.csv` → `status=geprueft`. Modelle ändern den Status nicht (Option A); ein späterer Schwenk würde hier ausgewiesen.
- Data Dictionary: Tabelle zu `daten/korrekturen.csv` (Felder wie oben) und Zeile zu `status` mit drei Bedeutungen.
- „Bezifferte Qualität": Unterabschnitt „Unabhängige LLM-Lesung" mit Verweis auf `docs/llm_lesung.md` und `docs/goldstandard/ergebnis_llm.md` (Zahlen werden in Task 12 eingetragen; hier Platzhaltersatz „Zahlen: siehe verlinkte Dateien").
- „Abhängigkeiten": optional Zugang zu einem OpenAI-kompatiblen Inferenzendpunkt (`LLM_BASE_URL`, `LLM_API_KEY`), nur für die Neuerstellung der Prüfliste.
- „Publikationsumfang": `daten/korrekturen.csv` und `daten/pruefung_llm.csv` gehören dazu (nur Kopffeld-/Namensinhalte); `llm/` (Seitenbilder, Rohantworten) und `.env` nicht.

- [ ] **Step 5: `ANLEITUNG.md`** — neuer Abschnitt „Korrekturen in den Datensatz bringen": Spalten von `korrekturen.csv`, Konvention „ganzer Eintrag", Datumsform, Nachtragen/Streichen/Bestätigen, `python3 -m strassen.erschliessen` neu laufen lassen, Abbruch bei abweichendem `wert_alt`. Für die LLM-Prüfliste: `korrektur`/`beleg` ausfüllen, dann `python3 -m strassen.llm_vergleich uebernehmen`.

- [ ] **Step 6: `daten/korrekturen.csv`** nur Kopfzeile. Tests grün; Commit**

```bash
git add datapackage.json README.md docs/goldstandard/ANLEITUNG.md daten/korrekturen.csv tests/test_datapackage.py
git commit -m "Schema und Doku: korrekturen.csv als Ressource, status-Stufen, LLM-Lesung im README

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 11: Kalibrierung an Entwicklungsseiten (lokal, braucht API-Zugang)

**Files:**
- Create: `docs/llm_kalibrierung.md`
- Modify (nur wenn nötig): `strassen/llm_prompt.md`, `strassen/llm_leser.py` (JSON-Extraktion), `strassen/llm_vergleich.py` (Normalisierung)
- Tests: bei jeder Code-Änderung ein Test mit der beobachteten Antwortform (gekürzt auf Kopf/Kette, kein Erläuterungstext) in `tests/test_llm_leser.py` bzw. `tests/test_llm_vergleich.py`

**Entwicklungsseiten (keine enthält einen Goldstandard-Eintrag; Goldstandard-Seiten: 23, 34, 39, 41, 65, 67, 80, 84, 87, 88, 91, 118, 120, 121, 127, 138, 161, 173, 179, 187, 188, 190, 200, 203, 204, 211, 214, 224, 229, 243, 252, 254, 265, 267, 268, 273, 276, 277, 291, 298, 303, 306, 309, 320, 342, 344, 353):** Band 1: **30, 60, 100, 150**; Band 2: **220, 260, 300, 340**.

- [ ] **Step 1: `.env` anlegen** (lokal, gitignored) mit `LLM_BASE_URL` und `LLM_API_KEY` — Werte vom Nutzer; falls `.env` fehlt, Task mit `NEEDS_CONTEXT` melden.

- [ ] **Step 2: Seiten rendern**

```bash
python3 -m strassen.seiten --seiten 30,60,100,150,220,260,300,340
```

- [ ] **Step 3: Beide Modelle lesen lassen**

```bash
python3 -m strassen.llm_leser --modell inferenz-qwen3-8-27b --seiten 30,60,100,150,220,260,300,340
python3 -m strassen.llm_leser --modell inferenz-mistral-small-4-119b --seiten 30,60,100,150,220,260,300,340
```

- [ ] **Step 4: Prüfliste nur für diese Seiten**

```bash
python3 -m strassen.llm_vergleich pruefliste --kennzahlen /tmp/kalibrierung_kennzahlen.md
```

(Die Prüfliste umfasst automatisch nur gelesene Seiten.) `daten/pruefung_llm.csv` danach **nicht committen** — Kalibrierungsstand: `git checkout -- daten/pruefung_llm.csv` bzw. Datei löschen, sie entsteht in Task 12 neu.

- [ ] **Step 5: Sichten** — jede Abweichung mit `einig=beide` gegen das Seitenbild `llm/seiten/sNNN.png` prüfen (Read-Tool auf das PNG). Drei Fragen: (a) liegt der Parser falsch (→ Kandidat für `korrekturen.csv`, hier nur notieren), (b) liegt das Modell falsch (→ Prompt-Schwäche? nur ändern, wenn systematisch), (c) Formproblem (Datum nicht normalisierbar, `schl_nr`-Form, Listen als String) → Normalisierung anpassen. Unlesbare Seiten: Rohtext lesen, JSON-Extraktion anpassen.

- [ ] **Step 6: Iterieren** — Prompt/Extraktion ändern, `--neu` für die acht Seiten, wieder Step 4/5. Höchstens drei Runden; jede Prompt-Änderung mit Begründung in `docs/llm_kalibrierung.md` festhalten (Seite, Beobachtung, Änderung, Wirkung). Kein Blick auf Goldstandard-Seiten.

- [ ] **Step 7: `docs/llm_kalibrierung.md`** schreiben: Entwicklungsseiten, Runden, Endstand des Prompts (Hash), Kennzahlen der acht Seiten je Modell (aus Step 4), bekannte Modellschwächen. Keine Transkriptionen zitieren (nur Kopffeld-/Namensbeispiele).

- [ ] **Step 8: Commit** (Prompt, Code, Tests, Kalibrierungsnotiz — keine `llm/`-Dateien)

```bash
git add strassen/llm_prompt.md strassen/llm_leser.py strassen/llm_vergleich.py tests/ docs/llm_kalibrierung.md
git commit -m "LLM-Lesung kalibriert an 8 Entwicklungsseiten (Prompt-Stand <hash>)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 12: Goldstandard-Messung, Volllauf, erste Korrekturen, Regeneration

**Files:**
- Create: `docs/goldstandard/ergebnis_llm.md`, `docs/llm_lesung.md`, `daten/pruefung_llm.csv`
- Modify: `daten/korrekturen.csv` (3 Goldstandard-Korrekturen), `daten/*.csv` (Regeneration), `docs/qualitaet.md`, `docs/erhebungsstand.md`, `README.md` (Zahlen), Memory-Note des Nutzers wird vom Controller aktualisiert, nicht vom Subagenten.

- [ ] **Step 1: Goldstandard-Seiten lesen lassen** (47 Seiten, Liste in Task 11) mit beiden Modellen, Prompt unverändert:

```bash
python3 -m strassen.seiten --seiten 23,34,39,41,65,67,80,84,87,88,91,118,120,121,127,138,161,173,179,187,188,190,200,203,204,211,214,224,229,243,252,254,265,267,268,273,276,277,291,298,303,306,309,320,342,344,353
python3 -m strassen.llm_leser --modell inferenz-qwen3-8-27b --seiten <dieselbe Liste>
python3 -m strassen.llm_leser --modell inferenz-mistral-small-4-119b --seiten <dieselbe Liste>
python3 -m strassen.llm_vergleich goldstandard
```

Ergebnis `docs/goldstandard/ergebnis_llm.md` committen. **Der Prompt wird danach nicht mehr geändert.** Falls die Messung ein Formproblem zeigt (nicht normalisierbare Daten in einer Form, die die Entwicklungsseiten nicht hatten), darf die Normalisierung in `llm_vergleich` angepasst werden — das ist Auswertung, nicht Lesung — und wird in `ergebnis_llm.md` vermerkt.

- [ ] **Step 2: Volllauf**

```bash
python3 -m strassen.seiten
python3 -m strassen.llm_leser --modell inferenz-qwen3-8-27b
python3 -m strassen.llm_leser --modell inferenz-mistral-small-4-119b
python3 -m strassen.llm_vergleich pruefliste
```

Bei `LaufAbbruch` (429/5xx) den Befehl wiederholen; er holt fehlende Seiten nach. Unlesbare Seiten einmal mit `--neu --seiten <liste>` nachfassen.

- [ ] **Step 3: Die drei offenen Goldstandard-Korrekturen ermitteln** und nach `daten/korrekturen.csv` eintragen (`quelle=goldstandard`, `datum` = heutiges Datum, `beleg` = Wortlaut aus `stichprobe.csv`-Spalte `korrektur`):

```bash
python3 - <<'EOF'
import csv, tempfile, pathlib
from collections import defaultdict
from strassen.erschliessen import main
aus = pathlib.Path(tempfile.mkdtemp())
main(ocr_dir="ocr/seiten", ausgabe_dir=str(aus), korrekturen_pfad="")
s = {z["schl_nr"]: z for z in csv.DictReader(open(aus/"strassen.csv", encoding="utf-8"))}
n = defaultdict(dict)
for z in csv.DictReader(open(aus/"namen.csv", encoding="utf-8")): n[z["schl_nr"]][int(z["stadium"])] = z
from strassen.goldstandard import formatiere_datum
for z in csv.DictReader(open("docs/goldstandard/stichprobe.csv", encoding="utf-8")):
    if z["korrekt"].strip().lower() != "nein": continue
    f = z["feld"]
    if f.startswith("stadium_"):
        _, k, art = f.split("_"); st = n[z["schl_nr"]].get(int(k))
        ist = None if st is None else (formatiere_datum(st["datum_praezision"], st["gueltig_ab"]) if art == "datum" else st["name"])
    else:
        ist = s[z["schl_nr"]][f]
    if ist != z["korrektur"]:
        print(z["schl_nr"], f, repr(ist), "->", repr(z["korrektur"]), "status", s[z["schl_nr"]]["status"])
EOF
```

Für jede Ausgabezeile eine Korrekturzeile: `wert_alt` = `ist` (leer bei `None` → Nachtrag, dann datum UND name eintragen), `wert_neu` = `korrektur` (bei Datumsfeldern den gedruckten Text; `stichprobe.csv` hat Datensatzform `1927-08-29` → als `29.08.1927` eintragen). Zu jedem korrigierten Eintrag gilt die Konvention „ganzer Eintrag geprüft" — die Stichprobe hat genau das getan.

- [ ] **Step 4: Regeneration**

```bash
python3 -m strassen.erschliessen
python3 -m strassen.veroeffentlichen
python3 -m pytest -q
```

Erwartung: `test_goldstandard_regression` weiterhin grün (es misst den reinen Parser ohne Overlay, weiterhin 14 von 17). Zusätzlich prüfen, dass `daten/strassen.csv` für die drei korrigierten Einträge `status=geprueft` trägt und die Korrekturwerte enthält. Kennzahlen notieren (`strassen_geprueft`, unsicher-Zahl).

- [ ] **Step 5: README-Zahlen** — Data Dictionary (Zeilenzahlen), „Bezifferte Qualität → Unabhängige LLM-Lesung": Fehlerquote je Modell aus `ergebnis_llm.md`, Seiten gelesen/unlesbar, Anzahl Prüfzeilen nach `einig`, Anzahl `geprueft`. Satz: „Die Modelle verändern den Status nicht; alle `geprueft`-Einträge gehen auf manuelle Prüfung zurück."

- [ ] **Step 6: Commit**

```bash
git add daten/ docs/ README.md
git commit -m "LLM-Lesung: Goldstandard-Messung, Volllauf beider Modelle, Prüfliste; erste Korrekturen (Goldstandard) angewandt

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

## Selbstprüfung (durchgeführt beim Schreiben)

- **Spec-Abdeckung:** 3.1 → Task 1; 3.2 → Tasks 2–3, 11; 3.3 → Tasks 5–7, 12; 3.4 → Task 8; `geprueft` in Veröffentlichung → Task 9; 3.5 → Task 10; 4 (Kalibrierung, Messung, Volllauf) → Tasks 11–12; 5 (Tests) → in jedem Task; 6 (Nicht-Ziele) → keine Extraktion der Erläuterungstexte (Prompt Regel 4), kein Statuswechsel durch Modelle (`STATUS_MODELL` nie in Datensatz geschrieben), `llm/` gitignored (Task 1).
- **Typkonsistenz:** `feldwert(strassen: dict, namen: dict, schl_nr, feld)` in Tasks 6 und 7; `als_struktur` aus Task 4 in 6/7; `lese_text` aus Task 4 in 5/8; `FELDER_KORREKTUREN` identisch in Task 7 und 8; `formatiere_datum` (bestehend) liefert die Stichprobenform für `wert_alt` (Task 8) und `wert_parser`/`wert_modell` (Task 6); Antwortdatei-Form aus Task 3 = Fixture in Task 5.
- **Platzhalter:** README-Zahlen in Task 10 sind bewusst „siehe verlinkte Dateien" und werden in Task 12 gesetzt.
