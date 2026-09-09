from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from rag_app.domain.models import Chunk, Citation


class CitationValidationError(ValueError):
    """Raised when a citation cannot be reconstructed from the immutable source."""


class CitationValidator:
    def __init__(self, root: Path, connection: sqlite3.Connection) -> None:
        self.root = root.resolve()
        self.connection = connection

    def build(self, chunk: Chunk, start_line: int | None = None, end_line: int | None = None) -> Citation:
        start = start_line or chunk.start_line
        end = end_line or chunk.end_line
        if start < chunk.start_line or end > chunk.end_line or start > end:
            raise CitationValidationError("El rango solicitado queda fuera del fragmento indexado")
        row = self.connection.execute(
            "SELECT sha256,encoding FROM source_files WHERE snapshot_id=? AND source_path=?",
            (chunk.snapshot_id, chunk.source_path),
        ).fetchone()
        if row is None:
            raise CitationValidationError("La fuente no pertenece al snapshot")
        source = (self.root / chunk.source_path).resolve()
        if self.root not in source.parents:
            raise CitationValidationError("Ruta de fuente fuera del repositorio")
        raw = source.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != row["sha256"] or actual_hash != chunk.source_sha256:
            raise CitationValidationError(f"La fuente cambio desde el snapshot: {chunk.source_path}")
        text = raw.decode(row["encoding"])
        lines = text.splitlines()
        if end > len(lines):
            raise CitationValidationError("La cita apunta fuera de las lineas existentes")
        snippet = "\n".join(lines[start - 1:end])
        indexed_lines = "\n".join(lines[chunk.start_line - 1:chunk.end_line])
        if hashlib.sha256(indexed_lines.encode("utf-8")).hexdigest() != chunk.raw_sha256:
            raise CitationValidationError("El fragmento ya no reproduce el texto indexado")
        return Citation(
            chunk_id=chunk.chunk_id, pbl=chunk.pbl, file=chunk.source_path,
            object=chunk.object_name, member=chunk.member_name,
            start_line=start, end_line=end, snippet=snippet, snapshot_id=chunk.snapshot_id,
        )

    def validate(self, citation: Citation) -> bool:
        row = self.connection.execute("SELECT * FROM chunks WHERE chunk_id=?", (citation.chunk_id,)).fetchone()
        if row is None:
            return False
        from rag_app.storage.database import chunk_from_row
        try:
            rebuilt = self.build(chunk_from_row(row), citation.start_line, citation.end_line)
        except (OSError, UnicodeError, CitationValidationError):
            return False
        return rebuilt.snippet == citation.snippet and rebuilt.snapshot_id == citation.snapshot_id
