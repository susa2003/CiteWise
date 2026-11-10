import { ArrowRight, BookOpenCheck, FileSearch, Network, ShieldCheck, Upload, Workflow } from "lucide-react";
import { Link } from "react-router-dom";

const capabilities = [
  { icon: FileSearch, title: "Read with evidence", text: "Keep every extracted passage tied to its original paper and page." },
  { icon: Workflow, title: "Connect papers", text: "Compare methods and results with their datasets and conditions in view." },
  { icon: Network, title: "Explore open questions", text: "Separate author-stated limitations from inferred research opportunities." },
];

export default function LandingPage() {
  return (
    <div className="landing-page">
      <section className="landing-hero">
        <div className="landing-copy">
          <div className="eyebrow"><span className="eyebrow-dot" /> EVIDENCE FIRST. ALWAYS.</div>
          <h1>Your next research insight<br />starts with a better question.</h1>
          <p>Bring your papers together. Trace the evidence, compare the ideas, and find the questions worth asking next.</p>
          <div className="landing-actions"><Link className="primary-button" to="/library"><Upload size={16} /> Add your first paper <ArrowRight size={14} /></Link><Link className="quiet-link" to="/dashboard">Explore workspace</Link></div>
          <div className="trust-line"><ShieldCheck size={15} /> Every source keeps its original page reference.</div>
        </div>
        <div className="hero-visual" aria-label="Illustration of a research paper with its citation evidence">
          <div className="visual-glow" />
          <div className="visual-paper back-paper"><span /><span /><span /><span /></div>
          <div className="visual-paper main-paper"><div className="visual-paper-tag">EVIDENCE VIEW · ILLUSTRATION</div><strong>Your paper’s findings, linked to their source page</strong><i /><span /><span /><span /><div className="highlight-line" /><span /><span /></div>
          <div className="citation-bubble"><BookOpenCheck size={15} /><span><b>Source pages preserved</b><small>Open evidence from your papers</small></span></div>
          <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
        </div>
      </section>
      <section className="landing-capabilities">
        <div className="landing-section-title"><div><span className="section-kicker">A RESEARCH WORKSPACE</span><h2>Move from reading to understanding.</h2></div><p>Built to keep AI suggestions close to the evidence that supports them.</p></div>
        <div className="capability-grid">{capabilities.map(({ icon: Icon, title, text }) => <article className="capability-card" key={title}><span className="capability-icon"><Icon size={18} /></span><h3>{title}</h3><p>{text}</p><span className="capability-arrow"><ArrowRight size={15} /></span></article>)}</div>
      </section>
      <section className="landing-footer"><span>CiteWise AI</span><span>Research intelligence for careful readers</span><Link to="/library">Start with a paper <ArrowRight size={13} /></Link></section>
    </div>
  );
}
