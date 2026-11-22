# Design

## Context

The current preview has a fixed local owner, passage search, and a same-origin web proxy. Account sessions and encrypted credential storage are reserved for the identity stage.

## Goals / Non-Goals

**Goals:** Durable local history, bounded context, Groq answer requests with a user key, source navigation, and safe failure behavior.

**Non-Goals:** Multi-user isolation, persisted secrets, streaming, PDF export, semantic retrieval, or claim-support evaluation.

## Decisions

- Store conversations, messages, and citation-to-chunk references in PostgreSQL. Every route scopes by the fixed owner/workspace; later identity work must replace this fixture.
- Keep the Groq key only in React memory and POST it with each question. The backend never logs, saves, echoes, or interpolates it into errors. No browser storage is used. This requires re-entry after reload, a deliberate local-preview limit.
- Call a fixed Groq HTTPS endpoint with an allowlisted model (`openai/gpt-oss-20b` default, `openai/gpt-oss-120b` optional). The model sees at most six current passages, each truncated to 1200 characters, and recent conversation turns. The provider response cites numbered context passages; the server validates those numbers before persistence.
- Treat document text as quoted data in the prompt. Unknown or missing citations become an abstention. This validates citation identity, not factual support.
- Delete a conversation immediately if its citations reference a document entering deletion, before passage cleanup removes the rows.

## Risks / Trade-offs

- Lexical retrieval can miss relevant evidence → expose the limitation and evaluate before claiming answer quality.
- A valid source ID can still support an incorrect claim → add separate claim-support evaluation later.
- Passages leave the local machine for Groq → show an explicit notice before sending.
- Fixed-owner API is not safe for shared use → retain localhost-only Compose bindings until identity and permissions pass.
