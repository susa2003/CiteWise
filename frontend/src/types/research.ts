export type DocumentStatus = "processing" | "processed" | "processed_with_warnings" | "failed";

export interface DocumentRecord {
  id: string;
  original_filename: string;
  status: DocumentStatus;
  file_size: number;
  title: string | null;
  authors: string[];
  abstract: string | null;
  publication_year: number | null;
  doi: string | null;
  keywords: string[];
  references: string[];
  metadata_sources: Record<string, string>;
  page_count: number;
  chunk_count: number;
  warnings: string[];
  processing_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: DocumentRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface SourceResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  section_heading: string | null;
  excerpt: string;
  score: number;
}

export interface DocumentPage {
  document_id: string;
  original_filename: string;
  page_number: number;
  section_heading: string | null;
  extraction_method: string;
  warnings: string[];
  text: string;
}

export interface DashboardData {
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  processing_documents: number;
  total_chunks: number;
  recent_documents: DocumentRecord[];
  papers_by_year: { label: string; count: number }[];
  frequent_keywords: { label: string; count: number }[];
  analysis_history: { id: string; kind: string; document_ids: string[]; created_at: string }[];
  recent_comparisons: { id: string; kind: string; document_ids: string[]; created_at: string }[];
}

export interface AnalysisFinding {
  category: string;
  text: string;
  sources: SourceResult[];
}

export interface AnalysisResponse {
  mode: string;
  message: string | null;
  run_id: string | null;
  document_id: string;
  findings: AnalysisFinding[];
}

export interface ComparisonPaperFinding {
  document_id: string;
  filename: string;
  text: string;
  sources: SourceResult[];
}

export interface ComparisonPoint {
  text: string;
  sources: SourceResult[];
}

export interface ComparisonResponse {
  mode: string;
  message: string | null;
  run_id: string | null;
  document_ids: string[];
  categories: { category: string; papers: ComparisonPaperFinding[] }[];
  similarities: ComparisonPoint[];
  differences: ComparisonPoint[];
  methodological_strengths: ComparisonPoint[];
  methodological_weaknesses: ComparisonPoint[];
  dataset_differences: ComparisonPoint[];
  research_opportunities: ComparisonPoint[];
  performance_comparison: { comparable: boolean; text: string; metric: string | null; dataset: string | null; conditions: string | null; sources: SourceResult[] } | null;
}

export interface GapFinding {
  title: string;
  explanation: string;
  kind: "explicit_limitation" | "inferred_opportunity" | "hypothesis";
  sources: SourceResult[];
  why_it_matters: string;
  possible_direction: string;
  suggested_experiments: string[];
  potential_metrics: string[];
}

export interface GapResponse {
  mode: string;
  message: string | null;
  run_id: string | null;
  document_ids: string[];
  gaps: GapFinding[];
}

export interface SummaryResponse {
  mode: string;
  message: string | null;
  run_id: string | null;
  document_id: string;
  format: string;
  sections: { heading: string; text: string; interpretation: boolean; sources: SourceResult[] }[];
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  mode: string;
  evidence_found: boolean;
  insufficient_evidence: boolean;
  claims: { text: string; interpretation: boolean; citations: SourceResult[] }[];
  sources: SourceResult[];
}

export interface PublicSettings {
  environment: string;
  max_upload_mb: number;
  llm_provider: string;
  llm_configured: boolean;
  embedding_provider: string;
  semantic_available: boolean;
  ocr_enabled: boolean;
  demo_mode: boolean;
}
