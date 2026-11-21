# Decision record

Only the user can confirm product preferences. A proposal is not a confirmed decision. Record the date, owner, alternatives, rationale, and consequences when a choice is confirmed.

## Confirmed by the user (2026-11-21)

- Build an original, independent portfolio repository; do not copy another document management project.
- The initial preference was Django, React with TypeScript, PostgreSQL with pgvector, and Docker Compose. The application framework choice below supersedes Django before implementation.
- Start the interface in Spanish and offer English; write code and technical documentation in English.
- Work in reviewable vertical stages, with synthetic data, affected-behavior checks, execution instructions, and diff review.
- Keep the product private until permissions, deletion, upload limits, privacy, and adversarial documents have been verified.
- Do not create a remote repository, push, or deploy without a later request.
- Use Blandskron/AgenteIADocumental as a comparison reference for product behavior, engineering practices, CI/CD, and skills. Keep FaroDocs original: do not transfer its code, prompts, documentation, assets, interface, or file layout.
- Use the frontend workflow previously used in the AI Engineering projects: Impeccable for product UI design/review, Playwright CLI for browser checks, and Web Interface Guidelines when an interface audit calls for them. Define FaroDocs' own visual system.
- Request `gpt-6-astra` with high reasoning effort for substantial planning and orchestration when the runtime permits model selection. Record requested and runtime-confirmed model/effort separately; do not claim a model was used without confirmation.
- Use Next.js with React and TypeScript for the web application, FastAPI for the Python backend, a separate Python worker for document jobs, PostgreSQL with pgvector, and Docker Compose for local execution. Server Actions may handle short UI mutations; FastAPI remains the source of truth for authorization and document operations.
- Use Google sign-in for user accounts. Persist each user's chat history and selected AI provider/model. Persist a user-supplied provider API key securely so it remains available across sessions; the application must not require the project owner's OpenAI credits. Google sign-in and optional Google Drive import are separate consent flows.
- Publish source increments to the existing public `nicovon24/FaroDocs` GitHub repository. This supersedes the earlier no-remote/no-push instruction for source control; it does not authorize deployment or a claim of public product readiness.
- Start with a single-user local preview for upload and library work. Add Google sign-in and account-bound history/provider credentials in the identity stage before shared use. The local owner fixture does not establish user isolation or production permissions.

## Proposed defaults requiring user preference

| ID | Proposal | Why | Alternative |
| --- | --- | --- | --- |
| P1 | First *shared portfolio demo* after library, hybrid search, source-backed chat, and document-level access control; earlier slices remain local development previews | A multi-user demo must not expose private document content | Keep previews local until identity and permissions pass |
| P2 | Prioritize claim-to-source verification, a versioned evaluation panel, then adversarial-document tests | These make answer trustworthiness and engineering tradeoffs explainable in interviews | Prioritize version comparison or structured extraction for a domain-specific story |
| P3 | Start with local uploads and an explicit user-triggered Drive import later | Keeps ingestion and permissions understandable before OAuth | Include manual Drive import in the first demo |
| P4 | Start with local multilingual embeddings and a curated set of user-key generation providers behind one application interface | Avoids project-owner API credits and keeps retrieval reproducible; exact providers and models remain to be selected | User-selected embedding providers or an optional local generation model |
| P5 | Use one modular FastAPI backend, a Python worker, PostgreSQL, and a queue broker in Compose | Separates long document processing from request latency without splitting business logic into services | Start with synchronous jobs for tiny files, then add a worker |

## Pending experiment decisions

- Choose exact embedding and generation models and initial supported providers only after recording language coverage, data handling terms, price, and a small retrieval baseline. Do not claim support for every provider with a token.
- Choose the exact secret-store mechanism for local development and any later hosting environment; keep its encryption key separate from PostgreSQL and document rotation, backup, and deletion behavior before saving real user credentials.
- Choose an OCR library and test scanned PDFs in the later OCR stage. The first text-bearing parser choice and its measured locator limits are recorded in `docs/extraction-spike.md`.
- Set actual file-size, page-count, and request-rate limits from local resource tests rather than promising arbitrary numbers.
