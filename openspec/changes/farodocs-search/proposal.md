# Proposal

## Why

The local library exposes extracted passages only after opening a document. The owner needs to find relevant passages across the collection before using them in conversations.

## What Changes

- Add passage search across ready, current versions of visible local documents.
- Show ranked passages, document and source location, and a link to the original version.
- Keep empty queries, no results, and processing/deleted documents predictable.

## Capabilities

### New Capabilities

- `passage-search`: Query and inspect ranked passages in the local owner's library.

### Modified Capabilities

None.

## Impact

PostgreSQL index, FastAPI search route, Next.js search surface, synthetic API/browser checks, and local documentation. This slice uses lexical retrieval; semantic/vector ranking remains a measured follow-up rather than a quality claim.
