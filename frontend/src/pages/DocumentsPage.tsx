import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { AlertTriangle, Check, CheckCircle2, ChevronDown, FileText, LoaderCircle, RefreshCw, Trash2, Upload, X } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { Notice, PageHeading } from "../components/PageHeading";
import { api, errorMessage } from "../services/api";
import type { DocumentList, DocumentPage, DocumentRecord, PublicSettings } from "../types/research";

type QueueItem = { id: string; name: string; progress: number; status: "uploading" | "done" | "error"; detail?: string };

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [dragging, setDragging] = useState(false);
  const [maxUploadMb, setMaxUploadMb] = useState(50);
  const [page, setPage] = useState<DocumentPage | null>(null);
  const [pageError, setPageError] = useState("");
  const [pageLoading, setPageLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [searchParams] = useSearchParams();

  async function loadDocuments() {
    setLoading(true); setError("");
    try {
      const response = await api.get<DocumentList>("/documents", { params: { limit: 100 } });
      setDocuments(response.data.items); setTotal(response.data.total);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  async function openPage(documentId: string, pageNumber: number) {
    setPageLoading(true); setPageError("");
    try { const response = await api.get<DocumentPage>(`/documents/${documentId}/pages/${pageNumber}`); setPage(response.data); }
    catch (reason) { setPage(null); setPageError(errorMessage(reason)); }
    finally { setPageLoading(false); }
  }

  useEffect(() => {
    void loadDocuments();
    api.get<PublicSettings>("/settings").then(({ data }) => setMaxUploadMb(data.max_upload_mb)).catch(() => undefined);
  }, []);

  useEffect(() => {
    const docId = searchParams.get("doc");
    const pageNumber = Number(searchParams.get("page") || 1);
    if (docId) void openPage(docId, Number.isFinite(pageNumber) && pageNumber > 0 ? pageNumber : 1);
  }, [searchParams]);

  async function uploadFiles(fileList: FileList | File[]) {
    const files = Array.from(fileList);
    const accepted: File[] = [];
    const rejected: QueueItem[] = [];
    for (const file of files) {
      const id = `${file.name}-${file.size}-${Date.now()}-${Math.random()}`;
      if (!file.name.toLowerCase().endsWith(".pdf") || (file.type && file.type !== "application/pdf")) {
        rejected.push({ id, name: file.name, progress: 0, status: "error", detail: "Only PDF files are accepted." });
      } else if (file.size > maxUploadMb * 1024 * 1024) {
        rejected.push({ id, name: file.name, progress: 0, status: "error", detail: `File exceeds the ${maxUploadMb} MB limit.` });
      } else {
        accepted.push(file);
      }
    }
    const batch = accepted.map((file) => ({ file, id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}` }));
    setQueue([...rejected, ...batch.map(({ file, id }) => ({ id, name: file.name, progress: 0, status: "uploading" as const }))]);
    if (!accepted.length) return;

    const body = new FormData();
    batch.forEach(({ file }) => body.append("files", file, file.name));
    try {
      const response = await api.post<{ results: { filename: string; duplicate: boolean; error: string | null; document: DocumentRecord | null }[] }>("/documents", body, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          const progress = event.total ? Math.round((event.loaded / event.total) * 100) : 45;
          setQueue((current) => current.map((item) => item.status === "uploading" ? { ...item, progress } : item));
        },
      });
      const outcomes = response.data.results;
      const outcomeById = new Map(batch.map(({ id }, index) => [id, outcomes[index]]));
      setQueue((current) => current.map((item) => {
        const outcome = outcomeById.get(item.id);
        if (!outcome) return item;
        if (outcome.error) return { ...item, status: "error", progress: 100, detail: outcome.error };
        if (!outcome.document || outcome.document.status === "failed") {
          return { ...item, status: "error", progress: 100, detail: outcome.document?.processing_error || "The PDF could not be processed." };
        }
        const warningNote = outcome.document.status === "processed_with_warnings" ? " · review processing warnings" : "";
        return { ...item, status: "done", progress: 100, detail: outcome.duplicate ? "Already in your library · duplicate detected" : `${outcome.document.page_count} pages extracted${warningNote}` };
      }));
      if (outcomes.some((item) => item.document && item.document.status !== "failed" && !item.error)) setNotice("Upload complete. Each PDF keeps its original page references.");
      await loadDocuments();
    } catch (reason) {
      setQueue((current) => current.map((item) => item.status === "uploading" ? { ...item, status: "error", detail: errorMessage(reason) } : item));
    }
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files?.length) void uploadFiles(event.target.files);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); setDragging(false);
    if (event.dataTransfer.files.length) void uploadFiles(event.dataTransfer.files);
  }

  async function deleteDocument(document: DocumentRecord) {
    if (!window.confirm(`Delete “${document.original_filename}” and its extracted pages and search index?`)) return;
    try {
      await api.delete(`/documents/${document.id}`);
      setNotice(`${document.original_filename} was deleted.`);
      if (page?.document_id === document.id) setPage(null);
      await loadDocuments();
    } catch (reason) { setError(errorMessage(reason)); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="PAPER LIBRARY" title="Your research, organized." description="Upload PDFs to extract page-level text, metadata, and searchable evidence." />
      {error && <Notice tone="error">{error} <button className="inline-button" onClick={() => void loadDocuments()}>Retry</button></Notice>}
      {notice && <Notice tone="success">{notice}<button className="notice-close" aria-label="Dismiss" onClick={() => setNotice("")}><X size={13} /></button></Notice>}

      <div className={`upload-dropzone${dragging ? " dragging" : ""}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
        <input ref={inputRef} type="file" accept="application/pdf,.pdf" multiple hidden onChange={onInputChange} />
        <span className="drop-icon"><Upload size={20} /></span>
        <div><strong>Drop research papers here</strong><p>PDF only · Up to {maxUploadMb} MB per file · Multiple files supported</p></div>
        <button className="secondary-button" onClick={() => inputRef.current?.click()}>Browse files</button>
      </div>

      {queue.length > 0 && <section className="panel queue-panel"><div className="panel-heading"><div><h2>Upload activity</h2><p>Files are processed page by page.</p></div><button className="text-button" onClick={() => setQueue([])}>Clear <X size={13} /></button></div><div className="queue-list">{queue.map((item) => <div className="queue-row" key={item.id}><span className={`queue-icon ${item.status}`}>{item.status === "uploading" ? <LoaderCircle className="spin" size={15} /> : item.status === "done" ? <Check size={15} /> : <AlertTriangle size={15} />}</span><span className="queue-name"><strong>{item.name}</strong><small>{item.detail || (item.status === "uploading" ? "Uploading…" : "")}</small>{item.status === "uploading" && <i className="progress-track"><b style={{ width: `${item.progress}%` }} /></i>}</span><span className="queue-progress">{item.status === "uploading" ? `${item.progress}%` : item.status === "done" ? "Added" : "Needs attention"}</span></div>)}</div></section>}

      <div className="library-layout">
        <section className="panel documents-panel">
          <div className="panel-heading"><div><h2>All papers <span className="heading-count">{total}</span></h2><p>Source files remain private in local storage.</p></div><button className="icon-button" title="Refresh library" onClick={() => void loadDocuments()}><RefreshCw size={15} /></button></div>
          {loading ? <div className="page-loading"><LoaderCircle className="spin" size={20} /> Loading documents…</div> : documents.length === 0 ? <div className="library-empty"><span><FileText size={21} /></span><h3>No papers yet</h3><p>Upload one or more PDFs to create your evidence library.</p><button className="secondary-button" onClick={() => inputRef.current?.click()}><Upload size={14} /> Choose PDF</button></div> : <div className="document-list">{documents.map((document) => <article className="document-row" key={document.id}>
            <span className="document-icon large"><FileText size={18} /></span>
            <div className="document-info"><strong>{document.title || document.original_filename}</strong><small>{document.original_filename}</small><div className="document-meta"><span className={`status-tag ${document.status}`}>{document.status.replaceAll("_", " ")}</span><span>{document.page_count} pages</span><span>{document.chunk_count} chunks</span>{document.publication_year && <span>{document.publication_year}</span>}</div>{document.processing_error && <small className="document-error">{document.processing_error}</small>}{document.warnings.length > 0 && <details className="warning-detail"><summary>{document.warnings.length} processing warning{document.warnings.length === 1 ? "" : "s"}</summary><ul>{document.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></details>}</div>
            <div className="document-actions"><button className="outline-button" disabled={document.page_count === 0} onClick={() => void openPage(document.id, 1)}>View page <ChevronDown size={13} /></button><button className="danger-icon" aria-label={`Delete ${document.original_filename}`} title="Delete paper" onClick={() => void deleteDocument(document)}><Trash2 size={15} /></button></div>
          </article>)}</div>}
        </section>

        <aside className="panel source-viewer">
          <div className="panel-heading"><div><h2>Source reader</h2><p>Open any page to inspect extracted text.</p></div></div>
          {pageLoading ? <div className="page-loading"><LoaderCircle className="spin" size={19} /> Opening source page…</div> : pageError ? <div className="source-placeholder error-text">{pageError}</div> : page ? <div className="reader-content"><div className="reader-label"><CheckCircle2 size={14} /> SOURCE PAGE</div><h3>{page.original_filename}</h3><div className="reader-page">Page {page.page_number}{page.section_heading ? ` · ${page.section_heading}` : ""} · {page.extraction_method === "ocr" ? "OCR text" : "Extracted text"}</div>{page.warnings.map((warning) => <div className="reader-warning" key={warning}><AlertTriangle size={13} />{warning}</div>)}<pre>{page.text || "No text was extracted from this page."}</pre></div> : <div className="source-placeholder"><span><FileText size={20} /></span><strong>Select a paper page</strong><p>Source excerpts and citations link back here so you can check what the paper says.</p></div>}
        </aside>
      </div>
    </div>
  );
}
