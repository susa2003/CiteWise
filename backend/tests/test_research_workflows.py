import asyncio
import json
from pathlib import Path
import re
import tempfile

import httpx

from backend.app.core.config import get_settings
from backend.app.db.session import get_engine
from backend.app.main import app
from backend.tests.pdf_fixtures import make_pdf


def test_analysis_comparison_gaps_and_summary_validate_evidence(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-research-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("CITEWISE_LLM_API_KEY", "test-secret")
    monkeypatch.setenv("CITEWISE_LLM_MODEL", "test-model")
    get_settings.cache_clear()
    get_engine.cache_clear()

    paper_sources: dict[str, str] = {}

    def source_ids(message: str) -> list[tuple[str, str]]:
        return re.findall(r"\[chunk_id=([a-f0-9]+)\] ([^,\n]+), page", message)

    async def fake_completion(_settings, messages, system_prompt=""):
        evidence_message = messages[-1]["content"]
        ids_by_name = {}
        for chunk_id, filename in source_ids(evidence_message):
            ids_by_name.setdefault(filename, chunk_id)
        ids = list(ids_by_name.values())
        if "structured analysis" in system_prompt.lower():
            return json.dumps({"findings": [
                {"category": "Research Problem", "text": "The paper studies evidence grounded retrieval.", "chunk_ids": [ids[0]]},
                {"category": "Results", "text": "This unsupported result is rejected.", "chunk_ids": ["not-a-real-chunk"]},
            ]})
        if "compare the supplied" in system_prompt.lower():
            return json.dumps({
                "categories": [{"category": "Results", "paper_findings": [
                    {"document_id": paper_sources["paper-a.pdf"], "text": "Paper A reports a retrieval result.", "chunk_ids": [ids_by_name["paper-a.pdf"]]},
                    {"document_id": paper_sources["paper-b.pdf"], "text": "Paper B reports a different retrieval result.", "chunk_ids": [ids_by_name["paper-b.pdf"]]},
                ]}],
                "similarities": [{"text": "Both papers study retrieval.", "chunk_ids": [ids[0], ids[-1]]}],
                "differences": [], "methodological_strengths": [], "methodological_weaknesses": [],
                "dataset_differences": [], "research_opportunities": [],
                "performance_comparison": {
                    "comparable": True, "text": "Paper A scores 0.91 and Paper B scores 0.82.",
                    "papers": [
                        {
                            "document_id": paper_sources["paper-a.pdf"],
                            "metric": "AUC", "dataset": "dataset A", "conditions": "same setup",
                            "chunk_ids": [ids_by_name["paper-a.pdf"]],
                        },
                        {
                            "document_id": paper_sources["paper-b.pdf"],
                            "metric": "AUC", "dataset": "dataset B", "conditions": "same setup",
                            "chunk_ids": [ids_by_name["paper-b.pdf"]],
                        },
                    ],
                },
            })
        if "identify possible research gaps" in system_prompt.lower():
            return json.dumps({"gaps": [{
                "title": "Limited dataset coverage", "explanation": "The authors note that the evaluation uses a limited dataset.",
                "kind": "explicit_limitation", "chunk_ids": [ids[0]], "why_it_matters": "Coverage may affect transfer.",
                "possible_direction": "Evaluate on additional populations.", "suggested_experiments": ["Cross-dataset evaluation"],
                "potential_metrics": ["Recall@K"],
            }]})
        if "create the requested research-paper summary" in system_prompt.lower():
            return json.dumps({"sections": [{
                "heading": "Approach", "text": "The paper evaluates a retrieval method.",
                "interpretation": False, "chunk_ids": [ids[0]],
            }]})
        raise AssertionError(f"Unexpected prompt: {system_prompt}")

    for module in ["analysis", "comparisons", "gaps", "summaries"]:
        monkeypatch.setattr(f"backend.app.api.{module}.complete_json", fake_completion)

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                papers = [
                    ("paper-a.pdf", make_pdf([
                        "Introduction. The research problem is evidence grounded retrieval. The method uses BM25. "
                        "The evaluation reports recall on a limited dataset. The authors identify dataset coverage as a limitation."
                    ])),
                    ("paper-b.pdf", make_pdf([
                        "Introduction. The research problem is evidence grounded retrieval. The method uses neural ranking. "
                        "The evaluation reports precision on a separate dataset."
                    ])),
                ]
                uploaded = []
                for filename, content in papers:
                    response = await client.post("/api/documents", files=[("files", (filename, content, "application/pdf"))])
                    document = response.json()["results"][0]["document"]
                    uploaded.append(document["id"])
                    paper_sources[filename] = document["id"]
                analysis = await client.post("/api/analysis", json={"document_id": uploaded[0]})
                comparison = await client.post("/api/comparisons", json={"document_ids": uploaded})
                gaps = await client.post("/api/gaps", json={"document_ids": [uploaded[0]]})
                summary = await client.post("/api/summaries", json={"document_id": uploaded[0], "format": "short"})
                return analysis, comparison, gaps, summary

    analysis, comparison, gaps, summary = asyncio.run(scenario())
    analysis_data = analysis.json()
    problem = next(item for item in analysis_data["findings"] if item["category"] == "Research Problem")
    result = next(item for item in analysis_data["findings"] if item["category"] == "Results")
    assert analysis_data["mode"] == "llm_grounded"
    assert problem["sources"][0]["filename"] == "paper-a.pdf"
    assert result["text"] == "Not explicitly mentioned in the uploaded paper."
    assert result["sources"] == []

    comparison_data = comparison.json()
    results_category = next(item for item in comparison_data["categories"] if item["category"] == "Results")
    assert [paper["filename"] for paper in results_category["papers"]] == ["paper-a.pdf", "paper-b.pdf"]
    assert comparison_data["performance_comparison"]["comparable"] is False
    assert comparison_data["performance_comparison"]["metric"] is None
    assert "not directly comparable" in comparison_data["performance_comparison"]["text"]

    gap = gaps.json()["gaps"][0]
    assert gap["kind"] == "explicit_limitation"
    assert gap["sources"][0]["filename"] == "paper-a.pdf"
    assert gap["potential_metrics"] == ["Recall@K"]
    assert summary.json()["mode"] == "llm_grounded"
    assert summary.json()["sections"][0]["sources"][0]["page_number"] == 1


def test_analysis_features_are_explicitly_unavailable_without_llm(monkeypatch) -> None:
    temporary_root = Path(tempfile.mkdtemp(prefix="citewise-test-no-llm-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(temporary_root / "storage"))
    monkeypatch.setenv("CITEWISE_DATABASE_URL", f"sqlite:///{(temporary_root / 'test.db').as_posix()}")
    monkeypatch.setenv("CITEWISE_LLM_PROVIDER", "none")
    get_settings.cache_clear()
    get_engine.cache_clear()

    async def scenario():
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                uploaded = await client.post("/api/documents", files=[("files", (
                    "paper.pdf", make_pdf(["Research content and evidence." ]), "application/pdf"
                ))])
                document_id = uploaded.json()["results"][0]["document"]["id"]
                return await client.post("/api/analysis", json={"document_id": document_id})

    response = asyncio.run(scenario())
    assert response.json()["mode"] == "unavailable"
    assert response.json()["findings"] == []
    assert "requires a configured LLM" in response.json()["message"]
