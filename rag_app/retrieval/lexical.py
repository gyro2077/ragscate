from __future__ import annotations

import re
import sqlite3

from rag_app.domain.models import Chunk
from rag_app.ingestion.common import normalize_text
from rag_app.storage.database import chunk_from_row


STOPWORDS = {"a", "al", "como", "de", "del", "donde", "el", "en", "es", "la", "las", "lo", "los", "por", "que", "se", "un", "una", "y"}
EXPANSIONS = {
    "prima anual": ["of_calcular_cotizacion", "prima_anual", "subtotal", "impuesto"],
    "boton calcular": ["cb_calcular.clicked", "of_calcular", "of_calcular_cotizacion", "cb_calcular"],
    "flujo calcular": ["cb_calcular.clicked", "of_calcular", "of_calcular_cotizacion"],
    "validaciones edad": ["of_leer_entradas", "edad", "isnumber"],
    "validaciones": ["of_leer_entradas", "of_factor_edad"],
    "aplican edad": ["of_leer_entradas", "edad", "isnumber"],
    "requieren autorizacion": ["motivos_autorizacion", "of_calcular_cotizacion", "alto"],
    "requiere autorizacion": ["motivos_autorizacion", "of_calcular_cotizacion", "alto"],
    "cambiaria impuesto": ["of_calcular_cotizacion", "idc_impuesto_porcentaje", "impuesto"],
    "impuesto": ["of_calcular_cotizacion", "idc_impuesto_porcentaje"],
    "agregar una categoria": ["of_factor_categoria", "ddlb_categoria", "additem"],
    "tabla consulta": ["d_tabla_primas_edad", "datawindow", "of_actualizar_tabla", "external"],
    "cuota mensual": ["of_calcular_cotizacion", "cuota_mensual"],
    "hace limpiar": ["of_limpiar", "cb_limpiar", "clicked"],
}


def expansion_symbols(question: str) -> list[str]:
    normalized = normalize_text(question)
    result: list[str] = []
    for phrase, values in EXPANSIONS.items():
        if phrase in normalized:
            result.extend(values)
    return list(dict.fromkeys(item.lower() for item in result))


def enrich_query(question: str) -> str:
    normalized = normalize_text(question)
    additions = expansion_symbols(question)
    return " ".join((question, *additions))


def query_tokens(question: str) -> list[str]:
    raw_identifiers = re.findall(r"[A-Za-z][A-Za-z0-9_]+", question)
    words = re.findall(r"[a-z0-9_]+", normalize_text(enrich_query(question)))
    result: list[str] = []
    for token in [*raw_identifiers, *words]:
        lowered = token.lower()
        if len(lowered) >= 2 and lowered not in STOPWORDS and lowered not in result:
            result.append(lowered)
    return result


def lexical_search(connection: sqlite3.Connection, snapshot_id: str, question: str, limit: int = 20) -> list[tuple[Chunk, float]]:
    tokens = query_tokens(question)
    if not tokens:
        return []
    match = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
    rows = connection.execute(
        """SELECT c.*, bm25(chunks_fts, 0.0, 0.0, 8.0, 12.0, 10.0, 1.0) AS lexical_score
        FROM chunks_fts JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
        WHERE chunks_fts MATCH ? AND chunks_fts.snapshot_id = ?
        ORDER BY lexical_score LIMIT ?""",
        (match, snapshot_id, limit),
    ).fetchall()
    return [(chunk_from_row(row), float(row["lexical_score"])) for row in rows]
