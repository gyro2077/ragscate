from __future__ import annotations

from typing import Protocol

from rag_app.config import Settings


class LLMProvider(Protocol):
    enabled: bool

    def generate(self, system: str, user: str) -> str: ...


class DisabledProvider:
    enabled = False

    def generate(self, system: str, user: str) -> str:
        raise RuntimeError("El proveedor LLM esta deshabilitado")


class OllamaProvider:
    enabled = True

    def __init__(self, base_url: str, model: str) -> None:
        if not model:
            raise ValueError("RAG_LLM_MODEL es obligatorio para Ollama")
        self.base_url, self.model = base_url.rstrip("/"), model

    def generate(self, system: str, user: str) -> str:
        import httpx
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "stream": False, "messages": [
                {"role": "system", "content": system}, {"role": "user", "content": user},
            ]}, timeout=90,
        )
        response.raise_for_status()
        return str(response.json()["message"]["content"]).strip()


class OpenAICompatibleProvider:
    enabled = True

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        if not model:
            raise ValueError("RAG_LLM_MODEL es obligatorio para el proveedor compatible")
        self.base_url, self.model, self.api_key = base_url.rstrip("/"), model, api_key

    def generate(self, system: str, user: str) -> str:
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = httpx.post(
            f"{self.base_url}/v1/chat/completions", headers=headers,
            json={"model": self.model, "temperature": 0, "messages": [
                {"role": "system", "content": system}, {"role": "user", "content": user},
            ]}, timeout=90,
        )
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"]).strip()


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "disabled":
        return DisabledProvider()
    if provider == "ollama":
        return OllamaProvider(settings.llm_base_url, settings.llm_model)
    if provider in {"openai-compatible", "openai_compatible"}:
        return OpenAICompatibleProvider(settings.llm_base_url, settings.llm_model, settings.llm_api_key)
    raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")
