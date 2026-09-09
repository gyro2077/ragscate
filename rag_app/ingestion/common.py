from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path


SUPPORTED_EXTENSIONS = {".sra", ".srw", ".sru", ".srs", ".srd"}
TYPE_BY_EXTENSION = {
    ".sra": "application",
    ".srw": "window",
    ".sru": "userobject",
    ".srs": "structure",
    ".srd": "datawindow",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    ascii_text = ascii_text.lower().replace("_", " ")
    return re.sub(r"\s+", " ", ascii_text).strip()


def read_source(path: Path) -> tuple[bytes, str, list[str], str, str]:
    raw = path.read_bytes()
    try:
        text = raw.decode("ascii")
        encoding = "ascii"
    except UnicodeDecodeError:
        text = raw.decode("utf-8")
        encoding = "utf-8"
    if b"\r\n" in raw:
        line_ending = "CRLF"
    elif b"\n" in raw:
        line_ending = "LF"
    else:
        line_ending = "NONE"
    return raw, text, text.splitlines(), encoding, line_ending


def extract_object_name(lines: list[str], path: Path) -> str:
    for line in lines:
        match = re.match(r"\s*global\s+type\s+([A-Za-z_][\w]*)\s+from\s+", line, re.I)
        if match:
            return match.group(1)
    header = re.match(r"\$PBExportHeader\$(.+?)\.[^.]+$", lines[0] if lines else "")
    return header.group(1) if header else path.stem


def make_chunk_id(snapshot_id: str, source_path: str, member_type: str, member_name: str, start: int, end: int, raw_hash: str) -> str:
    identity = "|".join((snapshot_id, source_path, member_type, member_name, str(start), str(end), raw_hash))
    return sha256_text(identity)

