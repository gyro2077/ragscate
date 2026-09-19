from __future__ import annotations
from pathlib import Path
import pymupdf as fitz  # PyMuPDF (fitz alias deprecated)

from rag_app.domain.models import Chunk, ParsedSource, SourceFile
from rag_app.ingestion.common import make_chunk_id, normalize_text, sha256_text
from rag_app.ingestion.validators import is_pdf_signed, UnsignedDocumentError

import re

def parse_signed_business_rules(root: Path, source: SourceFile) -> ParsedSource:
    path = root / source.source_path
    
    if not is_pdf_signed(path):
        print(f"\n⚠️  RECHAZADO: El documento '{source.source_path}' no contiene firma electrónica válida. Ignorando...\n")
        return ParsedSource(source=source, chunks=[], relations=[])
        
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
        
    lines = text.splitlines()
    if not lines:
        return ParsedSource(source=source, chunks=[], relations=[])
        
    chunks: list[Chunk] = []
    rule_pattern = re.compile(r"^\d{2}\. ")
    
    current_lines = []
    start_line = 1
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # When hitting a new rule, save the previous block as a chunk
        if rule_pattern.match(line) and current_lines:
            chunk_text = "\n".join(current_lines)
            raw_hash = sha256_text(chunk_text)
            
            chunk_id = make_chunk_id(
                source.snapshot_id, source.source_path, "rule_block", f"Lines_{start_line}_{line_num - 1}", 
                start_line, line_num - 1, raw_hash
            )
            
            chunks.append(Chunk(
                chunk_id=chunk_id, snapshot_id=source.snapshot_id, pbl=source.pbl,
                source_path=source.source_path, source_sha256=source.sha256,
                object_name=source.object_name, object_type="business_rule",
                member_type="rule_block", member_name=f"Lines_{start_line}_{line_num - 1}",
                control_name=None, start_line=start_line, end_line=line_num - 1,
                raw_sha256=raw_hash, text=chunk_text, normalized_text=normalize_text(chunk_text), symbols=()
            ))
            
            current_lines = [line]
            start_line = line_num
        else:
            current_lines.append(line)
            
    # Save the last block
    if current_lines:
        chunk_text = "\n".join(current_lines)
        raw_hash = sha256_text(chunk_text)
        chunk_id = make_chunk_id(
            source.snapshot_id, source.source_path, "rule_block", f"Lines_{start_line}_{len(lines)}", 
            start_line, len(lines), raw_hash
        )
        chunks.append(Chunk(
            chunk_id=chunk_id, snapshot_id=source.snapshot_id, pbl=source.pbl,
            source_path=source.source_path, source_sha256=source.sha256,
            object_name=source.object_name, object_type="business_rule",
            member_type="rule_block", member_name=f"Lines_{start_line}_{len(lines)}",
            control_name=None, start_line=start_line, end_line=len(lines),
            raw_sha256=raw_hash, text=chunk_text, normalized_text=normalize_text(chunk_text), symbols=()
        ))
        
    return ParsedSource(source=source, chunks=chunks, relations=[])
