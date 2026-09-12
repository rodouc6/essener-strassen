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
