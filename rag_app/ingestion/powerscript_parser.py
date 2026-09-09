from __future__ import annotations

import re
from pathlib import Path

from rag_app.domain.models import Chunk, ParsedSource, Relation, SourceFile

from .common import make_chunk_id, normalize_text, read_source, sha256_text


START_ROUTINE = re.compile(r"^\s*public\s+(function|subroutine)\s+(?:[\w()]+\s+)?([A-Za-z_]\w*)\s*\(", re.I)
START_EVENT = re.compile(r"^\s*event\s+([A-Za-z_]\w*)\s*;", re.I)
START_CONTROL = re.compile(r"^\s*type\s+([A-Za-z_]\w*)\s+from\s+([A-Za-z_]\w*)\s+within\s+([A-Za-z_]\w*)", re.I)
GLOBAL_TYPE = re.compile(r"^\s*global\s+type\s+([A-Za-z_]\w*)\s+from\s+([A-Za-z_]\w*)", re.I)


def _find_end(lines: list[str], start_index: int, end_pattern: re.Pattern[str]) -> int:
    for index in range(start_index + 1, len(lines)):
        if end_pattern.match(lines[index]):
            return index
    return len(lines) - 1


def _chunk(source: SourceFile, lines: list[str], member_type: str, member_name: str, start_index: int, end_index: int, control_name: str | None = None, symbols: tuple[str, ...] = ()) -> Chunk:
    text = "\n".join(lines[start_index:end_index + 1])
    raw_hash = sha256_text(text)
    start_line, end_line = start_index + 1, end_index + 1
    chunk_id = make_chunk_id(source.snapshot_id, source.source_path, member_type, member_name, start_line, end_line, raw_hash)
    return Chunk(
        chunk_id=chunk_id,
        snapshot_id=source.snapshot_id,
        pbl=source.pbl,
        source_path=source.source_path,
        source_sha256=source.sha256,
        object_name=source.object_name,
        object_type=source.object_type,
        member_type=member_type,
        member_name=member_name,
        control_name=control_name,
        start_line=start_line,
        end_line=end_line,
        raw_sha256=raw_hash,
        text=text,
        normalized_text=normalize_text(text),
        symbols=tuple(dict.fromkeys((member_name, *symbols))),
    )


def parse_powerscript(root: Path, source: SourceFile) -> ParsedSource:
    path = root / source.source_path
    _raw, _text, lines, _encoding, _ending = read_source(path)
    chunks: list[Chunk] = []
    relations: list[Relation] = []

    if source.extension == ".srs":
        fields = tuple(
            match.group(1) for line in lines
            if (match := re.match(r"^\s*(?:boolean|integer|long|decimal|string|date|datetime)\s+([A-Za-z_]\w*)\s*$", line, re.I))
        )
        item = _chunk(source, lines, "structure", source.object_name, 0, len(lines) - 1, symbols=fields)
        return ParsedSource(source=source, chunks=[item], relations=[])

    forward_end = -1
    for idx, line in enumerate(lines):
        if line.strip().lower() == "end forward":
            forward_end = idx
            break

    ancestor = ""
    for idx, line in enumerate(lines):
        match = GLOBAL_TYPE.match(line)
        if match and match.group(1).lower() == source.object_name.lower():
            ancestor = match.group(2)
            if idx > forward_end:
                break
    object_end = next((idx - 1 for idx, line in enumerate(lines) if idx > forward_end and line.strip().lower() == "type variables"), min(len(lines) - 1, max(forward_end + 5, 0)))
    chunks.append(_chunk(source, lines, "object", source.object_name, 0, max(0, object_end), symbols=(ancestor,) if ancestor else ()))

    if ancestor:
        relations.append(Relation(source.snapshot_id, chunks[0].chunk_id, source.object_name, "inherits_from", ancestor, evidence_line=chunks[0].start_line))

    idx = max(forward_end + 1, 0)
    last_control: str | None = None
    while idx < len(lines):
        lowered = lines[idx].strip().lower()
        if lowered == "type variables":
            end = _find_end(lines, idx, re.compile(r"^\s*end\s+variables\s*$", re.I))
            item = _chunk(source, lines, "variables", "variables", idx, end)
            chunks.append(item)
            relations.append(Relation(source.snapshot_id, item.chunk_id, source.object_name, "contains", "variables", evidence_line=idx + 1))
            idx = end + 1
            continue

        routine = START_ROUTINE.match(lines[idx])
        if routine and idx > forward_end:
            kind, name = routine.group(1).lower(), routine.group(2)
            end = _find_end(lines, idx, re.compile(rf"^\s*end\s+{kind}\s*$", re.I))
            item = _chunk(source, lines, kind, name, idx, end)
            chunks.append(item)
            relations.append(Relation(source.snapshot_id, item.chunk_id, source.object_name, "contains", name, evidence_line=idx + 1))
            last_control = None
            idx = end + 1
            continue

        control = START_CONTROL.match(lines[idx])
        if control and idx > forward_end:
            name, control_type, _owner = control.groups()
            end = _find_end(lines, idx, re.compile(r"^\s*end\s+type\s*$", re.I))
            item = _chunk(source, lines, "control", name, idx, end, control_name=name, symbols=(control_type,))
            chunks.append(item)
            relations.append(Relation(source.snapshot_id, item.chunk_id, source.object_name, "contains", name, evidence_line=idx + 1))
            last_control = name
            idx = end + 1
            continue

        event = START_EVENT.match(lines[idx])
        if event:
            event_name = event.group(1)
            end = _find_end(lines, idx, re.compile(r"^\s*end\s+event\s*$", re.I))
            member_name = f"{last_control}.{event_name}" if last_control else event_name
            item = _chunk(source, lines, "event", member_name, idx, end, control_name=last_control, symbols=(event_name,))
            chunks.append(item)
            relations.append(Relation(source.snapshot_id, item.chunk_id, source.object_name, "contains", member_name, evidence_line=idx + 1))
            idx = end + 1
            continue
        idx += 1

    return ParsedSource(source=source, chunks=chunks, relations=relations)
