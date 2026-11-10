import { useEffect, useState } from "react";
import { Check, Clipboard, ExternalLink, KeyRound, ServerCog, ShieldCheck, Sparkles } from "lucide-react";
import { Notice, PageHeading } from "../components/PageHeading";
import { api, errorMessage } from "../services/api";
import type { PublicSettings } from "../types/research";

export default function SettingsPage() {
  const [settings, setSettings] = useState<PublicSettings | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const apiRoot = (api.defaults.baseURL || "http://127.0.0.1:8000/api").replace(/\/api\/?$/, "");

  useEffect(() => { api.get<PublicSettings>("/settings").then(({ data }) => setSettings(data)).catch((reason) => setError(errorMessage(reason))); }, []);

  async function copyConfig() {
    const config = "CITEWISE_LLM_PROVIDER=openai_compatible\nCITEWISE_LLM_API_KEY=your_api_key\nCITEWISE_LLM_MODEL=your_model\nCITEWISE_LLM_BASE_URL=https://api.openai.com/v1";
    try { await navigator.clipboard.writeText(config); setCopied(true); setTimeout(() => setCopied(false), 1800); }
    catch { setError("Clipboard access is unavailable in this browser. Copy the example from the backend .env.example file."); }
  }

  return (
    <div className="page-stack">
      <PageHeading eyebrow="WORKSPACE CONFIGURATION" title="Your settings." description="Review runtime capabilities and configure optional services through the local environment file." />
      {error && <Notice tone="error">{error}</Notice>}
      <section className="panel settings-overview"><div className="settings-state-icon"><Sparkles size={19} /></div><div className="settings-state-copy"><span className="section-kicker">CURRENT MODE</span><h2>{settings?.demo_mode ? "Demo mode" : "AI provider connected"}</h2><p>{settings?.demo_mode ? "PDF upload, extraction, metadata, and keyword retrieval work without paid AI credentials. Generated analysis stays unavailable until an LLM is configured." : `Connected to ${settings?.llm_provider}. Generated responses still require validated paper citations.`}</p></div><span className={`status-tag ${settings?.llm_configured ? "processed" : "processing"}`}>{settings?.llm_configured ? "AI configured" : "No LLM key"}</span></section>

      <div className="settings-grid">
        <section className="panel settings-card"><div className="settings-card-icon"><KeyRound size={17} /></div><h2>Language model</h2><p>Provider credentials stay on the backend in <code>.env</code>. They are never returned by the settings API or saved in the browser.</p><div className="settings-kv"><span>Provider</span><strong>{settings?.llm_provider || "Loading…"}</strong><span>Model configured</span><strong>{settings?.llm_configured ? "Yes" : "No"}</strong><span>API key value</span><strong className="private-value">Hidden from this app</strong></div><button className="outline-button" onClick={() => void copyConfig()}>{copied ? <Check size={14} /> : <Clipboard size={14} />}{copied ? "Copied example" : "Copy .env example"}</button></section>

        <section className="panel settings-card"><div className="settings-card-icon blue"><ServerCog size={17} /></div><h2>Retrieval and OCR</h2><p>Optional local capabilities can be enabled without changing the default keyword-only demo setup.</p><div className="settings-kv"><span>Semantic provider</span><strong>{settings?.embedding_provider || "Loading…"}</strong><span>Vector and model packages</span><strong>{settings?.semantic_available ? "Available" : "Not installed"}</strong><span>OCR setting</span><strong>{settings?.ocr_enabled ? "Enabled" : "Disabled"}</strong><span>Upload limit</span><strong>{settings ? `${settings.max_upload_mb} MB per PDF` : "Loading…"}</strong></div><pre className="code-snippet">python -m pip install -r backend/requirements-rag.txt</pre><pre className="code-snippet">python -m pip install -r backend/requirements-ocr.txt</pre></section>

        <section className="panel settings-card security-settings"><div className="settings-card-icon sage"><ShieldCheck size={17} /></div><h2>Documents and privacy</h2><p>Uploaded PDFs and local indexes stay inside the workspace storage directory. Storage is excluded from Git by default.</p><ul><li>Only PDF uploads are accepted.</li><li>Filename paths are replaced with generated storage IDs.</li><li>Page and chunk references are stored with original page numbers.</li><li>Delete a paper from the library to remove its stored file and derived index.</li></ul><a href={`${apiRoot}/docs`} target="_blank" rel="noreferrer">Open API documentation <ExternalLink size={12} /></a></section>

        <section className="panel settings-card run-settings"><h2>Local server</h2><p>Settings are loaded when the backend starts. After editing <code>.env</code>, restart the API and refresh this page.</p><div className="run-commands"><code>Backend · uvicorn backend.app.main:app --reload</code><code>Frontend · npm run dev</code></div></section>
      </div>
      <div className="settings-footer">Runtime: {settings?.environment || "—"} <span>·</span> API reports no credential values.</div>
    </div>
  );
}
