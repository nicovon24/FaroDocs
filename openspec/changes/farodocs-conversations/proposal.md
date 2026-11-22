# Proposal

## Why

Search finds passages, but the owner cannot ask a follow-up question or return to an answer. A local conversation flow using the user's Groq key makes source-backed questions usable without project-owner credits.

## What Changes

- Add locally persisted conversations and messages for the fixed development owner.
- Answer questions from bounded retrieved passages through Groq, with source links and abstention when evidence is absent or citations are invalid.
- Let the owner provide a Groq key in the current browser session; do not persist or return it.
- Remove conversations referencing a document when that document is deleted.

## Capabilities

### New Capabilities

- `source-conversations`: Local history and source-backed question answering with a user-supplied provider key.

### Modified Capabilities

None.

## Impact

New PostgreSQL tables, FastAPI routes and Groq adapter, Next.js conversation view, deletion lifecycle, synthetic fake-provider checks, and documentation. This local preview excludes Google sign-in, encrypted key persistence, answer PDF export, and quality claims.
