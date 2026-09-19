from __future__ import annotations

from pathlib import Path

from .common import SUPPORTED_EXTENSIONS


def discover_sources(corpus_dir: Path, pdf_dir: Path | None = None) -> list[Path]:
    if not corpus_dir.is_dir():
        raise FileNotFoundError(f"No existe el corpus: {corpus_dir}")
    
    paths = [
        path for path in corpus_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    
    if pdf_dir and pdf_dir.is_dir():
        paths.extend(
            path for path in pdf_dir.rglob("*")
            if path.is_file() and path.suffix.lower() == ".pdf"
        )
        
    return sorted(paths)
