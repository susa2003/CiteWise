from collections.abc import Iterable


def split_page_text(text: str, chunk_chars: int = 1400, overlap_chars: int = 180) -> list[str]:
    """Split one page into readable chunks while retaining bounded overlap."""
    cleaned = "\n".join(line.rstrip() for line in text.replace("\x00", " ").splitlines()).strip()
    if not cleaned:
        return []
    if chunk_chars < 200 or overlap_chars < 0 or overlap_chars >= chunk_chars:
        raise ValueError("Chunk size must be >= 200 and overlap must be smaller than chunk size.")

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_chars, len(cleaned))
        if end < len(cleaned):
            boundary = max(cleaned.rfind("\n", start, end), cleaned.rfind(". ", start, end), cleaned.rfind(" ", start, end))
            if boundary > start + int(chunk_chars * 0.55):
                end = boundary + (1 if cleaned[boundary] == "\n" else 2 if cleaned[boundary:boundary + 2] == ". " else 0)
        value = cleaned[start:end].strip()
        if value:
            chunks.append(value)
        if end >= len(cleaned):
            break
        start = max(start + 1, end - overlap_chars)
    return chunks


def build_chunks(pages: Iterable[tuple[int, str, str | None]], chunk_chars: int = 1400, overlap_chars: int = 180) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for page_number, text, section_heading in pages:
        for index, content in enumerate(split_page_text(text, chunk_chars, overlap_chars)):
            results.append({
                "page_number": page_number,
                "chunk_index": index,
                "section_heading": section_heading,
                "content": content,
                "content_length": len(content),
            })
    return results
