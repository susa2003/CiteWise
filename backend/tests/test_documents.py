import asyncio
from pathlib import Path
import tempfile

import httpx

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine
from backend.app.main import app
from backend.tests.pdf_fixtures import make_pdf


def run_api(coro):
    return asyncio.run(coro)


def test_upload_extracts_each_page_and_duplicate_is_detected(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    get_settings.cache_clear()
    get_engine.cache_clear()
    payload = make_pdf([
        "Abstract\nWe study robust citation tracking and page-level evidence in research literature.",
        "Results\nThe proposed system links each reported observation to a source page and chunk.",
    ], title="Evidence-Aware Research", author="A. Example; B. Scholar")

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                first = await client.post("/api/documents", files=[("files", ("paper.pdf", payload, "application/pdf"))])
                second = await client.post("/api/documents", files=[("files", ("same-paper.pdf", payload, "application/pdf"))])
                listing = await client.get("/api/documents")
                document_id = first.json()["results"][0]["document"]["id"]
                page = await client.get(f"/api/documents/{document_id}/pages/2")
                deletion = await client.delete(f"/api/documents/{document_id}")
                after_delete = await client.get("/api/documents")
                stored_pdf_exists = (temporary_root / "storage" / "uploads" / f"{document_id}.pdf").exists()
                return first, second, listing, page, deletion, after_delete, stored_pdf_exists

    first, second, listing, page, deletion, after_delete, stored_pdf_exists = run_api(scenario())
    result = first.json()["results"][0]
    assert first.status_code == 201
    assert result["document"]["status"] == "processed"
    assert result["document"]["page_count"] == 2
    assert result["document"]["chunk_count"] >= 2
    assert result["document"]["title"] == "Evidence-Aware Research"
    assert result["document"]["authors"] == ["A. Example", "B. Scholar"]
    assert second.json()["results"][0]["duplicate"] is True
    assert listing.json()["total"] == 1
    assert page.json()["page_number"] == 2
    assert "source page and chunk" in page.json()["text"]
    assert deletion.status_code == 204
    assert after_delete.json()["total"] == 0
    assert stored_pdf_exists is False


def test_upload_reports_invalid_pdf_without_creating_a_document(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-invalid-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    get_settings.cache_clear()
    get_engine.cache_clear()

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/documents", files=[("files", ("fake.pdf", b"not a PDF", "application/pdf"))])
                listing = await client.get("/api/documents")
                return response, listing

    response, listing = run_api(scenario())
    assert response.status_code == 201
    assert response.json()["results"][0]["error"] == "The file does not contain a valid PDF header."
    assert listing.json()["total"] == 0


def test_page_chunking_keeps_original_page_number() -> None:
    from backend.app.services.documents.chunking import build_chunks

    chunks = build_chunks([(7, "A" * 3000, "Methods")], chunk_chars=800, overlap_chars=100)
    assert len(chunks) > 1
    assert {chunk["page_number"] for chunk in chunks} == {7}
    assert {chunk["section_heading"] for chunk in chunks} == {"Methods"}


def test_empty_scanned_page_reports_ocr_disabled_warning(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-scanned-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_OCR_ENABLED", "false")
    get_settings.cache_clear()
    get_engine.cache_clear()

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post("/api/documents", files=[("files", ("scan.pdf", make_pdf([""]), "application/pdf"))])

    response = run_api(scenario())
    document = response.json()["results"][0]["document"]
    assert document["status"] == "processed_with_warnings"
    assert document["page_count"] == 1
    assert any("OCR is disabled" in warning for warning in document["warnings"])


def test_scanned_page_uses_configured_ocr_fallback(tmp_path, monkeypatch) -> None:
    from backend.app.services.documents import extractor

    path = tmp_path / "scanned.pdf"
    path.write_bytes(make_pdf([""]))
    monkeypatch.setattr(extractor, "_ocr_page", lambda _page: "OCR extracted a methods section from the scanned page.")
    extracted = extractor.extract_pdf(path, ocr_enabled=True)
    assert extracted.pages[0].extraction_method == "ocr"
    assert "methods section" in extracted.pages[0].text
    assert extracted.pages[0].warnings == []
