from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rag_app.domain.models import Chunk, CodeDocMatch, DocumentChunk, Relation, SourceFile


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id TEXT PRIMARY KEY,
    git_commit TEXT NOT NULL,
    created_at TEXT NOT NULL,
    embed_provider TEXT NOT NULL,
    embed_model TEXT NOT NULL,
    chunk_count INTEGER NOT NULL,
    source_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS source_files (
    snapshot_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    pbl TEXT NOT NULL,
    object_name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    modified_at TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    encoding TEXT NOT NULL,
    line_ending TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    data_source TEXT,
    PRIMARY KEY (snapshot_id, source_path)
);
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    pbl TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    object_name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    member_type TEXT NOT NULL,
    member_name TEXT NOT NULL,
    control_name TEXT,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    raw_sha256 TEXT NOT NULL,
    text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    symbols_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_snapshot ON chunks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_chunks_member ON chunks(snapshot_id, member_name);
CREATE INDEX IF NOT EXISTS idx_chunks_object ON chunks(snapshot_id, object_name);
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT NOT NULL,
    source_chunk_id TEXT NOT NULL,
    source_symbol TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    target_symbol TEXT NOT NULL,
    target_chunk_id TEXT,
    evidence_line INTEGER
);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(snapshot_id, source_chunk_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(snapshot_id, target_chunk_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    chunk_id UNINDEXED,
    snapshot_id UNINDEXED,
    object_name,
    member_name,
    symbols,
    normalized_text,
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS doc_chunks (
    chunk_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    doc_title TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    section_title TEXT NOT NULL,
    section_level INTEGER NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    keywords_json TEXT NOT NULL,
    raw_sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_snapshot ON doc_chunks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_doc_approved ON doc_chunks(snapshot_id, approval_status);
CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    snapshot_id UNINDEXED,
    doc_id,
    section_title,
    keywords,
    normalized_text,
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS code_doc_matches (
    match_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    code_chunk_id TEXT NOT NULL,
    doc_chunk_id TEXT NOT NULL,
    match_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_match_code ON code_doc_matches(snapshot_id, code_chunk_id);
CREATE INDEX IF NOT EXISTS idx_match_doc ON code_doc_matches(snapshot_id, doc_chunk_id);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def chunk_from_row(row: sqlite3.Row) -> Chunk:
    return Chunk(
        chunk_id=row["chunk_id"], snapshot_id=row["snapshot_id"], pbl=row["pbl"],
        source_path=row["source_path"], source_sha256=row["source_sha256"],
        object_name=row["object_name"], object_type=row["object_type"],
        member_type=row["member_type"], member_name=row["member_name"],
        control_name=row["control_name"], start_line=row["start_line"],
        end_line=row["end_line"], raw_sha256=row["raw_sha256"], text=row["text"],
        normalized_text=row["normalized_text"], symbols=tuple(json.loads(row["symbols_json"])),
    )


def replace_snapshot(
    connection: sqlite3.Connection,
    sources: list[SourceFile],
    chunks: list[Chunk],
    relations: list[Relation],
    embed_provider: str,
    embed_model: str,
) -> None:
    if not sources:
        raise ValueError("No se puede guardar un snapshot sin fuentes")
    snapshot_id = sources[0].snapshot_id
    with connection:
        connection.execute("DELETE FROM chunks_fts WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute("DELETE FROM relations WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute("DELETE FROM chunks WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute("DELETE FROM source_files WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute("DELETE FROM snapshots WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute(
            "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
            (snapshot_id, sources[0].git_commit, sources[0].indexed_at, embed_provider, embed_model, len(chunks), len(sources)),
        )
        connection.executemany(
            "INSERT INTO source_files VALUES (:snapshot_id,:source_path,:pbl,:object_name,:object_type,:extension,:size_bytes,:modified_at,:sha256,:encoding,:line_ending,:indexed_at,:data_source)",
            [source.to_dict() for source in sources],
        )
        connection.executemany(
            """INSERT INTO chunks VALUES (
            :chunk_id,:snapshot_id,:pbl,:source_path,:source_sha256,:object_name,:object_type,
            :member_type,:member_name,:control_name,:start_line,:end_line,:raw_sha256,
            :text,:normalized_text,:symbols_json)""",
            [{**chunk.to_dict(), "symbols_json": json.dumps(chunk.symbols, ensure_ascii=False)} for chunk in chunks],
        )
        connection.executemany(
            "INSERT INTO chunks_fts VALUES (?, ?, ?, ?, ?, ?)",
            [(c.chunk_id, c.snapshot_id, c.object_name, c.member_name, " ".join(c.symbols), c.normalized_text) for c in chunks],
        )
        connection.executemany(
            """INSERT INTO relations(snapshot_id,source_chunk_id,source_symbol,relation_type,target_symbol,target_chunk_id,evidence_line)
            VALUES (:snapshot_id,:source_chunk_id,:source_symbol,:relation_type,:target_symbol,:target_chunk_id,:evidence_line)""",
            [relation.to_dict() for relation in relations],
        )


def list_snapshots(connection: sqlite3.Connection) -> list[dict[str, object]]:
    rows = connection.execute("SELECT * FROM snapshots ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]


def latest_snapshot_id(connection: sqlite3.Connection) -> str | None:
    row = connection.execute("SELECT snapshot_id FROM snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
    return row[0] if row else None


def get_chunk(connection: sqlite3.Connection, chunk_id: str) -> Chunk | None:
    row = connection.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
    return chunk_from_row(row) if row else None


def chunks_for_snapshot(connection: sqlite3.Connection, snapshot_id: str) -> list[Chunk]:
    return [chunk_from_row(row) for row in connection.execute("SELECT * FROM chunks WHERE snapshot_id = ? ORDER BY source_path,start_line", (snapshot_id,))]


def doc_chunk_from_row(row: sqlite3.Row) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=row["chunk_id"], snapshot_id=row["snapshot_id"],
        source_path=row["source_path"], doc_type=row["doc_type"],
        doc_id=row["doc_id"], doc_title=row["doc_title"],
        approval_status=row["approval_status"], section_title=row["section_title"],
        section_level=row["section_level"], start_line=row["start_line"],
        end_line=row["end_line"], text=row["text"],
        normalized_text=row["normalized_text"],
        keywords=tuple(json.loads(row["keywords_json"])),
        raw_sha256=row["raw_sha256"],
    )


def replace_doc_chunks(
    connection: sqlite3.Connection,
    snapshot_id: str,
    doc_chunks: list[DocumentChunk],
) -> None:
    with connection:
        connection.execute("DELETE FROM doc_chunks_fts WHERE snapshot_id = ?", (snapshot_id,))
        connection.execute("DELETE FROM doc_chunks WHERE snapshot_id = ?", (snapshot_id,))
        connection.executemany(
            """INSERT INTO doc_chunks VALUES (
            :chunk_id,:snapshot_id,:source_path,:doc_type,:doc_id,:doc_title,
            :approval_status,:section_title,:section_level,:start_line,:end_line,
            :text,:normalized_text,:keywords_json,:raw_sha256)""",
            [{**dc.to_dict(), "keywords_json": json.dumps(dc.keywords, ensure_ascii=False)} for dc in doc_chunks],
        )
        connection.executemany(
            "INSERT INTO doc_chunks_fts VALUES (?, ?, ?, ?, ?, ?)",
            [(dc.chunk_id, dc.snapshot_id, dc.doc_id, dc.section_title,
              " ".join(dc.keywords), dc.normalized_text) for dc in doc_chunks],
        )


def replace_matches(
    connection: sqlite3.Connection,
    snapshot_id: str,
    matches: list[CodeDocMatch],
) -> None:
    with connection:
        connection.execute("DELETE FROM code_doc_matches WHERE snapshot_id = ?", (snapshot_id,))
        connection.executemany(
            """INSERT INTO code_doc_matches VALUES (
            :match_id,:snapshot_id,:code_chunk_id,:doc_chunk_id,
            :match_type,:confidence,:evidence)""",
            [m.to_dict() for m in matches],
        )


def approved_doc_chunks(connection: sqlite3.Connection, snapshot_id: str) -> list[DocumentChunk]:
    rows = connection.execute(
        "SELECT * FROM doc_chunks WHERE snapshot_id = ? AND approval_status = 'approved' ORDER BY source_path, start_line",
        (snapshot_id,),
    ).fetchall()
    return [doc_chunk_from_row(row) for row in rows]


def all_doc_chunks(connection: sqlite3.Connection, snapshot_id: str) -> list[DocumentChunk]:
    rows = connection.execute(
        "SELECT * FROM doc_chunks WHERE snapshot_id = ? ORDER BY source_path, start_line",
        (snapshot_id,),
    ).fetchall()
    return [doc_chunk_from_row(row) for row in rows]


def matches_for_code(connection: sqlite3.Connection, snapshot_id: str, code_chunk_id: str) -> list[CodeDocMatch]:
    rows = connection.execute(
        "SELECT * FROM code_doc_matches WHERE snapshot_id = ? AND code_chunk_id = ? ORDER BY confidence DESC",
        (snapshot_id, code_chunk_id),
    ).fetchall()
    return [CodeDocMatch(**dict(row)) for row in rows]


def matches_for_snapshot(connection: sqlite3.Connection, snapshot_id: str) -> list[CodeDocMatch]:
    rows = connection.execute(
        "SELECT * FROM code_doc_matches WHERE snapshot_id = ? ORDER BY confidence DESC",
        (snapshot_id,),
    ).fetchall()
    return [CodeDocMatch(**dict(row)) for row in rows]
