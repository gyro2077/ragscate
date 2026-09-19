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

question = "que hace el negocio?"

# Simulate the fixed logic
all_hits = retriever.search(snapshot_id, question, top_k=20)
code_hits = [h for h in all_hits if h.chunk.object_type != "business_rule"][:5]

doc_hits_raw = retriever.search(snapshot_id, question, top_k=8, object_type="business_rule")
seen = set()
doc_hits = []
for h in doc_hits_raw:
    if h.chunk.raw_sha256 not in seen:
        seen.add(h.chunk.raw_sha256)
        doc_hits.append(h)
    if len(doc_hits) >= 4:
        break

print(f"CODE HITS: {len(code_hits)}")
for h in code_hits:
    print(f"  {h.score:.3f} | {h.chunk.object_type} | {h.chunk.source_path}")

print(f"\nDOC HITS (deduplicados): {len(doc_hits)}")
for h in doc_hits:
    print(f"  {h.score:.3f} | {h.chunk.object_type} | {h.chunk.source_path} | L{h.chunk.start_line}-{h.chunk.end_line}")
