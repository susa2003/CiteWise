import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ArrowRight, BookOpenCheck, CircleAlert, FileSearch, FlaskConical, Upload } from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Notice, PageHeading } from "../components/PageHeading";
import { api, errorMessage } from "../services/api";
import type { DashboardData } from "../types/research";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true); setError("");
    try { const response = await api.get<DashboardData>("/dashboard"); setData(response.data); }
    catch (reason) { setError(errorMessage(reason)); }
    finally { setLoading(false); }
  }

  useEffect(() => { void load(); }, []);

  return (
    <div className="page-stack">
      <PageHeading eyebrow="YOUR WORKSPACE" title="Research at a glance." description="A clear view of your papers, evidence, and recent research work." action={<Link className="primary-button" to="/library"><Upload size={15} /> Upload papers</Link>} />
      {error && <Notice tone="error">{error} <button className="inline-button" onClick={() => void load()}>Retry</button></Notice>}
      <section className="stats-grid">
        <Metric icon={BookOpenCheck} label="Papers in library" value={data?.total_documents ?? (loading ? "…" : "0")} note={`${data?.processed_documents ?? 0} processed`} />
        <Metric icon={FileSearch} label="Evidence indexed" value={data?.total_chunks ?? (loading ? "…" : "0")} note="Page-linked text chunks" />
        <Metric icon={FlaskConical} label="Research analyses" value={data?.analysis_history.length ?? (loading ? "…" : "0")} note="Saved analysis history" />
        <Metric icon={CircleAlert} label="Needs attention" value={data?.failed_documents ?? (loading ? "…" : "0")} note={`${data?.processing_documents ?? 0} processing`} />
      </section>

      <section className="dashboard-grid">
        <div className="panel dashboard-panel">
          <div className="panel-heading"><div><h2>Recent papers</h2><p>Latest documents added to your workspace.</p></div><Link className="text-button" to="/library">Open library <ArrowRight size={13} /></Link></div>
          {data?.recent_documents.length ? <div className="recent-list">{data.recent_documents.map((doc) => <Link className="recent-row" to={`/library?doc=${doc.id}`} key={doc.id}><span className="document-icon"><BookOpenCheck size={16} /></span><span className="recent-name"><strong>{doc.title || doc.original_filename}</strong><small>{doc.original_filename} · {doc.page_count} pages</small></span><StatusTag status={doc.status} /><ArrowRight size={14} className="muted-arrow" /></Link>)}</div> : <EmptyPanel title={loading ? "Loading your library…" : "Your library is ready"} text="Upload a paper and its processing activity will appear here." action={<Link className="secondary-button" to="/library"><Upload size={14} /> Add a PDF</Link>} />}
        </div>

        <div className="panel dashboard-panel chart-panel">
          <div className="panel-heading"><div><h2>Papers by year</h2><p>Publication years found in PDF metadata.</p></div></div>
          {data?.papers_by_year.length ? <div className="chart-wrap"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.papers_by_year} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}><CartesianGrid vertical={false} stroke="#edf0ed" /><XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: "#929b94", fontSize: 10 }} /><YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: "#a0a9a1", fontSize: 9 }} /><Tooltip cursor={{ fill: "#f3f7f3" }} contentStyle={{ border: "1px solid #e4ebe4", borderRadius: 8, fontSize: 11 }} /><Bar dataKey="count" name="Papers" fill="#4d8b63" radius={[5, 5, 0, 0]} maxBarSize={36} /></BarChart></ResponsiveContainer></div> : <EmptyPanel title="No year data yet" text="Publication year metadata will appear here when found in uploaded PDFs." />}
        </div>

        <div className="panel dashboard-panel keyword-panel">
          <div className="panel-heading"><div><h2>Frequently used keywords</h2><p>Terms extracted from paper metadata.</p></div></div>
          {data?.frequent_keywords.length ? <div className="keyword-list">{data.frequent_keywords.map((item) => <div className="keyword-row" key={item.label}><span>{item.label}</span><i style={{ width: `${Math.max(10, item.count / data.frequent_keywords[0].count * 100)}%` }} /><b>{item.count}</b></div>)}</div> : <EmptyPanel title="Keywords will collect here" text="Author keywords are shown when available in the PDF." />}
        </div>

        <div className="panel dashboard-panel history-panel">
          <div className="panel-heading"><div><h2>Recent activity</h2><p>Your saved analysis work.</p></div></div>
          {data?.analysis_history.length ? <div className="activity-list">{data.analysis_history.slice(0, 5).map((item) => <div className="activity-row" key={item.id}><span className="activity-dot" /><span><strong>{item.kind.replaceAll("_", " ")}</strong><small>{new Date(item.created_at).toLocaleString()}</small></span></div>)}</div> : <EmptyPanel title="No analyses yet" text="Run an analysis, comparison, or summary to build your history." />}
        </div>
      </section>
      {data?.failed_documents ? <Notice tone="info">{data.failed_documents} document{data.failed_documents === 1 ? " needs" : "s need"} attention. Review its processing warning in the library.</Notice> : null}
    </div>
  );
}

function Metric({ icon: Icon, label, value, note }: { icon: typeof BookOpenCheck; label: string; value: string | number; note: string }) {
  return <div className="metric-card"><div className="metric-icon sage"><Icon size={17} /></div><div className="metric-label">{label}</div><strong className="metric-value">{value}</strong><div className="metric-note">{note}</div></div>;
}

function StatusTag({ status }: { status: string }) {
  return <span className={`status-tag ${status}`}>{status.replaceAll("_", " ")}</span>;
}

function EmptyPanel({ title, text, action }: { title: string; text: string; action?: ReactNode }) {
  return <div className="dashboard-empty"><strong>{title}</strong><p>{text}</p>{action}</div>;
}
