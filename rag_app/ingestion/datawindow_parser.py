from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from rag_app.domain.models import Chunk, ParsedSource, Relation, SourceFile

from .common import make_chunk_id, normalize_text, read_source, sha256_text


def _make_chunk(source: SourceFile, lines: list[str], member_type: str, member_name: str, start: int, end: int, symbols: tuple[str, ...]) -> Chunk:
    text = "\n".join(lines[start:end + 1])
    raw_hash = sha256_text(text)
    start_line, end_line = start + 1, end + 1
    return Chunk(
        chunk_id=make_chunk_id(source.snapshot_id, source.source_path, member_type, member_name, start_line, end_line, raw_hash),
        snapshot_id=source.snapshot_id,
        pbl=source.pbl,
        source_path=source.source_path,
        source_sha256=source.sha256,
        object_name=source.object_name,
        object_type="datawindow",
        member_type=member_type,
        member_name=member_name,
        control_name=None,
        start_line=start_line,
        end_line=end_line,
        raw_sha256=raw_hash,
        text=text,
        normalized_text=normalize_text(text),
        symbols=symbols,
    )


def parse_datawindow(root: Path, source: SourceFile) -> ParsedSource:
    _raw, text, lines, _encoding, _ending = read_source(root / source.source_path)
    lower = text.lower()
    has_retrieve = "retrieve=" in lower or "pbselect(" in lower or "procedure=" in lower
    data_source = "retrieval" if has_retrieve else "external"
    source = replace(source, data_source=data_source)
    column_names = tuple(dict.fromkeys(re.findall(r"\bname=([A-Za-z_]\w*)\s+dbname=", text, re.I)))

    definition_start = next((i for i, line in enumerate(lines) if line.lower().startswith("release ")), 0)
    definition = _make_chunk(source, lines, "datawindow_definition", source.object_name, definition_start, len(lines) - 1, (source.object_name, data_source, *column_names))

    table_start = next((i for i, line in enumerate(lines) if line.lstrip().lower().startswith("table(")), definition_start)
    table_end = table_start
    depth = 0
    for i in range(table_start, len(lines)):
        depth += lines[i].count("(") - lines[i].count(")")
        table_end = i
        if depth <= 0 and i > table_start:
            break
    columns = _make_chunk(source, lines, "datawindow_columns", f"{source.object_name}.columns", table_start, table_end, column_names)

    presentation_start = min(table_end + 1, len(lines) - 1)
    presentation = _make_chunk(source, lines, "datawindow_presentation", f"{source.object_name}.presentation", presentation_start, len(lines) - 1, column_names)

    relations = [
        Relation(source.snapshot_id, definition.chunk_id, source.object_name, "contains", columns.member_name, columns.chunk_id, table_start + 1),
        Relation(source.snapshot_id, definition.chunk_id, source.object_name, "contains", presentation.member_name, presentation.chunk_id, presentation_start + 1),
    ]
    return ParsedSource(source=source, chunks=[definition, columns, presentation], relations=relations)
