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
