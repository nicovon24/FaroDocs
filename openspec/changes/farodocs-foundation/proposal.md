# Proposal

## Why

FaroDocs needs a reproducible first vertical slice that proves uploaded documents can be processed, organized, and inspected before search or RAG is added. The project is new; a narrow foundation makes the later retrieval and citation stages reviewable.

## What Changes

- Create a local Docker Compose application skeleton with Next.js/React/TypeScript, FastAPI, PostgreSQL with pgvector enabled, and a Python background worker/broker.
- Add private upload and library flows for text-bearing PDF, DOCX, TXT, and Markdown documents, including visible processing state and errors.
- Preserve original files and extracted passages with version and location metadata suitable for later citations.
- Add folders, tags, favorites, and basic document versions within the local owner scope.
- Supply generated synthetic fixtures, affected-behavior tests, local run instructions, and a reviewed diff.
- Keep external model calls, search, chat, OCR, Drive, multi-user access, evaluation scores, and public deployment outside this first change. The broader plan is in `docs/product-plan.md`.

## Capabilities

### New Capabilities

- `document-library`: Local owner upload, processing visibility, organization, versions, and inspectable extracted passages.

### Modified Capabilities

None.

## Impact

New local backend, frontend, Compose configuration, database migrations, private storage, generated fixtures, tests, and execution documentation. Source increments are pushed to the existing public GitHub repository; no hosted product infrastructure is created. Subsequent stages will add search, chat, permissions, OCR, integrations, and evaluation through separate changes.
