import sys
from rag_app.config import get_settings
from rag_app.storage.database import connect, latest_snapshot_id
from rag_app.generation.service import AnswerService
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.generation.citations import CitationValidator
from rag_app.indexer import create_encoder
from rag_app.generation.providers import create_llm_provider

settings = get_settings()
conn = connect(settings.database_path)
snapshot_id = latest_snapshot_id(conn)
encoder = create_encoder(settings)
retriever = HybridRetriever(conn, settings.data_dir, encoder)
validator = CitationValidator(settings.root, conn)
llm = create_llm_provider(settings)
service = AnswerService(conn, retriever, validator, llm, settings.max_context_chars, settings.llm_json_retries)

answer = service.ask(snapshot_id, "que calcula la edad?")
print("\n--- RESPUESTA ---")
print(answer.answer)
print("\n--- CITAS MOSTRADAS ---")
for c in answer.citations:
    print(c.file)
