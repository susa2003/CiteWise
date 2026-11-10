import sys
from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace

from backend.app.core.config import get_settings
from backend.app.services.retrieval import semantic_store


class FakeCollection:
    def __init__(self):
        self.upserted = None
        self.query_kwargs = None
        self.deleted = None

    def upsert(self, **kwargs):
        self.upserted = kwargs

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return {"ids": [["chunk-1"]], "distances": [[0.08]]}

    def delete(self, **kwargs):
        self.deleted = kwargs


def test_semantic_index_upsert_query_and_delete(monkeypatch) -> None:
    storage_dir = Path(tempfile.mkdtemp(prefix="citewise-vector-test-"))
    monkeypatch.setenv("CITEWISE_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("CITEWISE_EMBEDDING_PROVIDER", "sentence_transformers")
    get_settings.cache_clear()
    semantic_store._embedding_model.cache_clear()
    semantic_store._collection.cache_clear()

    class FakeModel:
        def __init__(self, model_name):
            self.model_name = model_name

        def encode(self, texts, **_kwargs):
            return [[float(len(text)), 1.0] for text in texts]

    class FakeClient:
        def __init__(self, path):
            self.path = path

        def get_or_create_collection(self, _name, **_kwargs):
            return collection

    collection = FakeCollection()
    chroma_module = ModuleType("chromadb")
    chroma_module.PersistentClient = FakeClient
    sentence_module = ModuleType("sentence_transformers")
    sentence_module.SentenceTransformer = FakeModel
    monkeypatch.setitem(sys.modules, "chromadb", chroma_module)
    monkeypatch.setitem(sys.modules, "sentence_transformers", sentence_module)

    chunk = SimpleNamespace(id="chunk-1", document_id="doc-1", page_number=4, content="source evidence chunk")
    semantic_store.upsert_chunks([chunk], "paper.pdf")
    results = semantic_store.query_chunks("source evidence", limit=5, document_ids=["doc-1"])
    semantic_store.delete_document_vectors("doc-1")

    assert collection.upserted["ids"] == ["chunk-1"]
    assert collection.upserted["metadatas"][0]["page_number"] == 4
    assert results == [("chunk-1", 0.08)]
    assert collection.query_kwargs["where"] == {"document_id": {"$in": ["doc-1"]}}
    assert collection.deleted == {"where": {"document_id": "doc-1"}}
