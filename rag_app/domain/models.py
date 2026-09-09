from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ObjectType = Literal["application", "window", "userobject", "structure", "datawindow", "unknown"]
MemberType = Literal[
    "object",
    "variables",
    "function",
    "subroutine",
    "event",
    "control",
    "structure",
    "datawindow_definition",
    "datawindow_columns",
    "datawindow_presentation",
]


@dataclass(frozen=True)
class SourceFile:
    snapshot_id: str
    git_commit: str
    pbl: str
    source_path: str
    object_name: str
    object_type: ObjectType
    extension: str
    size_bytes: int
    modified_at: str
    sha256: str
    encoding: str
    line_ending: str
    indexed_at: str
    data_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    snapshot_id: str
    pbl: str
    source_path: str
    source_sha256: str
    object_name: str
    object_type: ObjectType
    member_type: MemberType
    member_name: str
    control_name: str | None
    start_line: int
    end_line: int
    raw_sha256: str
    text: str
    normalized_text: str
    symbols: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["symbols"] = list(self.symbols)
        return result


@dataclass(frozen=True)
class Relation:
    snapshot_id: str
    source_chunk_id: str
    source_symbol: str
    relation_type: str
    target_symbol: str
    target_chunk_id: str | None = None
    evidence_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedSource:
    source: SourceFile
    chunks: list[Chunk]
    relations: list[Relation]


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float
    lexical_rank: int | None = None
    semantic_rank: int | None = None
    exact_symbol: bool = False
    expanded: bool = False


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    pbl: str
    file: str
    object: str
    member: str
    start_line: int
    end_line: int
    snippet: str
    snapshot_id: str


@dataclass(frozen=True)
class Answer:
    classification: Literal["Comprobado", "Inferido", "No localizado"]
    answer: str
    flow: list[str]
    citations: list[Citation]
    possible_change_locations: list[str]
    risks: list[str]
    recommended_tests: list[str]

