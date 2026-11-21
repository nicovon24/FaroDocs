# Tasks

## 1. Local foundation

- [x] 1.1 Create Next.js/React/TypeScript, FastAPI, PostgreSQL/pgvector, broker, and Python worker Compose skeleton; verify a clean `docker compose up --build` exposes API and UI health checks on localhost.
- [x] 1.2 Define document/version/job/blob/chunk and organization migrations; verify migration from an empty database and the expected constraints.
- [x] 1.3 Document exact local setup, environment variables, and reset commands in README; verify them on a clean local volume.

## 2. Upload and extraction

- [ ] 2.1 Select format parsers after a license and locator spike, record the decision, and verify sample PDF/DOCX/TXT/Markdown blocks retain usable locations.
- [ ] 2.2 Implement bounded upload validation and private original storage; verify supported, oversized, mismatched, and malformed synthetic files through API tests.
- [ ] 2.3 Implement queued extraction with idempotent jobs and visible states; verify successful and failed jobs, including retry behavior, in tests and the UI.
- [ ] 2.4 Persist deterministic passage IDs, extraction recipe, version, and source locators; verify reprocessing stability and passage open behavior with synthetic fixtures.
- [ ] 2.5 Document the fixture generator, parser limits, and upload/processing commands; verify the documented commands run.

## 3. Library workflow

- [ ] 3.1 Implement document list, folders, tags, favorites, filters, and version history; verify an end-to-end local UI flow with generated fixtures.
- [ ] 3.2 Implement passage inspection with page or text-offset fallback; verify a PDF and a text-format citation locator in the browser.
- [ ] 3.3 Implement tombstoned deletion and retryable blob/derived-data cleanup; verify immediate invisibility and eventual local cleanup in tests.
- [ ] 3.4 Document the library API and deletion semantics in README or technical docs; verify examples against the local API.

## 4. Integration review

- [ ] 4.1 Run the affected API tests and local browser user flow, review the diff, and record the exact commands and unresolved limitations before declaring this slice complete.

## Workflow follow-up

- Revisit the proposed product preferences in `docs/decisions.md` before committing to the next stage.
- Archive this change after implementation and verification are accepted.
