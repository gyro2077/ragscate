from __future__ import annotations

import re
import sqlite3
from dataclasses import replace
from pathlib import Path

import numpy as np

from rag_app.domain.models import Chunk, SearchHit
from rag_app.storage.database import chunk_from_row, chunks_for_snapshot

from .lexical import enrich_query, expansion_symbols, lexical_search
from .semantic import SemanticEncoder, load_embeddings


IDENTIFIER = re.compile(r"\b[A-Za-z][A-Za-z0-9_]+\b")


class HybridRetriever:
    def __init__(self, connection: sqlite3.Connection, data_dir: Path, encoder: SemanticEncoder) -> None:
        self.connection = connection
        self.data_dir = data_dir
        self.encoder = encoder

    def _exact_symbols(self, snapshot_id: str, question: str) -> set[str]:
        identifiers = {item.lower() for item in IDENTIFIER.findall(question) if "_" in item}
        if not identifiers:
            return set()
        known: set[str] = set()
        for chunk in chunks_for_snapshot(self.connection, snapshot_id):
            candidates = {chunk.object_name.lower(), chunk.member_name.lower(), *(s.lower() for s in chunk.symbols)}
            known.update(identifiers & candidates)
        return known

    def search(
        self,
        snapshot_id: str,
        question: str,
        top_k: int = 8,
        object_type: str | None = None,
        member_type: str | None = None,
        pbl: str | None = None,
        expand_relations: bool = True,
    ) -> list[SearchHit]:
        lexical = lexical_search(self.connection, snapshot_id, question, max(top_k * 3, 20))
        matrix, embedding_ids, meta = load_embeddings(self.data_dir / "snapshots" / snapshot_id)
        if meta["provider"] != self.encoder.provider_name or meta["model"] != self.encoder.model_name:
            raise ValueError("El codificador de consulta no coincide con el snapshot indexado")
        query_vector = self.encoder.encode_query(enrich_query(question))
        similarities = matrix @ query_vector
        semantic_order = np.argsort(-similarities)[:max(top_k * 3, 20)]

        chunks = {chunk.chunk_id: chunk for chunk in chunks_for_snapshot(self.connection, snapshot_id)}
        score: dict[str, float] = {}
        lex_rank: dict[str, int] = {}
        sem_rank: dict[str, int] = {}
        for rank, (chunk, _bm25) in enumerate(lexical, 1):
            score[chunk.chunk_id] = score.get(chunk.chunk_id, 0.0) + 1.0 / (60 + rank)
            lex_rank[chunk.chunk_id] = rank
        for rank, index in enumerate(semantic_order, 1):
            chunk_id = embedding_ids[int(index)]
            score[chunk_id] = score.get(chunk_id, 0.0) + 1.0 / (60 + rank)
            sem_rank[chunk_id] = rank

        exact_symbols = self._exact_symbols(snapshot_id, question)
        exact_chunks: set[str] = set()
        if exact_symbols:
            for chunk in chunks.values():
                direct = {chunk.member_name.lower(), *(s.lower() for s in chunk.symbols)}
                if direct & exact_symbols:
                    score[chunk.chunk_id] = score.get(chunk.chunk_id, 0.0) + 1.0
                    exact_chunks.add(chunk.chunk_id)
                elif chunk.object_name.lower() in exact_symbols:
                    score[chunk.chunk_id] = score.get(chunk.chunk_id, 0.0) + 0.08
                    exact_chunks.add(chunk.chunk_id)

        # Las expansiones son alias de dominio declarados (por ejemplo,
        # "impuesto" -> of_calcular_cotizacion). Tienen menos peso que un
        # simbolo escrito literalmente por el usuario, pero evitan que textos
        # de controles repetidos desplacen a la implementacion del simbolo.
        for position, symbol in enumerate(expansion_symbols(question)):
            weight = max(0.12, 0.24 - position * 0.03)
            for chunk in chunks.values():
                candidates = {chunk.member_name.lower(), *(s.lower() for s in chunk.symbols)}
                if symbol in candidates:
                    score[chunk.chunk_id] = score.get(chunk.chunk_id, 0.0) + weight

        def allowed(chunk: Chunk) -> bool:
            return (
                (object_type is None or chunk.object_type == object_type)
                and (member_type is None or chunk.member_type == member_type)
                and (pbl is None or chunk.pbl == pbl)
            )

        ordered = [chunk_id for chunk_id, _ in sorted(score.items(), key=lambda item: (-item[1], chunks[item[0]].source_path, chunks[item[0]].start_line)) if allowed(chunks[chunk_id])]
        initial = ordered[:top_k]
        expanded_ids: set[str] = set()
        if expand_relations and initial:
            placeholders = ",".join("?" for _ in initial)
            rows = self.connection.execute(
                f"""SELECT source_chunk_id,target_chunk_id FROM relations
                WHERE snapshot_id=? AND ((source_chunk_id IN ({placeholders})) OR (target_chunk_id IN ({placeholders})))""",
                (snapshot_id, *initial, *initial),
            ).fetchall()
            for row in rows:
                for candidate in (row["source_chunk_id"], row["target_chunk_id"]):
                    if candidate and candidate not in score and candidate in chunks and allowed(chunks[candidate]):
                        score[candidate] = min(score[item] for item in initial) * 0.5
                        expanded_ids.add(candidate)
            ordered = [chunk_id for chunk_id, _ in sorted(score.items(), key=lambda item: (-item[1], chunks[item[0]].source_path, chunks[item[0]].start_line)) if allowed(chunks[chunk_id])]

        return [SearchHit(
            chunk=chunks[chunk_id], score=score[chunk_id],
            lexical_rank=lex_rank.get(chunk_id), semantic_rank=sem_rank.get(chunk_id),
            exact_symbol=chunk_id in exact_chunks, expanded=chunk_id in expanded_ids,
        ) for chunk_id in ordered[:top_k]]

    def unknown_identifiers(self, snapshot_id: str, question: str) -> list[str]:
        requested = {item.lower() for item in IDENTIFIER.findall(question) if "_" in item}
        if not requested:
            return []
        known: set[str] = set()
        for chunk in chunks_for_snapshot(self.connection, snapshot_id):
            known.update((chunk.object_name.lower(), chunk.member_name.lower(), *(s.lower() for s in chunk.symbols)))
        return sorted(requested - known)
