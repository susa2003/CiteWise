import { FileSearch, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import type { SourceResult } from "../types/research";

export function SourceCard({ source, compact = false }: { source: SourceResult; compact?: boolean }) {
  return (
    <details className={`source-card${compact ? " compact" : ""}`}>
      <summary>
        <span className="source-mark"><FileSearch size={14} /></span>
        <span className="source-name"><strong>{source.filename}</strong><small>Page {source.page_number}{source.section_heading ? ` · ${source.section_heading}` : ""}</small></span>
        <span className="source-open">Evidence</span>
      </summary>
      {!compact && <p className="source-excerpt">“{source.excerpt}”</p>}
      <Link className="source-link" to={`/library?doc=${encodeURIComponent(source.document_id)}&page=${source.page_number}`}>
        Open cited page <ExternalLink size={12} />
      </Link>
    </details>
  );
}
