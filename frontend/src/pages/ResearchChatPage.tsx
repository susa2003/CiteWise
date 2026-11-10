import { useEffect, useMemo, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { ArrowDown, ArrowUp, BookOpenCheck, ChevronDown, LoaderCircle, MessageSquareText, Plus, Sparkles } from "lucide-react";
import { PageHeading, Notice } from "../components/PageHeading";
import { SourceCard } from "../components/SourceCard";
import { api, errorMessage } from "../services/api";
import type { ChatResponse, DocumentList, DocumentRecord, SourceResult } from "../types/research";

type ChatEntry = { role: "user" | "assistant"; content: string; result?: ChatResponse };
type SavedConversation = { id: string; title: string; created_at: string; updated_at: string };

const examples = ["What is the main objective?", "Which evaluation metrics are used?", "What limitations do the authors mention?"];

export default function ResearchChatPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [history, setHistory] = useState<SavedConversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [scopeOpen, setScopeOpen] = useState(false);

  const readyDocuments = useMemo(() => documents.filter((item) => ["processed", "processed_with_warnings"].includes(item.status)), [documents]);

  async function loadWorkspace() {
    try {
      const [library, conversations] = await Promise.all([
        api.get<DocumentList>("/documents", { params: { limit: 100 } }),
        api.get<SavedConversation[]>("/conversations"),
      ]);
      setDocuments(library.data.items);
      setSelectedIds((current) => current.length ? current.filter((id) => library.data.items.some((doc) => doc.id === id)) : library.data.items.map((doc) => doc.id));
      setHistory(conversations.data);
    } catch (reason) { setError(errorMessage(reason)); }
  }

  useEffect(() => { void loadWorkspace(); }, []);

  function toggleDocument(id: string) {
    setSelectedIds((current) => current.includes(id) ? current.filter((value) => value !== id) : [...current, id]);
  }

  async function sendQuestion(event?: FormEvent) {
    event?.preventDefault();
    const question = draft.trim();
    if (!question || sending) return;
    setDraft(""); setError(""); setSending(true);
    setEntries((current) => [...current, { role: "user", content: question }]);
    try {
      const response = await api.post<ChatResponse>("/chat", {
        question,
        conversation_id: conversationId,
        document_ids: selectedIds.length === readyDocuments.length ? undefined : selectedIds,
      });
      setConversationId(response.data.conversation_id);
      setEntries((current) => [...current, { role: "assistant", content: response.data.answer, result: response.data }]);
      const conversations = await api.get<SavedConversation[]>("/conversations");
      setHistory(conversations.data);
    } catch (reason) {
      setEntries((current) => [...current, { role: "assistant", content: errorMessage(reason) }]);
    } finally { setSending(false); }
  }

  async function loadConversation(id: string) {
    setError(""); setSending(true);
    try {
      const response = await api.get<{ id: string; messages: { role: "user" | "assistant"; content: string; answer_mode: string | null; insufficient_evidence: boolean | null; citations: { chunk_id: string | null; document_id: string; filename: string; page_number: number; excerpt: string; citation_type: string }[] }[] }>(`/conversations/${id}`);
      setConversationId(id);
      setEntries(response.data.messages.map((message) => ({
        role: message.role,
        content: message.content,
        result: message.role === "assistant" ? {
          conversation_id: id,
          answer: message.content,
          mode: message.answer_mode || "retrieval_only",
          evidence_found: message.citations.length > 0,
          insufficient_evidence: message.insufficient_evidence ?? false,
          claims: [],
          sources: message.citations.map((source) => ({
            chunk_id: source.chunk_id || "deleted-source",
            document_id: source.document_id,
            filename: source.filename,
            page_number: source.page_number,
            section_heading: null,
            excerpt: source.excerpt,
            score: 0,
          } satisfies SourceResult)),
        } : undefined,
      })));
    } catch (reason) { setError(errorMessage(reason)); }
    finally { setSending(false); }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void sendQuestion(); }
  }

  return (
    <div className="page-stack chat-page">
      <PageHeading eyebrow="ASK YOUR PAPERS" title="Research chat." description="Ask across your papers and inspect the passages behind each response." action={<button className="outline-button" onClick={() => { setConversationId(null); setEntries([]); setDraft(""); }}><Plus size={14} /> New conversation</button>} />
      {error && <Notice tone="error">{error}</Notice>}
      <div className="chat-layout">
        <aside className="panel chat-history-panel">
          <div className="panel-heading"><div><h2>Recent conversations</h2><p>History stays in this local workspace.</p></div></div>
          {history.length ? <div className="conversation-list">{history.map((item) => <button key={item.id} className={`conversation-item${conversationId === item.id ? " current" : ""}`} onClick={() => void loadConversation(item.id)}><MessageSquareText size={14} /><span><strong>{item.title}</strong><small>{new Date(item.updated_at).toLocaleDateString()}</small></span></button>)}</div> : <p className="history-empty">Your conversations will appear here.</p>}
        </aside>
        <section className="panel chat-panel">
          <div className="chat-toolbar"><div className="chat-scope-wrap"><button className="scope-button" onClick={() => setScopeOpen((open) => !open)}><BookOpenCheck size={15} />{selectedIds.length === readyDocuments.length ? `All papers (${readyDocuments.length})` : `${selectedIds.length} selected`}<ChevronDown size={13} /></button>{scopeOpen && <div className="scope-menu"><strong>Search in papers</strong>{readyDocuments.length ? readyDocuments.map((document) => <label key={document.id}><input type="checkbox" checked={selectedIds.includes(document.id)} onChange={() => toggleDocument(document.id)} />{document.title || document.original_filename}</label>) : <p>Upload a processed PDF to start chatting.</p>}<button className="text-button" onClick={() => setSelectedIds(readyDocuments.map((item) => item.id))}>Select all</button></div>}</div><span className="mode-chip"><Sparkles size={13} /> Evidence-grounded</span></div>
          <div className="chat-messages">
            {entries.length === 0 ? <div className="chat-welcome"><span className="chat-welcome-icon"><Sparkles size={20} /></span><h2>What would you like to understand?</h2><p>Choose a paper scope and ask about methods, results, or limitations. CiteWise keeps source excerpts beside its responses.</p><div className="prompt-suggestions">{examples.map((example) => <button key={example} onClick={() => setDraft(example)}>{example}<ArrowUp size={12} /></button>)}</div></div> : entries.map((entry, index) => <div className={`chat-message ${entry.role}`} key={`${index}-${entry.content.slice(0, 10)}`}><div className="message-avatar">{entry.role === "assistant" ? <BookOpenCheck size={15} /> : "You"}</div><div className="message-body"><div className="message-label">{entry.role === "assistant" ? "CITEWISE" : "YOU"}{entry.result && <span className={`mode-label ${entry.result.mode}`}>{entry.result.mode.replaceAll("_", " ")}</span>}</div><p>{entry.content}</p>{entry.result?.claims.map((claim, claimIndex) => <div className="claim-card" key={`${claim.text}-${claimIndex}`}><span className={`claim-kind ${claim.interpretation ? "interpretation" : "fact"}`}>{claim.interpretation ? "Interpretation" : "Source-supported statement"}</span><p>{claim.text}</p>{claim.citations.map((source) => <SourceCard source={source} key={source.chunk_id} />)}</div>)}{entry.result && entry.result.claims.length === 0 && entry.result.sources.length > 0 && <div className="retrieved-sources"><span>Retrieved paper passages</span>{entry.result.sources.map((source) => <SourceCard source={source} key={source.chunk_id} />)}</div>}</div></div>)}
            {sending && <div className="chat-message assistant"><div className="message-avatar"><BookOpenCheck size={15} /></div><div className="message-body"><div className="message-label">CITEWISE</div><p className="typing-state"><LoaderCircle className="spin" size={14} /> Searching selected papers…</p></div></div>}
          </div>
          <form className="chat-composer" onSubmit={(event) => void sendQuestion(event)}><textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={onKeyDown} placeholder="Ask a question about your papers…" aria-label="Your research question" rows={2} disabled={readyDocuments.length === 0 || sending} /><div className="composer-footer"><span>Enter to send · Shift + Enter for a new line</span><button className="send-button" type="submit" disabled={!draft.trim() || sending || readyDocuments.length === 0} aria-label="Send question">{sending ? <LoaderCircle className="spin" size={16} /> : <ArrowDown size={16} />}</button></div></form>
        </section>
      </div>
    </div>
  );
}
