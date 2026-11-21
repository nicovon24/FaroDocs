"use client";

import { useEffect, useState } from "react";
import "./styles.css";

type Language = "es" | "en";

const copy = {
  es: {
    local: "Vista local", library: "Biblioteca", search: "Búsqueda", chats: "Conversaciones",
    planned: "En desarrollo", workspace: "Espacio personal", heading: "Tu biblioteca",
    intro: "Un lugar para reunir documentos y volver a cada fuente con contexto.",
    emptyHeading: "Todavía no hay documentos",
    emptyBody: "La carga de PDF, DOCX, TXT y Markdown es la próxima función en desarrollo. Cuando esté lista, vas a ver aquí cada archivo y su estado de procesamiento.",
    next: "Siguiente etapa: carga y biblioteca", statusHeading: "Estado de esta vista",
    statusBody: "La aplicación ya inicia localmente. La organización de documentos, la búsqueda y el chat aún no están habilitados.",
    footer: "Vista de desarrollo para una persona · Sin cuenta de Google todavía",
  },
  en: {
    local: "Local preview", library: "Library", search: "Search", chats: "Conversations",
    planned: "In development", workspace: "Personal space", heading: "Your library",
    intro: "A place to gather documents and return to each source in context.",
    emptyHeading: "No documents yet",
    emptyBody: "PDF, DOCX, TXT and Markdown uploads are the next feature in development. Once available, each file and its processing status will appear here.",
    next: "Next stage: upload and library", statusHeading: "About this preview",
    statusBody: "The application now starts locally. Document organization, search and chat are not available yet.",
    footer: "Single-user development preview · No Google account yet",
  },
} as const;

function DocumentIcon() {
  return <svg viewBox="0 0 96 112" fill="none" aria-hidden="true">
    <path d="M20 3h38l23 23v78a5 5 0 0 1-5 5H20a5 5 0 0 1-5-5V8a5 5 0 0 1 5-5Z" fill="#FFFEFB" stroke="#17263D" strokeWidth="2" />
    <path d="M58 3v20a3 3 0 0 0 3 3h20" stroke="#17263D" strokeWidth="2" />
    <path d="M28 49h39M28 63h39M28 77h27" stroke="#A7B4BB" strokeWidth="3" strokeLinecap="round" />
    <rect x="7" y="86" width="29" height="20" rx="4" fill="#A84128" />
    <path d="M14 96h15" stroke="#FFFEFB" strokeWidth="2" strokeLinecap="round" />
  </svg>;
}

function NavIcon({ kind }: { kind: "library" | "search" | "chats" }) {
  const path = {
    library: <><path d="M4 5h16v14H4z" /><path d="M8 9h8M8 13h8" /></>,
    search: <><circle cx="10.5" cy="10.5" r="6" /><path d="m15 15 5 5" /></>,
    chats: <><path d="M4 5h16v12H9l-5 3V5Z" /><path d="M8 9h8M8 13h5" /></>,
  }[kind];
  return <svg className="nav-symbol" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{path}</svg>;
}

export default function Home() {
  const [language, setLanguage] = useState<Language>("es");
  const t = copy[language];

  useEffect(() => { document.documentElement.lang = language; }, [language]);

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand" aria-label="FaroDocs"><span className="brand-mark" aria-hidden="true">F</span><span>Faro<span className="brand-light">Docs</span></span></div>
      <div className="topbar-actions">
        <span className="local-badge"><span className="badge-dot" />{t.local}</span>
        <div className="language-switch" role="group" aria-label={language === "es" ? "Idioma" : "Language"}>
          <button type="button" className={language === "es" ? "selected" : ""} onClick={() => setLanguage("es")} aria-pressed={language === "es"}>ES</button>
          <button type="button" className={language === "en" ? "selected" : ""} onClick={() => setLanguage("en")} aria-pressed={language === "en"}>EN</button>
        </div>
      </div>
    </header>
    <div className="app-body">
      <aside className="sidebar" aria-label={language === "es" ? "Navegación" : "Navigation"}>
        <p className="sidebar-label">{t.workspace}</p>
        <nav aria-label={language === "es" ? "Navegación" : "Navigation"}>
          <span className="nav-item active" aria-current="page"><NavIcon kind="library" />{t.library}</span>
          <span className="nav-item unavailable"><NavIcon kind="search" />{t.search}<small>{t.planned}</small></span>
          <span className="nav-item unavailable"><NavIcon kind="chats" />{t.chats}<small>{t.planned}</small></span>
        </nav>
        <p className="sidebar-footer">{t.footer}</p>
      </aside>
      <main className="content">
        <div className="page-heading"><h1>{t.heading}</h1><p>{t.intro}</p></div>
        <section className="empty-library" aria-labelledby="empty-heading">
          <div className="empty-illustration"><DocumentIcon /></div>
          <h2 id="empty-heading">{t.emptyHeading}</h2>
          <p>{t.emptyBody}</p>
          <span className="stage-note">{t.next}</span>
        </section>
        <section className="status-section" aria-labelledby="status-heading">
          <h2 id="status-heading">{t.statusHeading}</h2><p>{t.statusBody}</p>
        </section>
      </main>
    </div>
  </div>;
}
