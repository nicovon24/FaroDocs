"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import "./styles.css";

type Language = "es" | "en";
type Item = { id: string; name: string };
type DocumentRow = {
  id: string; title: string; folder_id: string | null; version_id: string; filename: string;
  version_number: number; status: "queued" | "processing" | "ready" | "failed";
  error_message: string | null; favorite: boolean; tags: Item[];
};
type Version = { id: string; version_number: number; filename: string; status: DocumentRow["status"]; error_message: string | null; is_current: boolean; job_id: string | null; can_retry: boolean };
type Passage = { id: string; ordinal: number; text_content: string; locator: Record<string, number | string> };

const copy = {
  es: {
    local: "Vista local", library: "Biblioteca", search: "Búsqueda", chats: "Conversaciones", planned: "Próximamente",
    workspace: "Espacio personal", heading: "Tu biblioteca", intro: "Guardá documentos y volvé a cada pasaje con su fuente original.",
    upload: "Subir documentos", uploadHint: "PDF, DOCX, TXT o Markdown · Hasta 10 MiB · PDF de hasta 100 páginas",
    empty: "Todavía no hay documentos", emptyBody: "Subí un archivo para empezar a construir tu biblioteca.",
    all: "Todos", favorites: "Favoritos", folder: "Carpeta", tag: "Etiqueta", anyFolder: "Todas las carpetas",
    anyTag: "Todas las etiquetas", filter: "Filtrar por nombre", loading: "Cargando biblioteca…",
    folderName: "Nueva carpeta", tagName: "Nueva etiqueta", add: "Crear",
    detail: "Detalle del documento", versions: "Versiones", passages: "Pasajes", noPassages: "Los pasajes aparecerán cuando termine el procesamiento.",
    original: "Abrir original", addVersion: "Subir nueva versión", title: "Título", save: "Guardar", delete: "Eliminar documento",
    deleteConfirm: "¿Eliminar este documento y todos sus archivos y pasajes? No se puede deshacer.",
    back: "Cerrar detalle", retry: "Reintentar", status: "Estado", noFolder: "Sin carpeta", chooseFolder: "Carpeta",
    tags: "Etiquetas", pending: "Procesando", failed: "Falló", ready: "Listo", queued: "En cola", processing: "Procesando",
    page: "Página", paragraph: "Bloque", offset: "Caracteres", source: "Ubicación de origen", passage: "Pasaje",
    connection: "No se pudo conectar con la API local. Revisá que Docker Compose esté iniciado.",
    uploadError: "No se pudo subir el archivo.", saveError: "No se pudieron guardar los cambios.",
    localNote: "Desarrollo local para una persona. La búsqueda, el chat y las cuentas todavía no están disponibles.",
    fileRequired: "Elegí un archivo.", selectVersion: "Elegí una versión para inspeccionar sus pasajes.",
  },
  en: {
    local: "Local preview", library: "Library", search: "Search", chats: "Conversations", planned: "Coming later",
    workspace: "Personal space", heading: "Your library", intro: "Keep documents and return to each passage with its original source.",
    upload: "Upload documents", uploadHint: "PDF, DOCX, TXT or Markdown · Up to 10 MiB · PDFs up to 100 pages",
    empty: "No documents yet", emptyBody: "Upload a file to start building your library.",
    all: "All", favorites: "Favorites", folder: "Folder", tag: "Tag", anyFolder: "All folders",
    anyTag: "All tags", filter: "Filter by name", loading: "Loading library…",
    folderName: "New folder", tagName: "New tag", add: "Create",
    detail: "Document details", versions: "Versions", passages: "Passages", noPassages: "Passages appear when processing finishes.",
    original: "Open original", addVersion: "Upload new version", title: "Title", save: "Save", delete: "Delete document",
    deleteConfirm: "Delete this document and all its files and passages? This cannot be undone.",
    back: "Close details", retry: "Retry", status: "Status", noFolder: "No folder", chooseFolder: "Folder",
    tags: "Tags", pending: "Processing", failed: "Failed", ready: "Ready", queued: "Queued", processing: "Processing",
    page: "Page", paragraph: "Block", offset: "Characters", source: "Source location", passage: "Passage",
    connection: "Could not reach the local API. Check that Docker Compose is running.",
    uploadError: "Could not upload the file.", saveError: "Could not save changes.",
    localNote: "Single-owner local development. Search, chat and accounts are not available yet.",
    fileRequired: "Choose a file.", selectVersion: "Choose a version to inspect its passages.",
  },
} as const;

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/library${path}`, { ...init, cache: "no-store" });
  const type = response.headers.get("content-type") ?? "";
  const result = type.includes("application/json") ? await response.json() : null;
  if (!response.ok) throw new Error(result?.detail ?? `HTTP ${response.status}`);
  return result as T;
}

function NavIcon({ kind }: { kind: "library" | "search" | "chats" }) {
  const shape = {
    library: <><path d="M4 5h16v14H4z" /><path d="M8 9h8M8 13h8" /></>,
    search: <><circle cx="10.5" cy="10.5" r="6" /><path d="m15 15 5 5" /></>,
    chats: <><path d="M4 5h16v12H9l-5 3V5Z" /><path d="M8 9h8M8 13h5" /></>,
  }[kind];
  return <svg className="nav-symbol" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{shape}</svg>;
}

function locatorLabel(locator: Passage["locator"], t: typeof copy[Language]) {
  if (locator.page) return `${t.page} ${locator.page}`;
  if (locator.block) return `${t.paragraph} ${locator.block}`;
  if (locator.start !== undefined) return `${t.offset} ${locator.start}–${locator.end}`;
  return t.source;
}

export default function Home() {
  const [language, setLanguage] = useState<Language>("es");
  const t = copy[language];
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [folders, setFolders] = useState<Item[]>([]);
  const [tags, setTags] = useState<Item[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [versionId, setVersionId] = useState<string | null>(null);
  const [passages, setPassages] = useState<Passage[]>([]);
  const [activePassage, setActivePassage] = useState<string | null>(null);
  const [folderFilter, setFolderFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const uploadRef = useRef<HTMLInputElement>(null);
  const versionRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (folderFilter) params.set("folder", folderFilter);
      if (tagFilter) params.set("tag", tagFilter);
      if (favoritesOnly) params.set("favorite", "true");
      if (query) params.set("q", query);
      const [rows, allFolders, allTags] = await Promise.all([
        api<DocumentRow[]>(`/documents?${params}`), api<Item[]>("/folders"), api<Item[]>("/tags"),
      ]);
      setDocuments(rows); setFolders(allFolders); setTags(allTags); setError("");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : t.connection);
    } finally { setLoading(false); }
  }, [folderFilter, tagFilter, favoritesOnly, query, t.connection]);

  const loadDetail = useCallback(async (id: string, preferred?: string) => {
    const detail = await api<{ versions: Version[] }>(`/documents/${id}`);
    setVersions(detail.versions);
    const next = preferred ?? detail.versions.find(v => v.is_current)?.id ?? null;
    setVersionId(next);
    setPassages(next ? await api<Passage[]>(`/documents/${id}/versions/${next}/passages`) : []);
  }, []);

  useEffect(() => { document.documentElement.lang = language; }, [language]);
  useEffect(() => { const timer = window.setTimeout(() => { void refresh(); }, 0); return () => window.clearTimeout(timer); }, [refresh]);
  useEffect(() => {
    if (!documents.some(d => d.status === "queued" || d.status === "processing")) return;
    const timer = window.setInterval(() => { void refresh(); if (selected) void loadDetail(selected, versionId ?? undefined); }, 2000);
    return () => window.clearInterval(timer);
  }, [documents, refresh, selected, versionId, loadDetail]);

  const current = documents.find(d => d.id === selected);
  const visiblePassage = passages.find(p => p.id === activePassage);

  async function upload(file: File | undefined, forDocument?: string) {
    if (!file) { setError(t.fileRequired); return; }
    setBusy(true); setError("");
    try {
      const body = new FormData(); body.set("file", file);
      const result = await api<{ id: string; version_id: string }>(forDocument ? `/documents/${forDocument}/versions` : "/documents", { method: "POST", body });
      await refresh();
      setSelected(result.id);
      setActivePassage(null);
      await loadDetail(result.id, result.version_id);
    } catch (exc) { setError(exc instanceof Error ? exc.message : t.uploadError); }
    finally { setBusy(false); if (uploadRef.current) uploadRef.current.value = ""; if (versionRef.current) versionRef.current.value = ""; }
  }

  async function mutate(path: string, init: RequestInit, onDone?: () => void) {
    setBusy(true); setError("");
    try {
      await api(path, init); await refresh(); onDone?.();
      if (selected && init.method !== "DELETE") await loadDetail(selected, versionId ?? undefined);
    } catch (exc) { setError(exc instanceof Error ? exc.message : t.saveError); }
    finally { setBusy(false); }
  }

  async function createItem(event: FormEvent<HTMLFormElement>, kind: "folders" | "tags") {
    event.preventDefault();
    const form = event.currentTarget;
    const name = String(new FormData(form).get("name") ?? "").trim();
    if (!name) return;
    await mutate(`/${kind}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name }) }, () => form.reset());
  }

  function setDocument(patch: object) {
    if (!selected) return;
    void mutate(`/documents/${selected}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(patch) });
  }

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
        <p className="sidebar-footer">{t.localNote}</p>
      </aside>
      <main className="content">
        <div className="page-heading"><div><h1>{t.heading}</h1><p>{t.intro}</p></div>
          <label className="primary-button upload-button">{busy ? t.pending : t.upload}<input ref={uploadRef} type="file" accept=".pdf,.docx,.txt,.md" disabled={busy} onChange={e => void upload(e.target.files?.[0])} /></label>
        </div>
        <p className="upload-hint">{t.uploadHint}</p>
        {error && <div className="error-banner" role="alert">{error}</div>}
        <div className="library-layout">
          <section className="library-main" aria-label={t.library}>
            <div className="filters">
              <input aria-label={t.filter} placeholder={t.filter} value={query} onChange={e => setQuery(e.target.value)} />
              <select aria-label={t.folder} value={folderFilter} onChange={e => setFolderFilter(e.target.value)}><option value="">{t.anyFolder}</option>{folders.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select>
              <select aria-label={t.tag} value={tagFilter} onChange={e => setTagFilter(e.target.value)}><option value="">{t.anyTag}</option>{tags.map(tag => <option key={tag.id} value={tag.id}>{tag.name}</option>)}</select>
              <label className="favorite-filter"><input type="checkbox" checked={favoritesOnly} onChange={e => setFavoritesOnly(e.target.checked)} />{t.favorites}</label>
            </div>
            {loading ? <p className="table-empty">{t.loading}</p> : documents.length === 0 ? <div className="empty-library"><h2>{t.empty}</h2><p>{t.emptyBody}</p></div> :
              <div className="document-list">{documents.map(doc => <button className={selected === doc.id ? "document-row selected" : "document-row"} key={doc.id} onClick={() => { setSelected(doc.id); setActivePassage(null); void loadDetail(doc.id).catch(exc => setError(String(exc))); }}>
                <span className="file-glyph" aria-hidden="true">{doc.filename.split(".").pop()?.toUpperCase()}</span>
                <span className="row-main"><strong>{doc.title}</strong><small>{doc.filename} · v{doc.version_number}{doc.tags.length ? ` · ${doc.tags.map(x => x.name).join(", ")}` : ""}</small></span>
                <span className={`status-chip ${doc.status}`}>{t[doc.status]}</span><span className="row-star" aria-hidden="true">{doc.favorite ? "★" : ""}</span>
              </button>)}</div>}
          </section>
          <aside className="organize-panel" aria-label={t.tags}>
            <h2>{t.folder}</h2><form onSubmit={e => void createItem(e, "folders")}><input name="name" maxLength={120} placeholder={t.folderName} aria-label={t.folderName} required /><button disabled={busy} type="submit">{t.add}</button></form>
            <h2>{t.tag}</h2><form onSubmit={e => void createItem(e, "tags")}><input name="name" maxLength={120} placeholder={t.tagName} aria-label={t.tagName} required /><button disabled={busy} type="submit">{t.add}</button></form>
          </aside>
        </div>
        {selected && <section className="detail-panel" aria-label={t.detail}>
          <div className="detail-heading"><h2>{t.detail}</h2><button className="text-button" onClick={() => setSelected(null)}>{t.back}</button></div>
          <div className="detail-grid">
            <div className="detail-controls">
              <form onSubmit={e => { e.preventDefault(); const form = e.currentTarget; const title = String(new FormData(form).get("title") ?? ""); setDocument({ title }); }}><label>{t.title}<input name="title" key={current?.title} defaultValue={current?.title ?? ""} maxLength={240} required /></label><button disabled={busy}>{t.save}</button></form>
              <label>{t.chooseFolder}<select value={current?.folder_id ?? ""} onChange={e => setDocument({ folder_id: e.target.value || null })} disabled={busy}><option value="">{t.noFolder}</option>{folders.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
              <label className="checkbox-line"><input type="checkbox" checked={current?.favorite ?? false} onChange={e => setDocument({ favorite: e.target.checked })} disabled={busy} />{t.favorites}</label>
              {tags.length > 0 && <fieldset><legend>{t.tags}</legend>{tags.map(tag => <label className="checkbox-line" key={tag.id}><input type="checkbox" checked={current?.tags.some(x => x.id === tag.id) ?? false} disabled={busy} onChange={e => { const ids = new Set(current?.tags.map(x => x.id)); if (e.target.checked) ids.add(tag.id); else ids.delete(tag.id); setDocument({ tag_ids: [...ids] }); }} />{tag.name}</label>)}</fieldset>}
              <label className="secondary-button">{t.addVersion}<input ref={versionRef} type="file" accept=".pdf,.docx,.txt,.md" disabled={busy} onChange={e => void upload(e.target.files?.[0], selected)} /></label>
              <button className="danger-button" disabled={busy} onClick={() => { if (window.confirm(t.deleteConfirm)) void mutate(`/documents/${selected}`, { method: "DELETE" }, () => { setSelected(null); setVersions([]); setPassages([]); }); }}>{t.delete}</button>
            </div>
            <div className="source-panel">
              <h3>{t.versions}</h3>
              <div className="version-tabs">{versions.map(v => <button key={v.id} className={versionId === v.id ? "active" : ""} onClick={() => { setVersionId(v.id); setActivePassage(null); void api<Passage[]>(`/documents/${selected}/versions/${v.id}/passages`).then(setPassages).catch(exc => setError(String(exc))); }}>v{v.version_number} · {v.filename}</button>)}</div>
              {versionId && <><div className="source-toolbar"><span className={`status-chip ${versions.find(v => v.id === versionId)?.status ?? "queued"}`}>{t[versions.find(v => v.id === versionId)?.status ?? "queued"]}</span><a href={`/api/library/documents/${selected}/versions/${versionId}/original`} target="_blank" rel="noreferrer">{t.original}</a></div>
                {versions.find(v => v.id === versionId)?.error_message && <p className="error-text">{versions.find(v => v.id === versionId)?.error_message}</p>}
                {versions.find(v => v.id === versionId)?.job_id && versions.find(v => v.id === versionId)?.can_retry &&
                  <button className="retry-button" disabled={busy} onClick={() => { const jobId = versions.find(v => v.id === versionId)?.job_id; if (jobId) void mutate(`/jobs/${jobId}/retry`, { method: "POST" }); }}>{t.retry}</button>}
                <h3>{t.passages}</h3>
                {passages.length === 0 ? <p className="muted">{t.noPassages}</p> : <div className="passage-list">{passages.map(p => <button className={activePassage === p.id ? "passage-row active" : "passage-row"} key={p.id} onClick={() => setActivePassage(p.id)}><span>{locatorLabel(p.locator, t)}</span><p>{p.text_content}</p></button>)}</div>}
                {visiblePassage && <div className="passage-focus"><strong>{t.passage} · {locatorLabel(visiblePassage.locator, t)}</strong><p>{visiblePassage.text_content}</p><a href={`/api/library/documents/${selected}/versions/${versionId}/original${visiblePassage.locator.page ? `#page=${visiblePassage.locator.page}` : ""}`} target="_blank" rel="noreferrer">{t.original}</a></div>}
              </>}
            </div>
          </div>
        </section>}
      </main>
    </div>
  </div>;
}
