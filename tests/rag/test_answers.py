from __future__ import annotations

from dataclasses import replace

import pytest

from rag_app.config import ROOT, Settings
from rag_app.generation.citations import CitationValidationError, CitationValidator
from rag_app.generation.service import AnswerService
from rag_app.indexer import index_corpus
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.retrieval.semantic import HashingEncoder
from rag_app.storage.database import connect, get_chunk


@pytest.fixture()
def answer_stack(tmp_path):
    settings = replace(Settings(), root=ROOT, corpus_dir=ROOT / "pb-src", data_dir=tmp_path, embed_provider="hashing-test", embed_model="deterministic-token-hash")
    encoder = HashingEncoder()
    result = index_corpus(settings, encoder)
    connection = connect(settings.database_path)
    validator = CitationValidator(settings.root, connection)
    service = AnswerService(connection, HybridRetriever(connection, settings.data_dir, encoder), validator)
    yield result["snapshot_id"], service, validator, connection
    connection.close()


@pytest.mark.parametrize("question", [
    "¿Donde se calcula la prima anual?",
    "Explicame el flujo del boton Calcular.",
    "¿Que validaciones se aplican a la edad?",
    "¿Por que edad 70 y categoria Alto requieren autorizacion?",
    "¿Donde cambiaria el impuesto?",
    "¿Que funciones se afectan al agregar una categoria?",
    "¿Que tabla consulta d_tabla_primas_edad?",
    "¿Como se calcula la cuota mensual?",
    "¿Que hace Limpiar?",
])
def test_grounded_gold_answers_have_only_valid_citations(answer_stack, question):
    snapshot, service, validator, _connection = answer_stack
    answer = service.ask(snapshot, question)
    assert answer.classification == "Comprobado"
    assert answer.citations
    assert all(validator.validate(citation) for citation in answer.citations)


def test_missing_symbol_abstains_without_citations(answer_stack):
    snapshot, service, _validator, _connection = answer_stack
    answer = service.ask(snapshot, "¿Donde se valida numero_poliza?")
    assert answer.classification == "No localizado"
    assert answer.citations == []
    assert "numero_poliza" in answer.answer


def test_related_non_gold_question_is_marked_as_inferred(answer_stack):
    snapshot, service, validator, _connection = answer_stack
    answer = service.ask(snapshot, "¿Que contiene el objeto de reglas?")
    assert answer.classification == "Inferido"
    assert answer.citations
    assert all(validator.validate(citation) for citation in answer.citations)


def test_datawindow_answer_says_external_and_no_table(answer_stack):
    snapshot, service, _validator, _connection = answer_stack
    answer = service.ask(snapshot, "¿Que tabla consulta d_tabla_primas_edad?")
    assert "externa" in answer.answer
    assert "no consulta" in answer.answer


def test_flow_is_exact(answer_stack):
    snapshot, service, _validator, _connection = answer_stack
    answer = service.ask(snapshot, "Explicame el flujo del boton Calcular")
    assert answer.flow[:3] == ["cb_calcular.clicked", "w_cotizador_mvp.of_calcular", "n_cotizador_reglas.of_calcular_cotizacion"]


def test_citation_rejects_source_drift(answer_stack, tmp_path):
    snapshot, _service, _validator, connection = answer_stack
    row = connection.execute("SELECT chunk_id FROM chunks WHERE snapshot_id=? AND member_name='of_limpiar'", (snapshot,)).fetchone()
    chunk = get_chunk(connection, row[0])
    copied_root = tmp_path / "copy"
    copied = copied_root / chunk.source_path
    copied.parent.mkdir(parents=True)
    copied.write_bytes((ROOT / chunk.source_path).read_bytes() + b"// drift\n")
    with pytest.raises(CitationValidationError):
        CitationValidator(copied_root, connection).build(chunk)
