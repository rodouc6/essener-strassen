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


def test_sende_meldet_antwort_ohne_choices_als_http_502(monkeypatch):
    class Antwort:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self):
            return json.dumps({"error": "x"}).encode()

    def urlopen(req, timeout):
        return Antwort()

    monkeypatch.setattr(ll.urllib.request, "urlopen", urlopen)
    with pytest.raises(ll.HttpFehler) as exc:
        ll.sende({"model": "m"}, "https://h/v1", "k")
    assert exc.value.status == 502


def test_sende_uebersetzt_urlerror_in_http_503(monkeypatch):
    def urlopen(req, timeout):
        raise ll.urllib.error.URLError("down")

    monkeypatch.setattr(ll.urllib.request, "urlopen", urlopen)
    with pytest.raises(ll.HttpFehler) as exc:
        ll.sende({"model": "m"}, "https://h/v1", "k")
    assert exc.value.status == 503


def test_sende_uebersteht_fehlschlagendes_lesen_der_fehlerantwort(monkeypatch):
    def urlopen(req, timeout):
        raise ll.urllib.error.HTTPError("https://h/v1/chat/completions", 500, "msg", hdrs=None, fp=None)

    monkeypatch.setattr(ll.urllib.request, "urlopen", urlopen)
    with pytest.raises(ll.HttpFehler) as exc:
        ll.sende({"model": "m"}, "https://h/v1", "k")
    assert exc.value.status == 500
