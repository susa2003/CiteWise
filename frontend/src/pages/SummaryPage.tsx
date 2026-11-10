import { useEffect, useState } from "react";
import { Download, FileDown, FileText, LoaderCircle, Sparkles } from "lucide-react";
import { Notice, PageHeading } from "../components/PageHeading";
import { SourceCard } from "../components/SourceCard";
import { api, errorMessage } from "../services/api";
import type { DocumentList, DocumentRecord, SummaryResponse } from "../types/research";

const formats = [
  ["short", "Short summary"],
  ["detailed_technical", "Detailed technical"],
  ["beginner_friendly", "Beginner friendly"],
  ["academic", "Academic"],
  ["methodology_focused", "Methodology focused"],
  ["results_focused", "Results focused"],
];

export default function SummaryPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [format, setFormat] = useState("short");
  const [result, setResult] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<DocumentList>("/documents", { params: { limit: 100 } }).then(({ data }) => {
      const ready = data.items.filter((item) => ["processed", "processed_with_warnings"].includes(item.status));
      setDocuments(ready); setDocumentId(ready[0]?.id || "");
    }).catch((reason) => setError(errorMessage(reason)));
  }, []);

  async function generate() {
    if (!documentId) return;
    setLoading(true); setError(""); setResult(null);
    try { const response = await api.post<SummaryResponse>("/summaries", { document_id: documentId, format }); setResult(response.data); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  async function exportReport(fileFormat: "pdf" | "docx") {
    if (!result?.run_id) return;
    setExporting(fileFormat); setError("");
    try {
      const response = await api.post<Blob>("/exports", { run_id: result.run_id, format: fileFormat }, { responseType: "blob" });
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = `citewise-summary.${fileFormat}`; anchor.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setExporting(""); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="RESEARCH SUMMARY" title="Choose how to read it." description="Generate a paper summary in the style that fits your current task, with citations beside each section." />
      {error && <Notice tone="error">{error}</Notice>}
      <section className="panel operation-panel"><div className="operation-controls"><label className="field-label">Paper<select value={documentId} onChange={(event) => { setDocumentId(event.target.value); setResult(null); }}><option value="">Select a processed paper</option>{documents.map((document) => <option value={document.id} key={document.id}>{document.title || document.original_filename}</option>)}</select></label><label className="field-label">Summary format<select value={format} onChange={(event) => { setFormat(event.target.value); setResult(null); }}>{formats.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><button className="primary-button" disabled={!documentId || loading} onClick={() => void generate()}>{loading ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}{loading ? "Generating…" : "Generate summary"}</button></div></section>
      {result?.message && <Notice tone={result.mode === "provider_error" ? "error" : "info"}>{result.message}</Notice>}
      {result?.sections.length ? <section className="summary-result panel"><div className="panel-heading"><div><h2>{documents.find((item) => item.id === result.document_id)?.title || documents.find((item) => item.id === result.document_id)?.original_filename}</h2><p>{formats.find(([value]) => value === result.format)?.[1]} · Evidence linked</p></div><div className="export-actions"><button className="outline-button" disabled={!result.run_id || !!exporting} onClick={() => void exportReport("pdf")}><FileDown size={14} />{exporting === "pdf" ? "Preparing…" : "PDF"}</button><button className="outline-button" disabled={!result.run_id || !!exporting} onClick={() => void exportReport("docx")}><FileText size={14} />{exporting === "docx" ? "Preparing…" : "DOCX"}</button></div></div><div className="summary-sections">{result.sections.map((section, index) => <article className="summary-section" key={`${section.heading}-${index}`}><div className="summary-section-heading"><span>{String(index + 1).padStart(2, "0")}</span><h3>{section.heading}</h3>{section.interpretation && <em>Interpretation</em>}</div><p>{section.text}</p>{section.sources.map((source) => <SourceCard source={source} key={source.chunk_id} />)}</article>)}</div></section> : null}
      {result?.mode === "unavailable" && <div className="grounding-note"><Download size={14} /> PDF and DOCX export become available after a source-grounded summary is generated with a configured LLM provider.</div>}
      {!documents.length && <div className="panel empty-workflow"><span><FileText size={20} /></span><h2>No processed papers available</h2><p>Add a PDF to generate a source-linked summary.</p></div>}
    </div>
  );
}
