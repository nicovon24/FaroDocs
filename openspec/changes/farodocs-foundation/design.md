# Design

## Context

The repository currently contains planning files only. The first slice targets a single local owner; multi-user authorization and public operation are later gates. See `proposal.md` and `specs/document-library/spec.md` for scope and behavior.

## Goals / Non-Goals

**Goals:**
- Establish module boundaries and data records that can support later retrieval and per-document authorization without building those features now.
- Make ingestion and deletion observable and retryable, with source locations retained.
- Run the slice from one documented Compose command and generated fixtures.

**Non-Goals:**
- Production identity, external model calls, search, OCR, cloud storage, or Drive.
- A microservice split or a promise that all PDF layouts produce exact visual coordinates.

## Decisions

1. **Next.js web server plus one modular FastAPI backend and a Python worker.** Next.js renders the UI and may use Server Actions for short form mutations. Uploads and downloads use a streaming-capable route or same-origin proxy. FastAPI owns document records, authorization, library services, and job submission; it is the only business API. Long parsing work runs in a worker via a queue, sharing Python domain code with the API. Alternative: Next.js-only domain logic would move extraction and OCR away from the preferred Python ecosystem; Django would supply more built-in identity/admin features but is not the user's chosen backend. Compose includes PostgreSQL, a broker, FastAPI, worker, and Next.js.
2. **PostgreSQL is the source of truth; private file storage holds originals.** Records include Document, DocumentVersion, Blob, ProcessingJob, Chunk, Folder, Tag, and Favorite. A version is immutable after upload; processing status and derived artifacts are tracked separately. Alternative: filesystem-only metadata, which makes versioning and cleanup harder. pgvector is enabled but embeddings are not created in this slice.
3. **Extract location before chunking.** Format-specific adapters emit ordered blocks with page/paragraph/character metadata. Chunking records a recipe ID and deterministic ordinal or content hash so reprocessing the same bytes and recipe preserves IDs. A changed recipe yields new IDs. Alternative: plain text concatenation, which loses citation provenance.
4. **Use a local owner boundary without presenting it as secure multi-user isolation.** The application is bound to localhost and uses a development owner identity or fixture. All domain records still include an owner/workspace reference to ease the later permissions stage. FastAPI is the final authorization boundary; a Next.js Server Action must also check the session before invoking it. Alternative: implement the full permission model now, which would make this first slice too broad. This build is not suitable for shared use.
5. **Validate and stage uploads before processing.** Check configured byte and page limits, detect content type, use private paths, and expose failure states. Parsing libraries are selected after a small license and locator spike for each format. Alternative: accept by extension alone, which is unreliable. Processing jobs are idempotent and do not overwrite an immutable version.
6. **Deletion uses a tombstone and cleanup job.** Hide the document immediately, remove derived rows and blobs, and show cleanup completion or failure in an operations record. The later privacy stage will define backup and external provider retention. Alternative: immediate best-effort deletion in the HTTP request, which can leave partial data without visibility.

## Risks / Trade-offs

- PDF reading order or layout may be wrong -> retain original page reference, expose text fallback, and test a multi-column fixture before claiming precise highlights.
- Worker crash can leave processing pending -> persist job state and retry safely.
- File validation may misclassify content -> test extension/content mismatch and corrupted fixtures.
- Local development identity can be mistaken for real access control -> mark the UI and README as local-only until the permissions stage passes.
- Blob cleanup can fail after database deletion -> keep tombstone and retryable cleanup event.

## Migration Plan

This is a greenfield local repository. Build migrations from empty PostgreSQL, seed only synthetic data, and verify a clean Compose reset. No production rollback applies. Keep migration and fixture commands documented in the README once implementation exists.
