import { useEffect, useState } from "react";
import { AlertCircle, ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Notice, PageHeading } from "../components/PageHeading";
import { SourceCard } from "../components/SourceCard";
import { api, errorMessage } from "../services/api";
import type { AnalysisResponse, DocumentList, DocumentRecord } from "../types/research";

export default function AnalysisPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentId, setDocumentId] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [libraryLoading, setLibraryLoading] = useState(true);

  useEffect(() => {
    api.get<DocumentList>("/documents", { params: { limit: 100 } }).then(({ data }) => {
      const ready = data.items.filter((item) => ["processed", "processed_with_warnings"].includes(item.status));
      setDocuments(ready); setDocumentId(ready[0]?.id || "");
    }).catch((reason) => setError(errorMessage(reason))).finally(() => setLibraryLoading(false));
  }, []);

  async function runAnalysis() {
    if (!documentId) return;
    setLoading(true); setError(""); setResult(null);
    try { const response = await api.post<AnalysisResponse>("/analysis", { document_id: documentId }); setResult(response.data); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="STRUCTURED PAPER REVIEW" title="Understand the paper." description="Extract research claims into a structured view, with each supported point tied to its source page." />
      {error && <Notice tone="error">{error}</Notice>}
      <section className="panel operation-panel"><div className="operation-controls"><label className="field-label">Choose a paper<select value={documentId} onChange={(event) => { setDocumentId(event.target.value); setResult(null); }} disabled={libraryLoading || !documents.length}><option value="">{libraryLoading ? "Loading papers…" : "Select a processed paper"}</option>{documents.map((document) => <option value={document.id} key={document.id}>{document.title || document.original_filename}</option>)}</select></label><button className="primary-button" disabled={!documentId || loading} onClick={() => void runAnalysis()}>{loading ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}{loading ? "Analyzing…" : "Analyze paper"}</button></div><p className="operation-note">Research problem · methodology · data · evaluation · results · contributions · limitations · future work</p></section>

      {!documents.length && !libraryLoading && <div className="panel empty-workflow"><span><AlertCircle size={20} /></span><h2>No processed papers available</h2><p>Add a PDF first. CiteWise will preserve its source pages during extraction.</p><Link to="/library" className="secondary-button">Open paper library <ArrowRight size={14} /></Link></div>}
      {result?.mode === "unavailable" && <Notice tone="info">{result.message}</Notice>}
      {result?.mode === "provider_error" && <Notice tone="error">{result.message}</Notice>}
      {result?.mode === "insufficient_evidence" && <Notice tone="info">{result.message}</Notice>}
      {result?.findings.length ? <section className="analysis-grid">{result.findings.map((finding) => <article className="panel finding-card" key={finding.category}><div className="finding-heading"><span>{finding.category}</span><i /></div><p className={finding.sources.length ? "" : "muted-finding"}>{finding.text}</p>{finding.sources.map((source) => <SourceCard source={source} key={source.chunk_id} />)}</article>)}</section> : null}
      {result?.mode === "llm_grounded" && <div className="grounding-note"><AlertCircle size={14} /> Each generated finding cites one or more stored passages. “Not explicitly mentioned” means the analysis found no supporting statement in the reviewed evidence excerpts.</div>}
    </div>
  );
}
