# FaroDocs product context

Status: local single-owner library, search, and conversation preview. This file summarizes the current product direction; broader requirements and unbuilt stages live in `docs/product-plan.md`.

## User and job

The primary user is an individual researcher or analyst who keeps a document collection and needs to return from a passage or answer to its original source. The local job is to upload, organize, search, ask questions about, and inspect text-bearing files.

## Current experience

- Spanish is the default UI language; English is available from the header.
- A local owner uploads PDF, DOCX, TXT, or Markdown and sees queued, processing, ready, or failed status.
- The owner organizes documents with folders, tags, favorites, and filters, uploads a replacement version, and inspects extracted passages with their available source location.
- Deletion hides a document immediately and starts a cleanup job. This preview is limited to localhost and contains no login or multi-user protection.
- Search finds lexical passage matches in current ready versions. Conversations persist for the fixed local owner and can ask Groq with a key supplied for the current browser session; retrieved passages are sent to Groq.

## Product promise and evidence boundary

The intended product makes source passages inspectable. This preview proves document organization, basic source navigation, lexical search, and fake-provider conversation behavior with synthetic files. It does not claim retrieval quality, grounded answers, OCR accuracy, privacy for shared users, or readiness for public use. Identity and encrypted provider credential storage remain later stages.

## Working assumptions

- The first reviewer runs Docker Compose locally and uses synthetic documents.
- Original page display is useful for PDF even without a precise highlight; TXT and Markdown use character offsets, and DOCX uses structural blocks.
- A quiet, task-focused interface is appropriate for reading and organizing documents. These are design assumptions for the current preview, not user-confirmed product preferences.
