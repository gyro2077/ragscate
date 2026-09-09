from __future__ import annotations

import re
from pathlib import Path

from rag_app.domain.models import Chunk, ParsedSource, Relation, SourceFile

from .datawindow_parser import parse_datawindow
from .powerscript_parser import parse_powerscript


CALL_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
QUALIFIED_CALL_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\s*\(")
DATAOBJECT_PATTERN = re.compile(r"\bdataobject\s*=\s*[\"']([A-Za-z_]\w*)[\"']", re.I)
OPEN_PATTERN = re.compile(r"\bopen\s*\(\s*([A-Za-z_]\w*)", re.I)
SQL_READ_PATTERN = re.compile(r"\bfrom\s+([A-Za-z_][\w.]*)", re.I)
SQL_WRITE_PATTERN = re.compile(r"\b(?:update|insert\s+into|delete\s+from)\s+([A-Za-z_][\w.]*)", re.I)

IGNORED_CALLS = {
    "if", "for", "choose", "case", "return", "string", "integer", "dec", "decimal",
    "round", "trim", "lower", "upper", "isnumber", "isvalid", "messagebox", "create",
    "destroy", "min", "max",
}


def parse_all(root: Path, sources: list[SourceFile]) -> tuple[list[SourceFile], list[Chunk], list[Relation]]:
    parsed: list[ParsedSource] = []
    for source in sources:
        if source.extension == ".srd":
            parsed.append(parse_datawindow(root, source))
        else:
            parsed.append(parse_powerscript(root, source))

    final_sources = [item.source for item in parsed]
    chunks = [chunk for item in parsed for chunk in item.chunks]
    relations = [relation for item in parsed for relation in item.relations]

    symbol_to_chunk: dict[str, str] = {}
    for chunk in chunks:
        symbol_to_chunk.setdefault(chunk.object_name.lower(), chunk.chunk_id)
        symbol_to_chunk.setdefault(chunk.member_name.lower(), chunk.chunk_id)
        for symbol in chunk.symbols:
            symbol_to_chunk.setdefault(symbol.lower(), chunk.chunk_id)

    known_symbols = set(symbol_to_chunk)
    for chunk in chunks:
        lower_text = chunk.text.lower()
        found: set[tuple[str, str, int | None]] = set()
        for qualified in QUALIFIED_CALL_PATTERN.finditer(chunk.text):
            target = qualified.group(2)
            if target.lower() in known_symbols:
                line = chunk.start_line + chunk.text[:qualified.start()].count("\n")
                found.add(("calls", target, line))
        for call in CALL_PATTERN.finditer(chunk.text):
            target = call.group(1)
            key = target.lower()
            if key in known_symbols and key not in IGNORED_CALLS and key != chunk.member_name.lower():
                line = chunk.start_line + chunk.text[:call.start()].count("\n")
                found.add(("calls", target, line))
        for match in OPEN_PATTERN.finditer(chunk.text):
            target = match.group(1)
            line = chunk.start_line + chunk.text[:match.start()].count("\n")
            found.add(("opens", target, line))
        for match in DATAOBJECT_PATTERN.finditer(chunk.text):
            target = match.group(1)
            line = chunk.start_line + chunk.text[:match.start()].count("\n")
            found.add(("uses_datawindow", target, line))
        if any(token in lower_text for token in ("select ", "update ", "insert ", "delete ")):
            for match in SQL_READ_PATTERN.finditer(chunk.text):
                found.add(("reads_table", match.group(1), chunk.start_line + chunk.text[:match.start()].count("\n")))
            for match in SQL_WRITE_PATTERN.finditer(chunk.text):
                found.add(("writes_table", match.group(1), chunk.start_line + chunk.text[:match.start()].count("\n")))
        for relation_type, target, line in sorted(found):
            relations.append(Relation(
                snapshot_id=chunk.snapshot_id,
                source_chunk_id=chunk.chunk_id,
                source_symbol=chunk.member_name,
                relation_type=relation_type,
                target_symbol=target,
                target_chunk_id=symbol_to_chunk.get(target.lower()),
                evidence_line=line,
            ))
    return final_sources, chunks, relations
