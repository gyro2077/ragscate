from __future__ import annotations

from dataclasses import replace

import pytest

from rag_app.config import ROOT, Settings
from rag_app.indexer import index_corpus
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.retrieval.semantic import HashingEncoder
from rag_app.storage.database import connect, list_snapshots


@pytest.fixture()
def indexed(tmp_path):
    settings = replace(Settings(), root=ROOT, corpus_dir=ROOT / "pb-src", data_dir=tmp_path, embed_provider="hashing-test", embed_model="deterministic-token-hash")
    encoder = HashingEncoder()
    result = index_corpus(settings, encoder)
    connection = connect(settings.database_path)
    retriever = HybridRetriever(connection, settings.data_dir, encoder)
    yield settings, result, connection, retriever
    connection.close()


def test_index_persists_manifest_chunks_relations_and_embeddings(indexed):
    settings, result, connection, _retriever = indexed
    assert result["source_count"] == 5
    assert result["chunk_count"] > 15
    assert result["relation_count"] > 10
    assert list_snapshots(connection)[0]["snapshot_id"] == result["snapshot_id"]
    snapshot_dir = settings.data_dir / "snapshots" / result["snapshot_id"]
    for name in ("manifest.jsonl", "chunks.jsonl", "relations.jsonl", "embeddings.npy", "embedding_ids.json", "embedding_meta.json"):
        assert (snapshot_dir / name).is_file()


@pytest.mark.parametrize(("question", "expected"), [
    ("¿Donde se calcula la prima anual?", "of_calcular_cotizacion"),
    ("Explicame el flujo del boton Calcular", "cb_calcular.clicked"),
    ("¿Que validaciones se aplican a la edad?", "of_leer_entradas"),
    ("¿Por que edad 70 y categoria Alto requieren autorizacion?", "of_calcular_cotizacion"),
    ("¿Donde cambiaria el impuesto?", "of_calcular_cotizacion"),
    ("¿Que funciones se afectan al agregar una categoria?", "of_factor_categoria"),
    ("¿Que tabla consulta d_tabla_primas_edad?", "d_tabla_primas_edad"),
    ("¿Como se calcula la cuota mensual?", "of_calcular_cotizacion"),
    ("¿Que hace Limpiar?", "of_limpiar"),
])
def test_expected_member_is_in_top_three(indexed, question, expected):
    _settings, result, _connection, retriever = indexed
    hits = retriever.search(result["snapshot_id"], question, top_k=3)
    assert expected in {hit.chunk.member_name for hit in hits} or expected in {hit.chunk.object_name for hit in hits}


def test_exact_symbol_has_priority(indexed):
    _settings, result, _connection, retriever = indexed
    hits = retriever.search(result["snapshot_id"], "Explica of_limpiar", top_k=3)
    assert hits[0].chunk.member_name == "of_limpiar"
    assert hits[0].exact_symbol


def test_unknown_identifier_is_detected(indexed):
    _settings, result, _connection, retriever = indexed
    assert retriever.unknown_identifiers(result["snapshot_id"], "¿Donde se valida numero_poliza?") == ["numero_poliza"]


def test_filters_are_applied(indexed):
    _settings, result, _connection, retriever = indexed
    hits = retriever.search(result["snapshot_id"], "prima", top_k=10, object_type="userobject")
    assert hits and all(hit.chunk.object_type == "userobject" for hit in hits)
