from __future__ import annotations

from dataclasses import replace

import httpx
import pytest

from rag_app.config import Settings
from rag_app.generation.providers import LLMProviderError, OllamaProvider, create_llm_provider


def test_settings_are_forwarded_to_ollama_provider():
    settings = replace(
        Settings(),
        llm_provider="ollama",
        llm_model="modelo-local",
        llm_num_ctx=2048,
        llm_max_tokens=123,
        llm_temperature=0.2,
        llm_top_p=0.8,
        llm_keep_alive="3m",
        llm_think=False,
    )
    provider = create_llm_provider(settings)
    assert isinstance(provider, OllamaProvider)
    assert provider.options == {
        "num_ctx": 2048,
        "num_predict": 123,
        "temperature": 0.2,
        "top_p": 0.8,
    }
    assert provider.keep_alive == "3m"


def test_llm_settings_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("RAG_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_LLM_MODEL", "modelo-entorno")
    monkeypatch.setenv("RAG_LLM_TIMEOUT_SECONDS", "37.5")
    monkeypatch.setenv("RAG_LLM_NUM_CTX", "3072")
    monkeypatch.setenv("RAG_LLM_MAX_TOKENS", "321")
    monkeypatch.setenv("RAG_LLM_TEMPERATURE", "0.15")
    monkeypatch.setenv("RAG_LLM_TOP_P", "0.75")
    monkeypatch.setenv("RAG_LLM_KEEP_ALIVE", "4m")
    monkeypatch.setenv("RAG_LLM_THINK", "true")
    monkeypatch.setenv("RAG_LLM_JSON_RETRIES", "2")
    settings = Settings()
    provider = create_llm_provider(settings)
    assert isinstance(provider, OllamaProvider)
    assert settings.llm_json_retries == 2
    assert provider.timeout_seconds == 37.5
    assert provider.options == {
        "num_ctx": 3072,
        "num_predict": 321,
        "temperature": 0.15,
        "top_p": 0.75,
    }
    assert provider.keep_alive == "4m"
    assert provider.think is True


def test_ollama_generate_requests_schema_and_exposes_metrics(monkeypatch):
    captured = {}

    def fake_request(method, url, **kwargs):
        captured.update(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request(method, url),
            json={
                "message": {"content": '{"answer":"ok"}'},
                "total_duration": 2_000_000_000,
                "load_duration": 500_000_000,
                "prompt_eval_count": 10,
                "eval_count": 20,
                "eval_duration": 1_000_000_000,
            },
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    provider = OllamaProvider("http://localhost:11434", "modelo-local", max_tokens=100)
    result = provider.generate("sistema", "usuario", {"type": "object"})
    assert captured["format"] == {"type": "object"}
    assert captured["stream"] is False
    assert captured["options"]["num_predict"] == 100
    assert captured["think"] is False
    assert captured["keep_alive"] == "10m"
    assert result.content == '{"answer":"ok"}'
    assert result.metrics.total_duration_ms == 2000
    assert result.metrics.tokens_per_second == 20


def test_ollama_health_detects_missing_model(monkeypatch):
    def fake_request(method, url, **kwargs):
        return httpx.Response(200, request=httpx.Request(method, url), json={"models": [{"name": "otro:7b"}]})

    monkeypatch.setattr(httpx, "request", fake_request)
    health = OllamaProvider("http://localhost:11434", "modelo-local").health()
    assert health.available is True
    assert health.model_available is False


def test_ollama_timeout_is_typed(monkeypatch):
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("tarde")

    monkeypatch.setattr(httpx, "request", timeout)
    provider = OllamaProvider("http://localhost:11434", "modelo-local")
    with pytest.raises(LLMProviderError, match="tiempo") as error:
        provider.generate("s", "u", {"type": "object"})
    assert error.value.code == "timeout"


def test_ollama_connection_error_is_typed(monkeypatch):
    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("sin servicio")

    monkeypatch.setattr(httpx, "request", unavailable)
    provider = OllamaProvider("http://localhost:11434", "modelo-local")
    with pytest.raises(LLMProviderError, match="conectar") as error:
        provider.generate("s", "u", {"type": "object"})
    assert error.value.code == "unavailable"
