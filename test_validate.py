import sys
from rag_app.config import get_settings
from rag_app.storage.database import connect, latest_snapshot_id
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.indexer import create_encoder
from rag_app.generation.citations import CitationValidator

settings = get_settings()
conn = connect(settings.database_path)
snapshot_id = latest_snapshot_id(conn)
encoder = create_encoder(settings)
retriever = HybridRetriever(conn, settings.data_dir, encoder)
validator = CitationValidator(settings.root, conn)

doc_hits = retriever.search(snapshot_id, "que calcula la edad?", top_k=5, object_type="business_rule")
for h in doc_hits:
    print(f"\n--- Probando validar chunk {h.chunk.chunk_id} ({h.chunk.source_path}) ---")
    try:
        cite = validator.build(h.chunk)
        print("OK: Cita generada correctamente.")
    except Exception as e:
        print(f"ERROR: {e}")

