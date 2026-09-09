from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else ROOT / value


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on", "si", "sí"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} debe ser true o false")


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    corpus_dir: Path = field(default_factory=lambda: _path_from_env("RAG_CORPUS_DIR", "pb-src"))
    data_dir: Path = field(default_factory=lambda: _path_from_env("RAG_DATA_DIR", "rag-data"))
    pbl_name: str = field(default_factory=lambda: os.getenv("RAG_PBL_NAME", "cotizador_mvp.pbl"))
    embed_provider: str = field(default_factory=lambda: os.getenv("RAG_EMBED_PROVIDER", "sentence-transformers"))
    embed_model: str = field(default_factory=lambda: os.getenv("RAG_EMBED_MODEL", ""))
    embed_device: str = field(default_factory=lambda: os.getenv("RAG_EMBED_DEVICE", "cpu"))
    llm_provider: str = field(default_factory=lambda: os.getenv("RAG_LLM_PROVIDER", "disabled"))
    llm_model: str = field(default_factory=lambda: os.getenv("RAG_LLM_MODEL", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("RAG_LLM_BASE_URL", "http://127.0.0.1:11434"))
    llm_api_key: str = field(default_factory=lambda: os.getenv("RAG_LLM_API_KEY", ""))
    llm_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("RAG_LLM_TIMEOUT_SECONDS", "120")))
    llm_num_ctx: int = field(default_factory=lambda: int(os.getenv("RAG_LLM_NUM_CTX", "4096")))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("RAG_LLM_MAX_TOKENS", "500")))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("RAG_LLM_TEMPERATURE", "0")))
    llm_top_p: float = field(default_factory=lambda: float(os.getenv("RAG_LLM_TOP_P", "0.9")))
    llm_keep_alive: str = field(default_factory=lambda: os.getenv("RAG_LLM_KEEP_ALIVE", "10m"))
    llm_think: bool = field(default_factory=lambda: _env_bool("RAG_LLM_THINK", False))
    llm_json_retries: int = field(default_factory=lambda: int(os.getenv("RAG_LLM_JSON_RETRIES", "1")))
    top_k: int = field(default_factory=lambda: int(os.getenv("RAG_TOP_K", "8")))
    max_context_chars: int = field(default_factory=lambda: int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000")))

    @property
    def database_path(self) -> Path:
        return self.data_dir / "ragscate.sqlite3"


def get_settings() -> Settings:
    return Settings()
