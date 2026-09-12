"""Unabhängige LLM-Lesung: je Buchseite das Seitenbild an ein bildfähiges Modell
schicken und die Antwort als JSON sichern (Spec 2026-09-12, Abschnitt 3.2).

Das Modell sieht NUR das Bild — keinen OCR-Text, keine Parser-Werte. Rohantworten
liegen gitignored unter llm/antworten/<modell>/sNNN.json; ein Wiederholungslauf
überspringt vorhandene Antworten, sofern sie aus demselben Prompt-Stand stammen
(prompt_hash).

  python3 -m strassen.llm_leser --modell inferenz-qwen3-8-27b [--seiten 23-30] [--neu]

Konfiguration über Umgebungsvariablen LLM_BASE_URL (OpenAI-kompatibler Endpunkt, mit
oder ohne '/chat/completions') sowie je Modell LLM_API_KEY_QWEN bzw. LLM_API_KEY_MISTRAL,
mit LLM_API_KEY als Rückfall, falls kein modellspezifischer Schlüssel gesetzt ist; eine
.env in der Repo-Wurzel wird gelesen, gesetzte Umgebungsvariablen haben Vorrang.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import sys
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


_CHAT_COMPLETIONS = re.compile(r"/chat/completions/?$")


def konfiguration(modell: str = "") -> tuple:
    """Liest base_url/api_key aus der Umgebung. base_url wird um ein trailing '/' und
    ein optionales trailing '/chat/completions' gekappt, weil sende() das selbst anhängt.
    Der API-Key ist normalerweise modellspezifisch (der Inferenzserver nutzt eine
    base_url für alle Modelle, aber je Modell einen eigenen Key): LLM_API_KEY_<KURZ>
    (z. B. LLM_API_KEY_QWEN) hat Vorrang vor dem allgemeinen LLM_API_KEY."""
    base_url = _CHAT_COMPLETIONS.sub("", os.environ.get("LLM_BASE_URL", "").rstrip("/"))
    modell_var = ""
    if modell:
        try:
            from strassen.llm_vergleich import kurzname
            modell_var = f"LLM_API_KEY_{kurzname(modell).upper()}"
        except ValueError:
            modell_var = ""
    api_key = (os.environ.get(modell_var, "") if modell_var else "") or os.environ.get("LLM_API_KEY", "")
    if not base_url or not api_key:
        namen = f"{modell_var} bzw. LLM_API_KEY" if modell_var else "LLM_API_KEY"
        raise KonfigurationsFehler(f"LLM_BASE_URL und {namen} müssen gesetzt sein (.env oder Umgebung)")
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
    if not isinstance(text, str):
        # Der Inferenzserver liefert bei abgeschnittenen Antworten 'content': null
        # (beobachtet in der Kalibrierung, Task 11). Das ist eine leere Antwort und
        # gehört in die JSON-Wiederholung, nicht in einen TypeError.
        raise JsonFehler(f"kein Text in der Antwort (Typ {type(text).__name__})")
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


def sende(anfrage: dict, base_url: str, api_key: str, timeout: int = 300) -> str:
    """POST an <base_url>/chat/completions; gibt den Antworttext des Modells zurück.
    Fehlerhafte/unerwartete Antworten und Transportfehler werden als HttpFehler(502/503)
    gemeldet, damit _sende_mit_wiederholung sie wie jeden anderen 5xx-Fehler wiederholt."""
    req = urllib.request.Request(
        f"{base_url}/chat/completions", data=json.dumps(anfrage).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as antwort:
            rohtext = antwort.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", errors="replace")
        except Exception:
            text = ""
        raise HttpFehler(e.code, text) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise HttpFehler(503, str(e)) from e
    try:
        daten = json.loads(rohtext)
        inhalt = daten["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise HttpFehler(502, f"Antwort ohne choices: {rohtext[:200]}") from e
    # 'content': null heißt: Antwort strukturell in Ordnung, aber ohne Text (z. B.
    # finish_reason 'length'). Als leerer Text weitergeben, damit lies_seite es
    # wiederholt und die Seite notfalls als 'unlesbar' verbucht.
    return inhalt if isinstance(inhalt, str) else ""


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
    """Eine Buchseite lesen lassen. Vorhandene Antwort wird wiederverwendet, sofern ihr
    prompt_hash zum aktuellen Prompt passt (außer neu=True: immer neu anfordern).
    Unlesbares JSON: bis MAX_JSON_VERSUCHE identische Anfragen, dann fehler='unlesbar'."""
    ziel = antwort_pfad(ziel_dir, modell, buchseite)
    h = prompt_hash(prompt)
    if ziel.exists() and not neu:
        vorhanden = json.loads(ziel.read_text(encoding="utf-8"))
        # Antwort aus einem anderen Prompt-Stand zählt als Cache-Fehltreffer: sonst
        # mischt ein Prompt-Wechsel unbemerkt zwei Stände in einem Antwortordner.
        if vorhanden.get("prompt_hash") == h:
            return vorhanden

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
                "prompt_hash": h, "rohtext": rohtext,
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
    try:
        base_url, api_key = konfiguration(a.modell)
    except KonfigurationsFehler as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    sende_fn = partial(sende, base_url=base_url, api_key=api_key)
    prompt = lade_prompt()
    seiten = parse_seitenbereich(a.seiten)
    gelesen = unlesbar = ohne_bild = 0
    for b in seiten:
        png = Path(a.seiten_dir) / seiten_dateiname(b)
        if not png.exists():
            ohne_bild += 1
            continue
        try:
            erg = lies_seite(b, a.modell, png, prompt, sende_fn, a.antworten_dir, a.neu)
        except LaufAbbruch as e:
            # Erwarteter Abbruch (429/5xx erschöpft) — kein Traceback, die bereits
            # gesicherten Seiten bleiben gültig und werden beim nächsten Lauf ergänzt.
            print(f"Fehler: {e}", file=sys.stderr)
            sys.exit(1)
        gelesen += 1
        unlesbar += erg["fehler"] == "unlesbar"
        print(f"s{b:03d}: {len(erg['eintraege'] or [])} Einträge{' (unlesbar)' if erg['fehler'] else ''}",
              flush=True)
    print(f"{gelesen} Seiten, davon {unlesbar} unlesbar — Modell {a.modell}"
          + (f"; {ohne_bild} Seiten ohne Seitenbild übersprungen" if ohne_bild else ""))


if __name__ == "__main__":
    _cli()
