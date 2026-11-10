import { lazy, Suspense, useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { Activity, ArrowUpRight, BookOpenCheck, ChartNoAxesCombined, FileSearch, House, Layers3, MessageSquareText, Moon, Network, Settings2, ShieldCheck, Sun, Workflow } from "lucide-react";
const LandingPage = lazy(() => import("../pages/LandingPage"));
const DashboardPage = lazy(() => import("../pages/DashboardPage"));
const DocumentsPage = lazy(() => import("../pages/DocumentsPage"));
const AnalysisPage = lazy(() => import("../pages/AnalysisPage"));
const ResearchChatPage = lazy(() => import("../pages/ResearchChatPage"));
const ComparisonPage = lazy(() => import("../pages/ComparisonPage"));
const GapExplorerPage = lazy(() => import("../pages/GapExplorerPage"));
const SummaryPage = lazy(() => import("../pages/SummaryPage"));
const SettingsPage = lazy(() => import("../pages/SettingsPage"));
import { api } from "../services/api";
import type { HealthResponse } from "../types/api";

const navItems = [
  { to: "/dashboard", label: "Overview", icon: Layers3 },
  { to: "/library", label: "My papers", icon: BookOpenCheck },
  { to: "/analysis", label: "Paper analysis", icon: FileSearch },
  { to: "/chat", label: "Research chat", icon: MessageSquareText },
  { to: "/compare", label: "Compare papers", icon: Workflow },
  { to: "/gaps", label: "Research gaps", icon: Network },
  { to: "/summaries", label: "Summaries", icon: ChartNoAxesCombined },
  { to: "/settings", label: "Settings", icon: Settings2 },
];

const titles: Record<string, string> = {
  "/": "Welcome",
  "/dashboard": "Overview",
  "/library": "My papers",
  "/analysis": "Paper analysis",
  "/chat": "Research chat",
  "/compare": "Compare papers",
  "/gaps": "Research gaps",
  "/summaries": "Summaries",
  "/settings": "Settings",
};

export default function App() {
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [connectionError, setConnectionError] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem("citewise-theme") === "dark");

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("citewise-theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    let active = true;
    const check = () => api.get<HealthResponse>("/health").then(({ data }) => {
      if (active) { setHealth(data); setConnectionError(false); }
    }).catch(() => { if (active) { setHealth(null); setConnectionError(true); } });
    void check();
    const interval = window.setInterval(() => void check(), 30_000);
    return () => { active = false; window.clearInterval(interval); };
  }, []);

  const pageTitle = titles[location.pathname] ?? "CiteWise AI";
  const apiRoot = (api.defaults.baseURL || "http://127.0.0.1:8000/api").replace(/\/api\/?$/, "");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="CiteWise home"><span className="brand-mark"><BookOpenCheck size={19} strokeWidth={2.2} /></span><span><strong>citewise</strong><small>RESEARCH INTELLIGENCE</small></span></a>
        <div className="workspace-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <NavLink className={({ isActive }) => `nav-item${isActive ? " active" : ""}`} to="/"><House size={17} strokeWidth={1.8} /><span>Welcome</span></NavLink>
          {navItems.map(({ to, label, icon: Icon }) => <NavLink className={({ isActive }) => `nav-item${isActive ? " active" : ""}`} to={to} key={to}><Icon size={17} strokeWidth={1.8} /><span>{label}</span></NavLink>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="evidence-card"><span className="evidence-icon"><ShieldCheck size={16} /></span><strong>Evidence first</strong><p>Every generated insight can be checked against its source.</p></div>
          <div className="profile-row"><div className="avatar">CW</div><div><strong>Research workspace</strong><small>Local environment</small></div><Activity size={15} /></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar"><div className="breadcrumbs"><a href="/">Workspace</a><span>/</span><strong>{pageTitle}</strong></div><div className="topbar-right"><span className={`api-status ${health ? "online" : connectionError ? "offline" : "checking"}`}><i />{health ? "API connected" : connectionError ? "API unavailable" : "Connecting"}</span><button className="icon-button" aria-label={dark ? "Switch to light theme" : "Switch to dark theme"} title={dark ? "Switch to light theme" : "Switch to dark theme"} onClick={() => setDark((current) => !current)}>{dark ? <Sun size={16} /> : <Moon size={16} />}</button><a className="docs-link" href={`${apiRoot}/docs`} target="_blank" rel="noreferrer">API docs <ArrowUpRight size={13} /></a><div className="avatar small">CW</div></div></header>
        <div className="page-content"><Suspense fallback={<div className="page-loading"><Activity className="spin" size={17} /> Opening your workspace…</div>}><Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/library" element={<DocumentsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/chat" element={<ResearchChatPage />} />
          <Route path="/compare" element={<ComparisonPage />} />
          <Route path="/gaps" element={<GapExplorerPage />} />
          <Route path="/summaries" element={<SummaryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<div className="panel empty-workflow"><h2>Page not found</h2><a className="secondary-button" href="/dashboard">Open your workspace</a></div>} />
        </Routes></Suspense></div>
      </main>
    </div>
  );
}
