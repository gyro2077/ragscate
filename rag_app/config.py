from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else ROOT / value


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    corpus_dir: Path = _path_from_env("RAG_CORPUS_DIR", "pb-src")
    data_dir: Path = _path_from_env("RAG_DATA_DIR", "rag-data")
    pbl_name: str = os.getenv("RAG_PBL_NAME", "cotizador_mvp.pbl")
    embed_provider: str = os.getenv("RAG_EMBED_PROVIDER", "sentence-transformers")
    embed_model: str = os.getenv("RAG_EMBED_MODEL", "")
    embed_device: str = os.getenv("RAG_EMBED_DEVICE", "cpu")
    llm_provider: str = os.getenv("RAG_LLM_PROVIDER", "disabled")
    llm_model: str = os.getenv("RAG_LLM_MODEL", "")
    llm_base_url: str = os.getenv("RAG_LLM_BASE_URL", "http://127.0.0.1:11434")
    llm_api_key: str = os.getenv("RAG_LLM_API_KEY", "")
    top_k: int = int(os.getenv("RAG_TOP_K", "8"))
    max_context_chars: int = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "12000"))

    @property
    def database_path(self) -> Path:
        return self.data_dir / "ragscate.sqlite3"


def get_settings() -> Settings:
    return Settings()
