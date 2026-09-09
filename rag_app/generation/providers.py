from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

import httpx

from rag_app.config import Settings


class LLMProviderError(RuntimeError):
    """Error controlado de un proveedor; su mensaje es seguro para la interfaz."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    model: str
    enabled: bool
    available: bool
    model_available: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationMetrics:
    total_duration_ms: float | None = None
    load_duration_ms: float | None = None
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    tokens_per_second: float | None = None


@dataclass(frozen=True)
class GenerationResult:
    content: str
    metrics: GenerationMetrics


class LLMProvider(Protocol):
    enabled: bool
    provider_name: str
    model: str

    def generate(self, system: str, user: str, response_schema: dict[str, Any]) -> GenerationResult: ...
    def health(self) -> ProviderHealth: ...


class DisabledProvider:
    enabled = False
    provider_name = "disabled"
    model = ""

    def generate(self, system: str, user: str, response_schema: dict[str, Any]) -> GenerationResult:
        raise LLMProviderError("disabled", "El proveedor LLM está deshabilitado.")

    def health(self) -> ProviderHealth:
        return ProviderHealth("disabled", "", False, True, False, "Generación local deshabilitada")


class OllamaProvider:
    enabled = True
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        timeout_seconds: float = 120,
        num_ctx: int = 4096,
        max_tokens: int = 500,
        temperature: float = 0,
        top_p: float = 0.9,
        keep_alive: str = "10m",
        think: bool = False,
    ) -> None:
        if not model:
            raise ValueError("RAG_LLM_MODEL es obligatorio para Ollama")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.options = {
            "num_ctx": num_ctx,
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        self.keep_alive = keep_alive
        self.think = think

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout_seconds,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise LLMProviderError("timeout", "Ollama excedió el tiempo máximo de respuesta.") from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("unavailable", "No se pudo conectar con Ollama en el endpoint configurado.") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            code = "model_unavailable" if status == 404 else "http_error"
            detail = "El modelo configurado no está disponible en Ollama." if status == 404 else f"Ollama respondió HTTP {status}."
            raise LLMProviderError(code, detail) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise LLMProviderError("invalid_response", "Ollama devolvió una respuesta no utilizable.") from exc

    def health(self) -> ProviderHealth:
        try:
            response = self._request("GET", "/api/tags")
            payload = response.json()
            names = {str(item.get("name", "")) for item in payload.get("models", [])}
        except (LLMProviderError, ValueError, TypeError) as exc:
            detail = str(exc) if isinstance(exc, LLMProviderError) else "Ollama devolvió un inventario inválido."
            return ProviderHealth("ollama", self.model, True, False, False, detail)
        model_available = self.model in names
        detail = "Ollama disponible y modelo instalado." if model_available else "Ollama disponible, pero el modelo configurado no está instalado."
        return ProviderHealth("ollama", self.model, True, True, model_available, detail)

    def generate(self, system: str, user: str, response_schema: dict[str, Any]) -> GenerationResult:
        response = self._request(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "stream": False,
                "format": response_schema,
                "think": self.think,
                "keep_alive": self.keep_alive,
                "options": self.options,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        try:
            payload = response.json()
            content = str(payload["message"]["content"]).strip()
            if not content:
                raise KeyError("content")
            eval_count = int(payload["eval_count"]) if payload.get("eval_count") is not None else None
            eval_duration = int(payload["eval_duration"]) if payload.get("eval_duration") else None
            tokens_per_second = (
                eval_count / (eval_duration / 1_000_000_000)
                if eval_count is not None and eval_duration
                else None
            )
            metrics = GenerationMetrics(
                total_duration_ms=_nanoseconds_to_ms(payload.get("total_duration")),
                load_duration_ms=_nanoseconds_to_ms(payload.get("load_duration")),
                prompt_tokens=_optional_int(payload.get("prompt_eval_count")),
                output_tokens=eval_count,
                tokens_per_second=tokens_per_second,
            )
            return GenerationResult(content, metrics)
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise LLMProviderError("invalid_response", "Ollama devolvió una respuesta sin contenido o métricas válidas.") from exc


class OpenAICompatibleProvider:
    enabled = True
    provider_name = "openai-compatible"

    def __init__(self, base_url: str, model: str, api_key: str, timeout_seconds: float = 120) -> None:
        if not model:
            raise ValueError("RAG_LLM_MODEL es obligatorio para el proveedor compatible")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def health(self) -> ProviderHealth:
        try:
            response = httpx.get(f"{self.base_url}/v1/models", headers=self._headers, timeout=min(self.timeout_seconds, 10))
            response.raise_for_status()
            names = {str(item.get("id", "")) for item in response.json().get("data", [])}
        except (httpx.HTTPError, ValueError, TypeError):
            return ProviderHealth(self.provider_name, self.model, True, False, False, "Proveedor compatible no disponible.")
        model_available = not names or self.model in names
        return ProviderHealth(self.provider_name, self.model, True, True, model_available, "Proveedor compatible disponible.")

    def generate(self, system: str, user: str, response_schema: dict[str, Any]) -> GenerationResult:
        try:
            response = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers,
                json={
                    "model": self.model,
                    "temperature": 0,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {"name": "ragscate_grounded_answer", "strict": True, "schema": response_schema},
                    },
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            content = str(payload["choices"][0]["message"]["content"]).strip()
            usage = payload.get("usage", {})
            return GenerationResult(
                content,
                GenerationMetrics(
                    prompt_tokens=_optional_int(usage.get("prompt_tokens")),
                    output_tokens=_optional_int(usage.get("completion_tokens")),
                ),
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderError("timeout", "El proveedor LLM excedió el tiempo máximo de respuesta.") from exc
        except httpx.ConnectError as exc:
            raise LLMProviderError("unavailable", "No se pudo conectar con el proveedor LLM.") from exc
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("invalid_response", "El proveedor LLM devolvió una respuesta no utilizable.") from exc


def _nanoseconds_to_ms(value: object) -> float | None:
    return float(value) / 1_000_000 if value is not None else None


def _optional_int(value: object) -> int | None:
    return int(value) if value is not None else None


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "disabled":
        return DisabledProvider()
    if provider == "ollama":
        return OllamaProvider(
            settings.llm_base_url,
            settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            num_ctx=settings.llm_num_ctx,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            top_p=settings.llm_top_p,
            keep_alive=settings.llm_keep_alive,
            think=settings.llm_think,
        )
    if provider in {"openai-compatible", "openai_compatible"}:
        return OpenAICompatibleProvider(
            settings.llm_base_url,
            settings.llm_model,
            settings.llm_api_key,
            settings.llm_timeout_seconds,
        )
    raise ValueError(f"Proveedor LLM no soportado: {settings.llm_provider}")
