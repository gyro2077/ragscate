from __future__ import annotations

import json
from pathlib import Path

from rag_app.config import Settings
from rag_app.domain.models import Chunk, Relation
from rag_app.ingestion.chunker import parse_all
from rag_app.ingestion.manifest import build_manifest, write_manifest
from rag_app.retrieval.semantic import HashingEncoder, SemanticEncoder, SentenceTransformerEncoder, save_embeddings
from rag_app.storage.database import connect, replace_snapshot


def create_encoder(settings: Settings, testing: bool = False) -> SemanticEncoder:
    if testing or settings.embed_provider == "hashing-test":
        return HashingEncoder()
    if settings.embed_provider == "sentence-transformers":
        return SentenceTransformerEncoder(settings.embed_model, settings.embed_device)
    raise ValueError(f"Proveedor de embeddings no soportado: {settings.embed_provider}")


def index_corpus(settings: Settings, encoder: SemanticEncoder | None = None) -> dict[str, object]:
    snapshot_id, initial_sources = build_manifest(settings.root, settings.corpus_dir, settings.pbl_name)
    sources, chunks, relations = parse_all(settings.root, initial_sources)
    encoder = encoder or create_encoder(settings)
    snapshot_dir = settings.data_dir / "snapshots" / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(snapshot_dir / "manifest.jsonl", sources)
    (snapshot_dir / "chunks.jsonl").write_text(
        "".join(json.dumps(chunk.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for chunk in chunks), encoding="utf-8"
    )
    (snapshot_dir / "relations.jsonl").write_text(
        "".join(json.dumps(relation.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for relation in relations), encoding="utf-8"
    )
    save_embeddings(snapshot_dir, chunks, encoder)
    connection = connect(settings.database_path)
    try:
        replace_snapshot(connection, sources, chunks, relations, encoder.provider_name, encoder.model_name)
    finally:
        connection.close()
    return {
        "snapshot_id": snapshot_id,
        "source_count": len(sources),
        "chunk_count": len(chunks),
        "relation_count": len(relations),
        "embed_provider": encoder.provider_name,
        "embed_model": encoder.model_name,
    }
