from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from rag_app.api.main import create_app
from rag_app.config import ROOT, Settings
from rag_app.indexer import index_corpus
from rag_app.retrieval.semantic import HashingEncoder


def make_client(tmp_path):
    settings = replace(
        Settings(), root=ROOT, corpus_dir=ROOT / "pb-src", data_dir=tmp_path,
        embed_provider="hashing-test", embed_model="deterministic-token-hash", llm_provider="disabled",
    )
    encoder = HashingEncoder()
    result = index_corpus(settings, encoder)
    return TestClient(create_app(settings, encoder)), result


def test_health_home_search_and_ask(tmp_path):
    client, indexed = make_client(tmp_path)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["snapshot_id"] == indexed["snapshot_id"]
    rebuilt = client.post("/api/index")
    assert rebuilt.status_code == 200 and rebuilt.json()["source_count"] == 5
    home = client.get("/")
    assert home.status_code == 200 and "RAGscate" in home.text
    search = client.post("/api/search", json={"query": "of_limpiar", "top_k": 3})
    assert search.status_code == 200
    assert search.json()[0]["member"] == "of_limpiar"
    answer = client.post("/api/ask", json={"question": "¿Donde se calcula la prima anual?"})
    assert answer.status_code == 200
    body = answer.json()
    assert body["classification"] == "Comprobado"
    assert body["citations"][0]["snippet"]
    assert body["citations"][0]["snapshot_id"] == indexed["snapshot_id"]


def test_absence_contract_and_source_endpoint(tmp_path):
    client, _indexed = make_client(tmp_path)
    missing = client.post("/api/ask", json={"question": "¿Donde se valida numero_poliza?"})
    assert missing.status_code == 200
    assert missing.json()["classification"] == "No localizado"
    assert missing.json()["citations"] == []
    found = client.post("/api/search", json={"query": "of_limpiar", "top_k": 1}).json()[0]
    source = client.get(f"/api/source/{found['chunk_id']}?start_line={found['start_line']}&end_line={found['end_line']}")
    assert source.status_code == 200
    assert source.json()["member"] == "of_limpiar"


def test_api_requires_index(tmp_path):
    settings = replace(Settings(), root=ROOT, corpus_dir=ROOT / "pb-src", data_dir=tmp_path, embed_provider="hashing-test")
    client = TestClient(create_app(settings, HashingEncoder()))
    response = client.post("/api/ask", json={"question": "algo"})
    assert response.status_code == 409
