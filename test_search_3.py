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

print("\n--- REGLAS DE PDF ---")
doc_hits = retriever.search(snapshot_id, "que calcula la edad?", top_k=5, object_type="business_rule")
for h in doc_hits:
    print(f"Líneas {h.chunk.start_line}-{h.chunk.end_line}: {h.chunk.source_path}")
    print(f"Snippet preview: {h.chunk.text.strip()[:60]}...")
    print("-")
