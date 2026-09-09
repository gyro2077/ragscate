from __future__ import annotations

import hashlib
from pathlib import Path

from rag_app.config import ROOT
from rag_app.ingestion.chunker import parse_all
from rag_app.ingestion.common import sha256_text
from rag_app.ingestion.manifest import build_manifest


def _parsed():
    snapshot, sources = build_manifest(ROOT, ROOT / "pb-src", "cotizador_mvp.pbl")
    final_sources, chunks, relations = parse_all(ROOT, sources)
    return snapshot, final_sources, chunks, relations


def test_manifest_discovers_five_sources_and_is_stable():
    first, sources, _chunks, _relations = _parsed()
    second, _ = build_manifest(ROOT, ROOT / "pb-src", "cotizador_mvp.pbl")
    assert first == second
    assert len(sources) == 5
    assert {source.object_type for source in sources} == {"application", "window", "userobject", "structure", "datawindow"}


def test_every_chunk_reconstructs_exact_lines_and_hash():
    _snapshot, _sources, chunks, _relations = _parsed()
    for chunk in chunks:
        lines = (ROOT / chunk.source_path).read_bytes().decode("ascii").splitlines()
        reconstructed = "\n".join(lines[chunk.start_line - 1:chunk.end_line])
        assert reconstructed == chunk.text
        assert sha256_text(reconstructed) == chunk.raw_sha256
        assert chunk.start_line <= chunk.end_line


def test_required_members_and_exact_boundaries_are_detected():
    _snapshot, _sources, chunks, _relations = _parsed()
    by_member = {chunk.member_name: chunk for chunk in chunks}
    assert by_member["of_calcular_cotizacion"].start_line == 60
    assert by_member["of_calcular_cotizacion"].end_line == 133
    assert by_member["cb_calcular.clicked"].start_line == 576
    assert by_member["cb_calcular.clicked"].end_line == 580
    assert by_member["of_limpiar"].start_line == 289
    assert by_member["open"].object_name in {"cotizador_mvp", "w_cotizador_mvp"}


def test_datawindow_uses_dedicated_external_parser():
    _snapshot, sources, chunks, _relations = _parsed()
    datawindow = next(source for source in sources if source.object_type == "datawindow")
    assert datawindow.data_source == "external"
    dw_chunks = [chunk for chunk in chunks if chunk.object_name == "d_tabla_primas_edad"]
    assert {chunk.member_type for chunk in dw_chunks} == {
        "datawindow_definition", "datawindow_columns", "datawindow_presentation"
    }
    columns = next(chunk for chunk in dw_chunks if chunk.member_type == "datawindow_columns")
    assert {"rango_edad", "factor_edad", "prima_anual", "cuota_mensual", "condicion"}.issubset(columns.symbols)


def test_structure_is_a_complete_semantic_chunk():
    _snapshot, _sources, chunks, _relations = _parsed()
    structure = next(chunk for chunk in chunks if chunk.member_type == "structure")
    assert structure.member_name == "str_resultado_cotizacion"
    assert (structure.start_line, structure.end_line) == (1, 23)
    assert "prima_anual" in structure.symbols
    assert "motivos_autorizacion" in structure.symbols


def test_flow_relations_are_extracted():
    _snapshot, _sources, _chunks, relations = _parsed()
    triples = {(r.source_symbol.lower(), r.relation_type, r.target_symbol.lower()) for r in relations}
    assert ("cb_calcular.clicked", "calls", "of_calcular") in triples
    assert ("of_calcular", "calls", "of_calcular_cotizacion") in triples
    assert ("open", "opens", "w_cotizador_mvp") in triples
    assert any(kind == "uses_datawindow" and target == "d_tabla_primas_edad" for _source, kind, target in triples)


def test_powerbuilder_corpus_hashes_remain_expected():
    expected = {
        "cotizador_mvp.sra": "d488f450efc6c113ce591a75c1ab47a6e9c1f5a669dd8253621576868b9eda05",
        "d_tabla_primas_edad.srd": "083002673659043e50399a84be77394ad454f473db01859d9f14356d1825a664",
        "n_cotizador_reglas.sru": "b5a8d8aaed5d8b148851cc851d620f6495495ce4cbd6daa6eab91e4861333a38",
        "str_resultado_cotizacion.srs": "21b65ca12b1783728969d6a2c1a6ef67fa42fec17e938a4654d4630e3fabd0fe",
        "w_cotizador_mvp.srw": "8143dba3564c8f677a9fa4090af1c6eb5d104daf2bc9519faa9bdcd6099906a9",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ROOT / "pb-src" / name).read_bytes()).hexdigest() == digest
