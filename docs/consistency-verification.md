# Local consistency fix verification

Date: 2026-11-22. Scope: the local single-owner preview. No live Groq request was made.

## Synthetic evidence

- Version test: one synthetic document with an existing ready version and three replacement versions. A failed replacement kept the prior version current; a newer successful replacement became current; an older worker finishing later did not downgrade it. Search and the library list showed the current version at each step.
- Deletion test: one synthetic cited document, a fake Groq answer, and two concurrent operations. Deletion waited while the answer held its source lock, then removed the cited conversation; the cleanup job finished `ready` and removed its passages.
- Browser tests: two synthetic unanswered conversations and one new empty conversation. A delayed detail response for the first thread did not replace the selected second thread. The new thread displayed its empty state, and reselecting the active conversation retained its messages. A mocked ready document with a queued replacement remained at version 1 in the library and changed to version 2 after polling. Synthetic conversations were deleted after the check.
- The browser checked Spanish and English copy, keyboard focus, and 320/390 px layouts without horizontal overflow. Existing local documents were not used as test inputs.

## Commands and limits

- `docker compose up --build -d --wait`
- `docker compose exec -T api python /tmp/test_version_availability.py`: 1 test passed.
- `docker compose exec -T api python /tmp/test_conversations.py`: 3 tests passed.
- `py -3.12 -m unittest backend.tests.test_api_library backend.tests.test_api_search -v` with the test API URL: 4 tests passed.
- `npm run lint` and `npm run typecheck` passed in `web/`; the Docker web build passed.
- Playwright CLI used mocked responses for the delayed-detail and library-poll checks. These checks prove UI state handling, not provider quality or production load behavior.

The preview still lacks account isolation, rate controls, semantic retrieval, and claim-support evaluation. These checks do not establish public readiness.
