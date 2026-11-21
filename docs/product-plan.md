# FaroDocs product and architecture plan

Status: proposal, 2026-11-21. No application behavior or evaluation result is claimed here.

## Product

FaroDocs helps a person keep a private document collection, find passages, and ask questions while checking every cited source in its original context. The portfolio value is an inspectable RAG system with measured retrieval, groundedness, abstention, cost, and failure modes. Primary persona: an individual researcher or analyst. Secondary persona: a small workspace where members have different document access.

The first reviewable slice is upload and library management. The recommended first portfolio demo includes the first four stages below and remains local until its access-control and deletion checks pass. Scanned PDFs, Drive, and the evaluation UI can follow without preventing an honest text-PDF demo.

## Observable requirements and acceptance evidence

| Area | Target observable behavior | Planned evidence |
| --- | --- | --- |
| Identity | A user signs in with Google and accesses only workspaces they belong to | Mocked Google OIDC flow and two-user API/UI access tests |
| Ingestion | PDF, DOCX, TXT, and Markdown uploads show queued, processing, ready, or failed status and a useful error; scanned PDFs enter an OCR path | Synthetic documents, corrupt file, and scanned PDF fixtures |
| Library | Users organize documents with folders, tags, favorites, filters, and immutable versions | Browser flow and API tests |
| Provenance | Each extracted chunk has a stable ID within a document version and a page or text offset; a source link opens the referenced region | Click-through test against fixtures |
| Retrieval | Authorized documents are searched with PostgreSQL full-text and pgvector similarity, with inspectable ranked passages | Labeled query set and retrieval metrics |
| Chat | Spanish and English questions produce answers with passage citations; unsupported questions abstain | Bilingual, answerable, and unanswerable cases |
| Security | Document text is treated as data, not higher-priority instructions; all retrieval and source APIs enforce document access | Cross-user and prompt-injection tests |
| History/export | A signed-in user can reopen their own conversations after logout/login and export an answer plus citations to PDF | Two-user isolation, session restart, UI, and PDF inspection |
| AI connection | A signed-in user selects a supported provider/model, saves a provider API key, and can replace or remove it without the secret being exposed again | Redacted API responses/logs, persistence, rotation/removal, and cross-user tests |
| Drive | With scoped OAuth consent, a user selects files for manual import | Mocked integration plus user-run OAuth check |
| Lifecycle | Upload quotas reject excess work; deletion removes original files, versions, chunks, vectors, conversation source links, and derivatives according to a documented policy | Deletion and quota tests, audit event checks |

Requirements describe the target product. Each stage below states when they become implementation commitments.

## Architecture proposal

```text
Next.js (React/TypeScript) UI and server
       |
       v
FastAPI ---- PostgreSQL (metadata, full text, pgvector)
       |       |
       |       +---- private file storage (originals, optional page previews)
       v
queued jobs ---- worker (extract, OCR, chunk, embed, delete)
       |
       +---- model adapters (embeddings and chat, provider undecided)
```

This is a modular Python backend with a separate web server. Next.js owns rendering, translation, and short UI mutations through Server Actions. Server Components read through the backend; a thin Route Handler or same-origin reverse proxy handles upload/download and streaming where appropriate. Next.js does not own document records or make authorization decisions on behalf of FastAPI. Every Server Action that changes state checks the session before calling FastAPI, and FastAPI rechecks authorization. FastAPI owns identity, authorization, workspace membership, document lifecycle, retrieval, chat, and audit events. The worker runs the same Python domain code for slow or retryable processing. It is a process separation, not a set of business microservices: API and worker share one codebase and database, with the operational cost of a broker and worker. Proposed backend modules: `accounts`, `workspaces`, `documents`, `ingestion`, `retrieval`, `conversations`, `integrations`, and `evaluation`. Dependency direction: API handlers call application services; services use repository, parser, and model interfaces. Retrieval and chat receive an authorized document scope, never raw unscoped querysets.

Proposed core records: User with Google subject ID; Session; Workspace and Membership; Document with workspace/owner; DocumentGrant; immutable DocumentVersion; Blob; ProcessingJob; Chunk with version, deterministic index, text hash, page/offset/locator; Embedding with model ID and dimension; Folder, Tag, Favorite; Conversation, Message, Citation; user-owned ProviderConnection with encrypted secret reference; AuditEvent; EvaluationDataset and Case. Exact schema and constraints are stage-specific decisions. A chunk ID is stable for reprocessing the same version and extraction/chunking recipe; a new document version or recipe gets new IDs. Preserve extraction recipe and model IDs for reproducibility.

