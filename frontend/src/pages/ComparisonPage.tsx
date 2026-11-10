import { useEffect, useState } from "react";
import { ArrowRight, LoaderCircle, Scale, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Notice, PageHeading } from "../components/PageHeading";
import { SourceCard } from "../components/SourceCard";
import { api, errorMessage } from "../services/api";
import type { ComparisonResponse, DocumentList, DocumentRecord } from "../types/research";

export default function ComparisonPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<DocumentList>("/documents", { params: { limit: 100 } }).then(({ data }) => {
      const ready = data.items.filter((item) => ["processed", "processed_with_warnings"].includes(item.status));
      setDocuments(ready); setSelectedIds(ready.slice(0, 2).map((item) => item.id));
    }).catch((reason) => setError(errorMessage(reason)));
  }, []);

  function toggle(id: string) {
    setSelectedIds((current) => current.includes(id) ? current.filter((value) => value !== id) : current.length >= 5 ? current : [...current, id]);
    setResult(null);
  }

  async function compare() {
    if (selectedIds.length < 2) return;
    setLoading(true); setError(""); setResult(null);
    try { const response = await api.post<ComparisonResponse>("/comparisons", { document_ids: selectedIds }); setResult(response.data); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="CROSS-PAPER SYNTHESIS" title="Compare the evidence." description="Review methods, data, outcomes, and limitations side by side. Numeric results need comparable conditions." />
      {error && <Notice tone="error">{error}</Notice>}
      <section className="panel selection-panel"><div className="panel-heading"><div><h2>Select papers <span className="heading-count">{selectedIds.length}/5</span></h2><p>Choose at least two processed papers.</p></div><button className="primary-button" disabled={selectedIds.length < 2 || loading} onClick={() => void compare()}>{loading ? <LoaderCircle className="spin" size={15} /> : <Scale size={15} />}{loading ? "Comparing…" : "Compare papers"}</button></div>
        {documents.length ? <div className="paper-select-grid">{documents.map((document) => <label className={`paper-select-card${selectedIds.includes(document.id) ? " selected" : ""}`} key={document.id}><input type="checkbox" checked={selectedIds.includes(document.id)} onChange={() => toggle(document.id)} disabled={!selectedIds.includes(document.id) && selectedIds.length >= 5} /><span><strong>{document.title || document.original_filename}</strong><small>{document.original_filename} · {document.page_count} pages</small></span>{selectedIds.includes(document.id) && <span className="selection-check"><Sparkles size={12} /></span>}</label>)}</div> : <div className="selection-empty">Upload and process papers to compare them. <Link to="/library">Go to library <ArrowRight size={13} /></Link></div>}
      </section>

      {result?.message && <Notice tone={result.mode === "provider_error" ? "error" : "info"}>{result.message}</Notice>}
      {result?.mode === "llm_grounded" && <>
        <div className="comparison-caveat"><Scale size={15} /><span><strong>Results need context.</strong> Performance comparisons are shown only when evidence for every selected paper identifies a shared metric, dataset, and experimental conditions.</span></div>
        <section className="panel comparison-table-panel"><div className="panel-heading"><div><h2>Evidence comparison</h2><p>Open a cited page to check the supporting passage.</p></div></div><div className="comparison-table-scroll"><table className="comparison-table"><thead><tr><th>Category</th>{result.categories[0]?.papers.map((paper) => <th key={paper.document_id}>{paper.filename}</th>)}</tr></thead><tbody>{result.categories.map((category) => <tr key={category.category}><th scope="row">{category.category}</th>{category.papers.map((paper) => <td key={`${category.category}-${paper.document_id}`}><p className={paper.sources.length ? "" : "muted-finding"}>{paper.text}</p>{paper.sources.map((source) => <SourceCard source={source} compact key={source.chunk_id} />)}</td>)}</tr>)}</tbody></table></div></section>
        <section className="performance-card panel"><div className="finding-heading"><span>Performance comparison</span><span className={`comparability-pill${result.performance_comparison?.comparable ? " comparable" : ""}`}>{result.performance_comparison?.comparable ? "Comparable evidence found" : "Not directly comparable"}</span></div><p>{result.performance_comparison?.text}</p>{result.performance_comparison?.comparable && <div className="comparison-details"><span>Metric: {result.performance_comparison.metric}</span><span>Dataset: {result.performance_comparison.dataset}</span><span>Conditions: {result.performance_comparison.conditions}</span></div>}{result.performance_comparison?.sources.map((source) => <SourceCard source={source} compact key={source.chunk_id} />)}</section>
        <div className="comparison-points-grid">{[
          ["Similarities", result.similarities], ["Differences", result.differences], ["Methodological strengths", result.methodological_strengths], ["Methodological weaknesses", result.methodological_weaknesses], ["Dataset differences", result.dataset_differences], ["Research opportunities", result.research_opportunities],
        ].map(([title, values]) => <section className="panel point-panel" key={String(title)}><div className="panel-heading"><div><h2>{String(title)}</h2></div></div>{Array.isArray(values) && values.length ? <ul>{values.map((point, index) => <li key={`${point.text}-${index}`}><p>{point.text}</p>{point.sources.map((source) => <SourceCard source={source} compact key={source.chunk_id} />)}</li>)}</ul> : <p className="points-empty">No source-supported points were returned.</p>}</section>)}
        </div>
      </>}
    </div>
  );
}
