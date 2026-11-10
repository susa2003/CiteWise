import { useEffect, useState } from "react";
import { ArrowRight, Compass, FlaskConical, LoaderCircle, Lightbulb, ShieldAlert, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { Notice, PageHeading } from "../components/PageHeading";
import { SourceCard } from "../components/SourceCard";
import { api, errorMessage } from "../services/api";
import type { DocumentList, DocumentRecord, GapResponse } from "../types/research";

const kindLabel = { explicit_limitation: "Author-stated limitation", inferred_opportunity: "Inferred opportunity", hypothesis: "Hypothesis to investigate" };

export default function GapExplorerPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [result, setResult] = useState<GapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<DocumentList>("/documents", { params: { limit: 100 } }).then(({ data }) => {
      const ready = data.items.filter((item) => ["processed", "processed_with_warnings"].includes(item.status));
      setDocuments(ready); setSelectedIds(ready.map((item) => item.id));
    }).catch((reason) => setError(errorMessage(reason)));
  }, []);

  async function explore() {
    if (!selectedIds.length) return;
    setLoading(true); setError(""); setResult(null);
    try { const response = await api.post<GapResponse>("/gaps", { document_ids: selectedIds }); setResult(response.data); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="RESEARCH GAP EXPLORER" title="Find the open questions." description="Explore limitations and possible directions using your uploaded papers as evidence." />
      {error && <Notice tone="error">{error}</Notice>}
      <section className="panel selection-panel"><div className="panel-heading"><div><h2>Evidence scope <span className="heading-count">{selectedIds.length}</span></h2><p>Select which papers should support this exploration.</p></div><button className="primary-button" disabled={!selectedIds.length || loading} onClick={() => void explore()}>{loading ? <LoaderCircle className="spin" size={15} /> : <Compass size={15} />}{loading ? "Reviewing evidence…" : "Explore gaps"}</button></div>
        {documents.length ? <div className="paper-select-grid">{documents.map((document) => <label className={`paper-select-card${selectedIds.includes(document.id) ? " selected" : ""}`} key={document.id}><input type="checkbox" checked={selectedIds.includes(document.id)} onChange={() => { setSelectedIds((current) => current.includes(document.id) ? current.filter((id) => id !== document.id) : [...current, document.id]); setResult(null); }} /><span><strong>{document.title || document.original_filename}</strong><small>{document.original_filename} · {document.page_count} pages</small></span></label>)}</div> : <div className="selection-empty">Upload a paper to start from real source evidence. <Link to="/library">Go to library <ArrowRight size={13} /></Link></div>}
      </section>
      <div className="gap-principle"><ShieldAlert size={16} /><span><strong>Research opportunities are not novelty claims.</strong> CiteWise distinguishes what authors explicitly state from ideas inferred from this limited paper set.</span></div>
      {result?.message && <Notice tone={result.mode === "provider_error" ? "error" : "info"}>{result.message}</Notice>}
      {result?.gaps.length ? <div className="gap-grid">{result.gaps.map((gap, index) => <article className="panel gap-card" key={`${gap.title}-${index}`}><div className="gap-card-top"><span className={`gap-kind ${gap.kind}`}>{gap.kind === "explicit_limitation" ? <ShieldAlert size={13} /> : gap.kind === "inferred_opportunity" ? <Lightbulb size={13} /> : <FlaskConical size={13} />}{kindLabel[gap.kind]}</span><span className="gap-index">GAP {String(index + 1).padStart(2, "0")}</span></div><h2>{gap.title}</h2><p className="gap-explanation">{gap.explanation}</p><div className="gap-subsection"><strong>Why it matters</strong><p>{gap.why_it_matters}</p></div><div className="gap-subsection"><strong>Possible research direction</strong><p>{gap.possible_direction}</p></div><div className="gap-list-block"><strong>Suggested experiments</strong><ul>{gap.suggested_experiments.map((item) => <li key={item}>{item}</li>)}</ul></div><div className="gap-list-block"><strong>Potential evaluation metrics</strong><div className="tag-list">{gap.potential_metrics.map((item) => <span key={item}>{item}</span>)}</div></div><div className="gap-sources"><span>Supporting evidence</span>{gap.sources.map((source) => <SourceCard source={source} compact key={source.chunk_id} />)}</div></article>)}</div> : result?.mode === "llm_grounded" ? <div className="panel empty-workflow"><span><Sparkles size={20} /></span><h2>No source-supported gaps returned</h2><p>This does not prove that no open questions exist. Review the selected papers or widen the evidence scope.</p></div> : null}
    </div>
  );
}
