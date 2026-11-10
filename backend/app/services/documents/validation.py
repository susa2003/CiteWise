from pathlib import Path, PureWindowsPath
import re


def safe_original_filename(filename: str | None) -> str:
    raw = (filename or "research-paper.pdf").replace("\\", "/")
    name = Path(PureWindowsPath(raw).name).name
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).strip().strip(".")
    if not name:
        name = "research-paper.pdf"
    return name[:255]


def has_pdf_signature(prefix: bytes) -> bool:
    return b"%PDF-" in prefix[:1024]


def resolve_storage_path(storage_root: Path, relative_path: str) -> Path:
    root = storage_root.resolve()
    candidate = (root / relative_path).resolve()
    if candidate == root or not candidate.is_relative_to(root):
        raise ValueError("Stored document path is outside the configured storage directory.")
    return candidate
