from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np

from rag_app.domain.models import Chunk
from rag_app.ingestion.common import normalize_text


class SemanticEncoder(Protocol):
    provider_name: str
    model_name: str

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray: ...
    def encode_query(self, text: str) -> np.ndarray: ...


@dataclass
class HashingEncoder:
    """Codificador determinista para pruebas; no reemplaza Sentence Transformers."""

    dimensions: int = 512
    provider_name: str = "hashing-test"
    model_name: str = "deterministic-token-hash"

    def _encode(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        normalized = normalize_text(text)
        tokens = re.findall(r"[a-z0-9]+", normalized)
        features = tokens + [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        return np.vstack([self._encode(text) for text in texts])

    def encode_query(self, text: str) -> np.ndarray:
        return self._encode(text)


class SentenceTransformerEncoder:
    provider_name = "sentence-transformers"

    def __init__(self, model_name: str, device: str = "cpu") -> None:
        if not model_name:
            raise ValueError("Configure RAG_EMBED_MODEL para usar Sentence Transformers")
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, device=device)

    def encode_documents(self, texts: Sequence[str]) -> np.ndarray:
        method = getattr(self._model, "encode_document", self._model.encode)
        return np.asarray(method(list(texts), normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        method = getattr(self._model, "encode_query", self._model.encode)
        result = method([text], normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(result[0], dtype=np.float32)


def save_embeddings(snapshot_dir: Path, chunks: list[Chunk], encoder: SemanticEncoder) -> None:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    matrix = encoder.encode_documents([f"{c.object_name} {c.member_name} {' '.join(c.symbols)} {c.normalized_text}" for c in chunks])
    np.save(snapshot_dir / "embeddings.npy", matrix, allow_pickle=False)
    (snapshot_dir / "embedding_ids.json").write_text(json.dumps([c.chunk_id for c in chunks]), encoding="utf-8")
    (snapshot_dir / "embedding_meta.json").write_text(json.dumps({
        "provider": encoder.provider_name,
        "model": encoder.model_name,
        "dimensions": int(matrix.shape[1]),
        "count": int(matrix.shape[0]),
    }, indent=2), encoding="utf-8")


def load_embeddings(snapshot_dir: Path) -> tuple[np.ndarray, list[str], dict[str, object]]:
    matrix = np.load(snapshot_dir / "embeddings.npy", allow_pickle=False)
    ids = json.loads((snapshot_dir / "embedding_ids.json").read_text(encoding="utf-8"))
    meta = json.loads((snapshot_dir / "embedding_meta.json").read_text(encoding="utf-8"))
    if matrix.shape[0] != len(ids):
        raise ValueError("La matriz de embeddings no coincide con sus identificadores")
    return matrix, ids, meta
