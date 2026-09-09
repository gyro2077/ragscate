from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from rag_app.domain.models import SourceFile

from .common import TYPE_BY_EXTENSION, extract_object_name, read_source, sha256_bytes
from .discover import discover_sources


def git_commit(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unversioned"


def build_manifest(root: Path, corpus_dir: Path, pbl_name: str) -> tuple[str, list[SourceFile]]:
    paths = discover_sources(corpus_dir)
    if not paths:
        raise ValueError(f"No se encontraron fuentes SR* en {corpus_dir}")
    commit = git_commit(root)
    file_rows: list[tuple[Path, bytes, list[str], str, str, str]] = []
    combined = hashlib.sha256()
    for path in paths:
        raw, _text, lines, encoding, line_ending = read_source(path)
        digest = sha256_bytes(raw)
        relative = path.relative_to(root).as_posix()
        combined.update(relative.encode("utf-8"))
        combined.update(digest.encode("ascii"))
        file_rows.append((path, raw, lines, encoding, line_ending, digest))
    snapshot_id = f"{commit[:12]}-{combined.hexdigest()[:12]}"
    indexed_at = datetime.now(timezone.utc).isoformat()
    sources: list[SourceFile] = []
    for path, raw, lines, encoding, line_ending, digest in file_rows:
        extension = path.suffix.lower()
        stat = path.stat()
        sources.append(SourceFile(
            snapshot_id=snapshot_id,
            git_commit=commit,
            pbl=pbl_name,
            source_path=path.relative_to(root).as_posix(),
            object_name=extract_object_name(lines, path),
            object_type=TYPE_BY_EXTENSION.get(extension, "unknown"),
            extension=extension,
            size_bytes=len(raw),
            modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            sha256=digest,
            encoding=encoding,
            line_ending=line_ending,
            indexed_at=indexed_at,
        ))
    return snapshot_id, sources


def write_manifest(path: Path, sources: list[SourceFile]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True) + "\n" for item in sources)
    path.write_text(content, encoding="utf-8")
