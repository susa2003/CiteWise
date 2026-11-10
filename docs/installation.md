# Installation and environment configuration

These commands are for local development from the `CiteWise` project root. The backend requirements are pinned to compatible releases; the frontend lockfile records the resolved npm packages.

## Prerequisites

- Python 3.11 or newer (tested with Python 3.12)
- Node.js 20.19 or newer and npm
- Optional: Tesseract OCR for scanned PDF fallback
- Optional: an API key and model name for an OpenAI-compatible LLM provider

## Configuration

Copy `.env.example` to `.env` and set only the options needed for your local environment. The default provider is `none`; PDF extraction and keyword search work without paid credentials. Do not commit `.env` or private uploaded papers.

Relevant options:

- `CITEWISE_MAX_UPLOAD_MB`: per-file PDF size limit (default 50).
- `CITEWISE_LLM_PROVIDER=openai_compatible`, `CITEWISE_LLM_API_KEY`, and `CITEWISE_LLM_MODEL`: enable grounded generation. `CITEWISE_LLM_BASE_URL` defaults to `https://api.openai.com/v1` and can point to another compatible endpoint.
- `CITEWISE_EMBEDDING_PROVIDER=sentence_transformers`: enable optional local embeddings and ChromaDB. `CITEWISE_EMBEDDING_MODEL` defaults to `sentence-transformers/all-MiniLM-L6-v2`.
- `CITEWISE_OCR_ENABLED=true`: request OCR for pages without selectable text. The `pytesseract` Python package and the Tesseract executable must both be installed.

## Start the backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt
Copy-Item .env.example .env
uvicorn backend.app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`; interactive OpenAPI docs are at `http://127.0.0.1:8000/docs`.

## Start the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. To point the frontend to another API, set `VITE_API_BASE_URL` (for example, `http://127.0.0.1:8000/api`).

## Optional capabilities

Install export libraries to create PDF and DOCX reports:

```powershell
python -m pip install -r backend\requirements-exports.txt
```

Install Python OCR bindings with `python -m pip install -r backend\requirements-ocr.txt`, then install the Tesseract executable for your operating system and set `CITEWISE_OCR_ENABLED=true`.

Semantic retrieval is optional and larger because it includes a local ML runtime:

```powershell
python -m pip install -r backend\requirements-rag.txt
```

The configured embedding model may download on first use. If these packages are unavailable, keyword search remains active and semantic indexing failures are visible in document warnings.

## Local data

The `storage/` folder contains private uploads, the SQLite database, exported vector data, and temporary derived data. It is excluded from Git. Deleting a paper in the library removes its stored PDF and database records; backups should be handled deliberately.
