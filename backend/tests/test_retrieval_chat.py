import asyncio
from pathlib import Path
import tempfile

import httpx

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine
from backend.app.main import app
from backend.tests.pdf_fixtures import make_pdf


def test_keyword_search_chat_abstention_and_conversation_context(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-chat-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_LLM_PROVIDER", "none")
    get_settings.cache_clear()
    get_engine.cache_clear()
    content = make_pdf([
        "The evaluation reports mean reciprocal rank and precision at ten for retrieval quality."
    ], title="Search Evaluation")

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                upload = await client.post("/api/documents", files=[("files", ("evaluation.pdf", content, "application/pdf"))])
                document_id = upload.json()["results"][0]["document"]["id"]
                search = await client.post("/api/search", json={"query": "mean reciprocal rank", "document_ids": [document_id]})
                chat = await client.post("/api/chat", json={"question": "Explain reciprocal rank", "document_ids": [document_id]})
                followup = await client.post("/api/chat", json={
                    "question": "What other retrieval metric appears?",
                    "conversation_id": chat.json()["conversation_id"],
                    "document_ids": [document_id],
                })
                saved_conversation = await client.get(f"/api/conversations/{chat.json()['conversation_id']}")
                missing = await client.post("/api/chat", json={"question": "What country was the study conducted in?", "document_ids": [document_id]})
                return upload, search, chat, followup, saved_conversation, missing

    upload, search, chat, followup, saved_conversation, missing = asyncio.run(scenario())
    assert upload.json()["results"][0]["document"]["status"] == "processed"
    assert search.json()["retrieval_mode"] == "keyword"
    assert search.json()["sufficient_evidence"] is True
    assert search.json()["results"][0]["page_number"] == 1
    assert chat.json()["mode"] == "retrieval_only"
    assert chat.json()["claims"] == []
    assert "no generated answer is being presented" in chat.json()["answer"]
    assert chat.json()["sources"][0]["filename"] == "evaluation.pdf"
    assert followup.json()["conversation_id"] == chat.json()["conversation_id"]
    assert len(saved_conversation.json()["messages"]) == 4
    assert saved_conversation.json()["messages"][1]["citations"][0]["page_number"] == 1
    assert missing.json()["mode"] == "insufficient_evidence"
    assert missing.json()["insufficient_evidence"] is True
    assert missing.json()["sources"] == []


def test_model_claims_only_keep_valid_retrieved_chunk_citations(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-citations-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("CITEWISE_LLM_API_KEY", "test-secret")
    monkeypatch.setenv("CITEWISE_LLM_MODEL", "test-model")
    get_settings.cache_clear()
    get_engine.cache_clear()
    valid_ids: list[str] = []

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                await client.post("/api/documents", files=[("files", (
                    "methods.pdf",
                    make_pdf(["The method uses BM25 keyword retrieval for ranking relevant paper passages."]),
                    "application/pdf",
                ))])
                retrieved = (await client.post("/api/search", json={"query": "BM25 keyword retrieval"})).json()["results"][0]
                valid_ids.append(retrieved["chunk_id"])
                chat = await client.post("/api/chat", json={"question": "What retrieval method is used?"})
                return retrieved, chat

    async def fake_completion(_settings, _messages):
        return (
            '{"insufficient_evidence": false, "claims": ['
            f'{{"text":"The paper uses BM25 keyword retrieval.","interpretation":false,"chunk_ids":["{valid_ids[0]}"]}},'
            '{"text":"It also uses an invented neural reranker.","interpretation":false,"chunk_ids":["made-up-chunk"]}]}'
        )

    monkeypatch.setattr("backend.app.api.chat.complete_json", fake_completion)

    retrieved, chat = asyncio.run(scenario())
    # The generated claim must cite the same chunk ID returned by the server's retrieval.
    body = chat.json()
    assert body["mode"] == "llm_grounded"
    assert len(body["claims"]) == 1
    citation = body["claims"][0]["citations"][0]
    assert citation["chunk_id"] == retrieved["chunk_id"]
    assert citation["filename"] == "methods.pdf"
    assert citation["page_number"] == 1
    assert "invented neural reranker" not in body["answer"]
