# CiteWise AI

CiteWise AI is an evidence-first research paper workspace. It is designed to extract papers page by page, preserve source provenance, and keep generated answers distinct from what the uploaded documents actually support.

## Project status

The local platform now supports PDF upload, page-level extraction, duplicate detection, source reading, BM25 search, chat history, structured AI workflows when a provider is configured, dashboard data, and PDF/DOCX export. Demo mode leaves generated analysis unavailable and labels retrieval-only chat clearly.

## Architecture and setup

- [System architecture and implementation roadmap](docs/architecture.md)
- [Installation and environment configuration](docs/installation.md)
- [API and data model notes](docs/api-and-data-model.md)
- [RAG, evidence, and citation policy](docs/rag-and-evidence.md)
- [Testing guide](docs/testing.md)

## Local services

- Frontend: React, Vite, TypeScript, Tailwind CSS
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite
- PDF extraction: pdfplumber page-by-page; optional Tesseract OCR fallback
- Retrieval: BM25 keyword search; optional Sentence Transformers embeddings and ChromaDB
- LLM: OpenAI-compatible provider adapter configured through environment variables

## Run locally

See [installation and environment configuration](docs/installation.md) for full commands. Start the API from the project root with `uvicorn backend.app.main:app --reload`, and the frontend from `frontend/` with `npm run dev`.

The API docs are served at `/docs`. Local uploads, databases, vector indexes, and `.env` are excluded from version control.

Local uploads and databases are excluded from version control. Never commit private research papers or real API credentials.
