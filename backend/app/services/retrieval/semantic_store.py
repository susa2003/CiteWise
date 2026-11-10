from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.core.config import get_settings


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "citewise_chunks"


@lru_cache(maxsize=1)
def _embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


@lru_cache(maxsize=1)
def _collection(storage_path: str):
    import chromadb

    client = chromadb.PersistentClient(path=storage_path)
    return client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def _vector_configuration() -> tuple[Path, str]:
    settings = get_settings()
    model_name = settings.embedding_model or DEFAULT_MODEL
    return settings.storage_dir / "vectors", model_name


def upsert_chunks(chunks: list[Any], document_name: str) -> None:
    if not chunks:
        return
    vector_path, model_name = _vector_configuration()
    vector_path.mkdir(parents=True, exist_ok=True)
    encoded = _embedding_model(model_name).encode(
        [chunk.content for chunk in chunks], normalize_embeddings=True, show_progress_bar=False
    )
    embeddings = encoded.tolist() if hasattr(encoded, "tolist") else encoded
    collection = _collection(str(vector_path.resolve()))
    collection.upsert(
        ids=[chunk.id for chunk in chunks],
        documents=[chunk.content for chunk in chunks],
        embeddings=embeddings,
        metadatas=[{
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "page_number": chunk.page_number,
            "original_filename": document_name,
        } for chunk in chunks],
    )


def query_chunks(query: str, limit: int, document_ids: list[str] | None = None) -> list[tuple[str, float]]:
    vector_path, model_name = _vector_configuration()
    if not vector_path.exists():
        return []
    encoded = _embedding_model(model_name).encode([query], normalize_embeddings=True, show_progress_bar=False)
    embedding = encoded.tolist() if hasattr(encoded, "tolist") else encoded
    collection = _collection(str(vector_path.resolve()))
    kwargs: dict[str, Any] = {"query_embeddings": embedding, "n_results": limit}
    if document_ids:
        kwargs["where"] = {"document_id": {"$in": document_ids}}
    result = collection.query(**kwargs)
    ids = (result.get("ids") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    return [(chunk_id, float(distance)) for chunk_id, distance in zip(ids, distances)]


def delete_document_vectors(document_id: str) -> None:
    settings = get_settings()
    vector_path = settings.storage_dir / "vectors"
    if not vector_path.exists():
        return
    try:
        collection = _collection(str(vector_path.resolve()))
        collection.delete(where={"document_id": document_id})
    except ImportError:
        # No vector provider is installed in the keyword-only demo configuration.
        return
