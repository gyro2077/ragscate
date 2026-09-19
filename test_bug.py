import sys
from rag_app.config import get_settings
from rag_app.storage.database import connect, latest_snapshot_id
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.generation.citations import CitationValidator
from rag_app.indexer import create_encoder
from rag_app.generation.service import AnswerService
from rag_app.generation.providers import create_llm_provider

settings = get_settings()
conn = connect(settings.database_path)
snapshot_id = latest_snapshot_id(conn)
encoder = create_encoder(settings)
retriever = HybridRetriever(conn, settings.data_dir, encoder)
validator = CitationValidator(settings.root, conn)
llm = create_llm_provider(settings)
service = AnswerService(conn, retriever, validator, llm, settings.max_context_chars, settings.llm_json_retries)

question = "que hace el negocio?"
code_hits = retriever.search(snapshot_id, question, top_k=5)
code_hits = [h for h in code_hits if h.chunk.object_type != "business_rule"]
doc_hits = retriever.search(snapshot_id, question, top_k=4, object_type="business_rule")

print(f"Code hits: {[h.chunk.source_path for h in code_hits]}")
print(f"Doc hits: {[h.chunk.source_path for h in doc_hits]}")

code_citations = []
for h in code_hits: code_citations.append(validator.build(h.chunk))
doc_citations = []
for h in doc_hits: doc_citations.append(validator.build(h.chunk))

all_citations = doc_citations + code_citations
fitted = service._fit_context(all_citations)

doc_evidence = []
code_evidence = []
for c in fitted:
    if c in doc_citations:
        doc_evidence.append(c)
    else:
        code_evidence.append(c)

print(f"Doc evidence count: {len(doc_evidence)}")
print(f"Code evidence count: {len(code_evidence)}")
