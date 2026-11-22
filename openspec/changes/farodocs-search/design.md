# Design

## Context

Passages already have stable IDs and locators. PostgreSQL is the source of truth; the UI currently proxies library requests through Next.js. See the proposal for motivation.

## Goals / Non-Goals

**Goals:** Deterministic lexical ranking, bounded API output, visible provenance, and a useful bilingual search surface.

**Non-Goals:** Semantic similarity, vector embeddings, cross-user authorization, OCR text, or measured retrieval-quality claims.

## Decisions

- Use PostgreSQL full-text search with the `simple` dictionary on passage text. It is language neutral for Spanish/English tokens and avoids a model download. Rank with `ts_rank_cd`, then stable ID order. An alternative single-language stemming configuration would disadvantage the other UI language.
- Index passage text with a GIN expression index. Join `chunks` to current ready `document_versions` and nondeleted workspace `documents` in every query. A materialized search table would add synchronization risk.
- Return original links through the existing same-origin library proxy. PDF page anchors use the stored locator; text formats show the extracted passage and offset/block label.

## Risks / Trade-offs

- Lexical ranking misses synonyms and some inflections → document the limitation and measure retrieval before adding vector search.
- The preview uses a fixed local owner → keep localhost binding and require the later identity/permissions slice for shared use.
