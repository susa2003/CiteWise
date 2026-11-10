import asyncio
from pathlib import Path
import tempfile

import httpx

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine, get_session_factory
from backend.app.main import app
from backend.app.models.analysis import AnalysisRun


def test_dashboard_public_settings_and_report_exports(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-exports-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_LLM_PROVIDER", "none")
    get_settings.cache_clear()
    get_engine.cache_clear()

    async def scenario():
        async with app.router.lifespan_context(app):
            session = get_session_factory()()
            run = AnalysisRun(
                kind="summary",
                document_ids=["doc-1"],
                request_data={"format": "short"},
                result_data={"sections": [{
                    "heading": "Main finding",
                    "text": "A source linked finding.",
                    "sources": [{"filename": "paper.pdf", "page_number": 3, "excerpt": "Evidence excerpt from the paper."}],
                }]},
            )
            session.add(run)
            session.commit()
            run_id = run.id
            session.close()

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                dashboard = await client.get("/api/dashboard")
                settings = await client.get("/api/settings")
                pdf = await client.post("/api/exports", json={"run_id": run_id, "format": "pdf"})
                docx = await client.post("/api/exports", json={"run_id": run_id, "format": "docx"})
                return dashboard, settings, pdf, docx

    dashboard, settings, pdf, docx = asyncio.run(scenario())
    assert dashboard.status_code == 200
    assert dashboard.json()["total_documents"] == 0
    assert len(dashboard.json()["analysis_history"]) == 1
    public = settings.json()
    assert public["demo_mode"] is True
    assert public["llm_configured"] is False
    assert "test-secret" not in settings.text
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-")
    assert docx.status_code == 200
    assert docx.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert docx.content.startswith(b"PK")
