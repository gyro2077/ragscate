from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from rag_app.domain.models import Chunk, Relation, SourceFile


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
