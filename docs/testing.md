# Testing guide

Backend tests use generated minimal PDFs and mocked provider responses; they cover PDF validation, multi-page extraction, metadata, chunking, OCR fallback behavior, duplicate detection, safe deletion, keyword/hybrid retrieval contracts, citation validation, abstention, structured workflows, dashboard/settings, and PDF/DOCX exports. A semantic-store test uses mocked ChromaDB and embedding modules so default installs remain lightweight.

Run backend checks from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

Run frontend checks from `frontend/`:

```powershell
npm test
npm run build
```

Tests use generated fixtures and do not contain private research papers. The optional real OCR executable, embedding model, vector database package, or remote LLM are not required by the default test suite.

Negative cases assert insufficient evidence when the answer is absent. Provider responses are mocked for reproducibility; no test makes a claim about real model accuracy. Only claim tests passed after actually running the corresponding commands.
