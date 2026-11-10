# API and data model

The API uses a versionable `/api` REST namespace, JSON responses, Pydantic validation, and consistent HTTP status codes. Uploaded files use `multipart/form-data`; all user-visible document references use stable document IDs.

The initial relational model is documented in [architecture.md](architecture.md#3-database-design). Page and chunk records preserve the original 1-based page number so citation display does not depend on model-generated page claims.

FastAPI serves the live OpenAPI reference at `/docs` and `/openapi.json`.

## Implemented endpoints

- `GET /api/health`, `GET /api/settings`, `GET /api/dashboard`
- `POST /api/documents` (multipart field `files`, repeatable for batch upload); `GET /api/documents`; `GET /api/documents/{id}`; `DELETE /api/documents/{id}`
- `GET /api/documents/{id}/pages/{page_number}`
- `POST /api/search` with query, optional document IDs, and top-k
- `POST /api/chat`; `GET /api/conversations`; `GET /api/conversations/{id}`
- `POST /api/analysis`, `/api/comparisons`, `/api/gaps`, `/api/summaries`
- `POST /api/exports` with a stored run ID and `pdf` or `docx` format

AI operation endpoints report an unavailable mode when the LLM provider is not configured. Chat still returns ranked source passages in retrieval-only mode. It does not return hardcoded AI responses.

## Relational tables

- `documents`: original filename, safe generated storage path, content hash, status, extraction metadata, warnings, and counts.
- `document_pages`: one row per original PDF page, with text, extraction method, section, and warnings.
- `document_chunks`: page-bound text chunks with stable IDs and optional vector IDs.
- `conversations`, `messages`, and `citations`: chat history and stored citation snapshots. Source details remain visible in history if the original document is later deleted; the page link then returns not found.
- `analysis_runs`: structured analysis, comparisons, gap exploration, and generated summaries as JSON with source document IDs and timestamps.

SQLite is created under `storage/citewise.db` by default. SQLAlchemy models use portable JSON and relational types for later PostgreSQL support. Alembic migrations are not yet configured; the current local setup creates missing tables on startup.
