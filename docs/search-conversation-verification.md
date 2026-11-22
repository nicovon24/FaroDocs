# Search and conversation verification

Date: 2026-11-21/22 local development session. Scope: local single-owner preview, not a public deployment.

## Implemented behavior

- PostgreSQL lexical passage search over ready current document versions, with ranked excerpts and original-source links.
- Local conversation create, list, reopen, ask, and delete flows. Groq GPT OSS 20B is the default model; GPT OSS 120B is selectable. The user enters a request-only key in the browser.
- The question route sends at most six retrieved passages to Groq, validates numbered source IDs, and abstains when no passage is found or the response lacks valid citations.

## Evidence

- Corpus: one synthetic text document per HTTP search check, plus one synthetic ready passage per database-backed conversation test. The existing local library was not used for answer evaluation.
- `py -3.12 -m unittest backend.tests.test_groq -v`: 1 adapter test passed with a fake network response.
- `docker compose exec -T api python /tmp/test_conversations.py`: 2 database-backed tests passed with a fake provider. Covered history, citations, deletion, abstention, invalid citation, and provider error.
- `py -3.12 -m unittest backend.tests.test_api_library backend.tests.test_api_search -v`: 4 HTTP tests passed against healthy Compose services. Covered upload lifecycle and current/deleted passage visibility.
- `npm run lint`, `npm run typecheck`, `npm run build`: passed in `web/`.
- `openspec validate farodocs-search --strict` and `openspec validate farodocs-conversations --strict`: passed.
- Playwright CLI: Spanish and English interface, local history, no-source abstention, conversation deletion, and 320/390 px layouts checked. At 320 px, all three navigation buttons were visible and document scroll width equaled viewport width (320 px). The no-source browser flow used a synthetic key; it made no Groq request.
- `impeccable detect --json web/src/app/page.tsx web/src/app/styles.css`: no findings.

## Limits

No live Groq request was made because no real user key was supplied. Provider settings were checked against Groq's published API and model documentation, but real availability, latency, cost, and answer quality remain unmeasured. A fake provider proves request and citation handling, not factual support. Lexical retrieval can miss paraphrases. The current fixed owner does not isolate real users. Do not use private documents or expose the preview publicly before identity, permissions, privacy, and security work.
