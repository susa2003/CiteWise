from pathlib import Path


def make_pdf(page_texts: list[str], *, title: str = "", author: str = "") -> bytes:
    page_object_ids = [3 + index * 2 for index in range(len(page_texts))]
    font_object_id = 3 + len(page_texts) * 2
    info_object_id = font_object_id + 1
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{ ' '.join(f'{item} 0 R' for item in page_object_ids) }] /Count {len(page_texts)} >>".encode(),
    ]

    for index, content in enumerate(page_texts):
        page_id = page_object_ids[index]
        content_id = page_id + 1
        escaped = content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
        page = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode()
        content_obj = f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        objects.extend([page, content_obj])

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    info = f"<< /Title ({title}) /Author ({author}) >>".encode("latin-1")
    objects.append(info)

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode())
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info {info_object_id} 0 R >>\n".encode())
    pdf.extend(f"startxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(pdf)


def write_pdf(path: Path, page_texts: list[str], **metadata: str) -> Path:
    path.write_bytes(make_pdf(page_texts, **metadata))
    return path