### Ingestion and citations

Validate file type from content as well as extension, cap upload size and page count, store originals privately, and make jobs idempotent. Extract text with document location metadata before chunking. For PDF, store page and preferably bounding boxes; for DOCX/TXT/Markdown, preserve paragraph or character offsets. Render a source preview that points to the exact passage, and show a plain-text fallback when rendering precision is unavailable. OCR must record language and confidence/quality signals and expose uncertain text to the user. Never present a citation as an exact visual location if extraction cannot support it.

### Search and answer path

Filter by authorized document/version IDs before both lexical and vector retrieval. Start with Postgres full-text search plus pgvector exact cosine search on a small corpus; fuse ranked candidates with a documented method such as reciprocal rank fusion. Evaluate before adding approximate indexes, since they can change recall. Return passage IDs, rank signals, version, and locator. The chat service retrieves passages, constructs a bounded context, requests an answer in the question's language, verifies citation IDs against the retrieved set, and abstains when evidence is insufficient. A citation-validity check is not the same as claim support; claim verification is a separate planned differentiator. Treat all extracted document content as untrusted input and test malicious passages.

### Authorization and lifecycle

Use workspace membership plus explicit document grants (viewer/editor/owner proposal). Apply access filtering in list, retrieval, history, previews, exports, and background jobs, and recheck when serving a citation. Deny access by default. Deletion must account for database rows, private blobs, queued jobs, cached previews, embeddings, and exported files; document the behavior for backups separately. Audit events should avoid storing document contents. Provider calls may send passages externally, so make data handling and consent visible before enabling them.

### Google identity, conversations, and provider credentials

Use Google OpenID Connect authorization code sign-in with only `openid email profile` scopes. Validate the callback state and ID token, then link the Google `sub` claim to a FaroDocs User; email is display/contact data, not the stable identity key. FastAPI issues an opaque application session in a server-side store and an HttpOnly, SameSite cookie through a same-origin entry point. Next.js reads the session for rendering; FastAPI rechecks it and every document grant on API calls. Google Drive import requests separate, incremental consent later. See [identity and provider credential design](identity-and-provider-keys.md).

Conversations and messages are stored in PostgreSQL under the FaroDocs user/workspace; source references include document version and passage IDs. History queries and exports apply current document access, so a revoked document cannot be reopened through an old citation. A user can delete conversations. The selected provider/model and a masked key status are also account settings. The credential is accepted server-side, encrypted at rest with a key kept outside PostgreSQL, never returned to the browser, and replaceable or removable. No provider call occurs without a configured connection and a clear warning that authorized passages leave FaroDocs. The initial provider list is curated and capability-checked, not arbitrary API endpoints.

## Technology choices to validate during implementation

| Need | Proposal | Reason / limit |
| --- | --- | --- |
| Web API and identity | FastAPI, Google OIDC, server-side application sessions, and explicit authorization services | Typed API contracts and a Python pipeline; Google identifies users while FastAPI owns sessions and document permissions. |
| Client | Next.js App Router + React + TypeScript | Spanish-first rendering and typed API boundaries. Use Server Actions for short mutations; use a streaming-capable route for large uploads and chat streams. |
| Search | PostgreSQL full-text + pgvector | One transactional store for metadata and both retrieval modes; benchmark exact search before HNSW. |
| Background work | Celery with a broker, likely Redis | Retryable extraction/OCR/embedding jobs; adds one service to local Compose. |
| Extraction | Format-specific adapters; PDF library and OCR engine selected after license/location spike | PDF reading order and OCR quality can make citations misleading. |
| Models | Local multilingual embeddings proposed; user-key generation through curated provider adapters | Record provider, model, version, dimension, latency, token usage, and data policy per experiment. No project-owner OpenAI credit dependency. |

