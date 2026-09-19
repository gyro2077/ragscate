import sys
from rag_app.config import get_settings
from rag_app.storage.database import connect, latest_snapshot_id
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.indexer import create_encoder

settings = get_settings()
conn = connect(settings.database_path)
snapshot_id = latest_snapshot_id(conn)
encoder = create_encoder(settings)
retriever = HybridRetriever(conn, settings.data_dir, encoder)

print("\n--- SOLO REGLAS ---")
doc_hits = retriever.search(snapshot_id, "que parte del pdf calcula la prima?", top_k=5, object_type="business_rule")
for h in doc_hits:
    print(f"{h.score:.3f} | {h.chunk.object_type} | {h.chunk.source_path}")
