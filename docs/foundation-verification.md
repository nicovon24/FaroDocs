# Foundation and local library verification

Date: 2026-11-21. Scope: `farodocs-foundation` OpenSpec change, local development owner only. The corpus is generated synthetic content: four format fixtures, one textless PDF, and short deletion/retry text files. No model or provider was configured or called. These checks are functional evidence, not retrieval, answer-quality, OCR, or security evaluation.

## Commands and observed results

| Check | Command or action | Result |
| --- | --- | --- |
| Compose build and readiness | `docker compose up --build -d --wait` | Five services started; API, web, database, and broker healthy; worker running. |
| Health | `Invoke-RestMethod http://127.0.0.1:8000/health` and `Invoke-RestMethod http://127.0.0.1:3000/api/health` | Both returned `status: ok`. |
| Parser and upload validation | `$env:PYTHONPATH='backend;backend/tests'; py -3.12 -m unittest backend.tests.test_extraction backend.tests.test_uploads -v` | 3 tests passed, including four formats, locator checks, mismatched files, malformed files, 10 MiB admission, and expanded DOCX limit. |
| HTTP lifecycle | `$env:FARODOCS_TEST_API_URL='http://127.0.0.1:8000'; py -3.12 -m unittest backend.tests.test_api_library -v` | 3 tests passed: four uploads, invalid uploads, failed extraction and retry, immediate deletion invisibility, and cleanup job completion. |
| PostgreSQL lifecycle | `docker cp backend/tests/test_processing.py farodocs-api-1:/tmp/test_processing.py`; `docker compose exec -T api python /tmp/test_processing.py` | 2 tests passed: transient extraction failure followed by success and stable passage IDs/locators; simulated storage failure followed by successful cleanup and removed blob/chunk rows. |
| Web static checks | `npm run lint`, `npm run typecheck`, and Compose's `npm run build` in the web image | Passed. |
| Configuration and spec | `docker compose config --quiet`; `openspec validate farodocs-foundation --strict`; `git diff --check` | Passed. |

## Browser flow

Playwright CLI exercised the built web app at `http://127.0.0.1:3000`:

- Spanish upload of a two-page synthetic PDF reached `ready`; selecting its second passage kept the selection during polling and linked to the same original version with `#page=2`.
- A TXT passage showed a character range and its extracted text. A textless PDF showed a failure reason and a retry control. An old synthetic job that had remained queued with zero attempts offered retry and then reached `ready` with a passage.
- A folder, tag, favorite, and name filter narrowed the list to the intended document. Uploading a Markdown replacement showed version 2 while version 1 remained accessible.
- English copy switched the document language to `en`. At 390 px and 320 px, `document.documentElement.scrollWidth` equaled the viewport width. Screenshots were inspected for the populated list and detail view. Keyboard Tab reached the file input with `:focus-visible` and a 3 px outline on its label.
- Calculated contrast ratios from the current tokens: main ink on paper 13.73:1, muted text on paper 5.69:1, accent on paper 5.49:1; ready, failed, and processing chip text exceed 6.9:1 on their chip surfaces.

## Limits and follow-up

- This is a localhost, single-owner preview without sign-in, multi-user authorization, search, chat, external providers, or OCR. It is not ready for public use.
- PDF citations open the original page and extracted text; no pixel-accurate highlight is available. DOCX has structural block locations, not rendered page numbers. Complex PDF reading order, nested DOCX content, and scanned pages are outside the verified parser coverage.
- Multipart parsing can spool an incoming request before the 10 MiB file admission check. The current limits and local-only binding are not a public upload security assessment.
- Failed and stale queued jobs can be retried through the API and visible extraction control. A worker process terminated while a job is already `processing` can leave that job in `processing`; recovery of such jobs needs a lease or watchdog before public operation.
- Deletion removes local originals and derived rows after the tombstone, but does not erase database backups. The cleanup job status remains queryable through `GET /jobs/{job_id}`.
- CI now includes web checks, parser fixtures, PostgreSQL processing tests, Compose syntax, and the synthetic full-stack HTTP flow. CI results for the new workflow are pending the first push.

## OpenSpec verification

| Dimension | Result |
| --- | --- |
| Completeness | 13/13 tasks; all six added requirements mapped to the implementation. |
| Correctness | 6/6 requirements and 9/9 scenarios checked against the API, worker, UI, tests, and browser flow above. |
| Coherence | The modular API, private original storage, deterministic passages, and tombstoned cleanup follow the design. No critical, warning, or pattern findings in this local slice. |

The worker-crash recovery limit above is a known design risk for later public operation. This verification does not evaluate public security, retrieval quality, or external providers.