Reference documentation: [Next.js Server Actions](https://nextjs.org/docs/app/getting-started/mutating-data), [Next.js backend-for-frontend guide](https://nextjs.org/docs/app/guides/backend-for-frontend), [FastAPI background task limits](https://fastapi.tiangolo.com/tutorial/background-tasks/), [PostgreSQL full-text search](https://www.postgresql.org/docs/current/textsearch.html), [pgvector](https://github.com/pgvector/pgvector), [Drive download/export](https://developers.google.com/workspace/drive/api/guides/manage-downloads).

## Vertical stages

| Stage | Reviewable result | Synthetic evidence and checks |
| --- | --- | --- |
| 0. Foundation | Compose skeleton, schema, API/UI health checks, executable README, decision log | Deterministic setup and smoke check |
| 1. Upload and library | Four text-bearing formats, processing states, folder/tag/favorite basics, versions, passage preview | Generated tiny files; upload, malformed file, lifecycle UI/API tests |
| 2. Search | Full-text and vector retrieval with authorized-scope contract, visible passage results | Small bilingual corpus with labeled queries, retrieval and latency baseline |
| 3. Chat with sources | Bilingual answers, source click-through, abstention, local history/export, and user-key provider contract | Answerable/unanswerable questions; citation and PDF checks with a fake provider |
| 4. Identity and permissions | Google sign-in, persistent account-scoped history and encrypted provider connection, workspaces, document grants, cross-user isolation throughout API and worker | Mocked OIDC plus opt-in live check; two users and overlapping names; credential persistence, deletion, denial, and leak tests |
| 5. OCR | Scanned PDF routing and quality/error display | Synthetic scanned pages with known text and layout |
| 6. Integrations | Optional manual Drive OAuth import | Mocked imports plus opt-in live check, token revocation |
| 7. Evaluation | Versioned cases, retrieval/support/abstention/latency/cost reporting, adversarial cases | Published corpus manifest and actual measured results only |
| 8. Demo preparation | Reproducible seeded tour, architecture narrative, limits and privacy checklist | Clean install and full user flow |

The user chose a single-user local preview first. Stages 1-3 use a development owner fixture; any local history or provider setting in those stages is only a development preview. Stage 4 links history and provider settings to Google-backed FaroDocs accounts and verifies cross-user isolation before a shared demo. Each stage ends with affected-behavior tests, execution commands, diff review, and a status update. Cross-user authorization and credential storage are hard gates before multi-user use.

## Three differentiators to prioritize

1. **Claim-to-source verification** after basic citations. It confronts the central RAG failure mode: a valid citation may not support the sentence. Show unsupported claims and allow abstention or revision; measure false support before claiming reliability.
2. **Versioned evaluation panel**. Store queries, expected passages, answerability labels, corpus version, model/prompt settings, and run outputs. Report retrieval, support, abstention, latency, and cost separately, with sample counts and confidence limits. This gives an interview-ready account of tradeoffs.
3. **Adversarial-document tests**. Add synthetic documents containing instruction attempts, secret requests, and citation manipulation. These directly exercise the trust boundary and make security claims testable.

Version comparison and structured extraction are valuable but require additional domain fixtures and review UX. Drive incremental sync adds complex token, change tracking, and deletion semantics before the core answer quality is known.

## Evaluation and risks

Begin with a small synthetic/public corpus manifest (target proposal: 8-15 documents in both languages, at least 20 labeled queries, including unanswerable and adversarial cases). This is a target, not an existing dataset or result. Split metrics: retrieval recall@k and MRR; citation validity and human-labeled claim support; abstention precision/recall; p50/p95 latency; token/provider cost. Record corpus size, source licenses, annotation method, and known limits. Avoid a single aggregate quality score.

Main risks: misleading PDF reading order or coordinates; OCR errors; stale embeddings after version changes; cross-workspace leaks through search or citation routes; prompt injection; deletion gaps across derivatives and provider logs; model cost/latency; OAuth scope and token handling. Gate public-readiness claims on security and deletion tests plus provider data review. Trademark and domain availability require a separate check before publication; no name-availability claim is made.

## Current evidence

- Implemented: OpenSpec planning structure, technical documents, a Compose/API/web/worker skeleton with health endpoints, a bilingual empty library preview, and the initial library schema. No document behavior exists yet.
- Evaluated: Compose syntax, a clean five-service Compose startup, local API/web health endpoints, web build/lint/typecheck, Python package imports, a clean database migration, migration idempotency, selected schema constraints, and the empty preview at desktop and mobile widths with its language switch. No corpus, document user flow, retrieval, security, or model evaluation has run.
- Planned: every product capability and all numerical evaluation targets above.
