# FaroDocs (working title)

FaroDocs is an original document intelligence portfolio project in early implementation. The intended product is a local-first web application for organizing documents, searching their contents, and asking questions with inspectable source passages. The name needs trademark and domain checks before product publication.

The selected architecture is Next.js (React/TypeScript), FastAPI and a Python document worker, PostgreSQL/pgvector, and Docker Compose. See the [system designs](system-design/README.md) for planned flows.

The first library preview targets one local development owner. Google sign-in, account-scoped chat history, and saved user-selected AI provider credentials are planned in the [identity and provider credential design](docs/identity-and-provider-keys.md). They are not implemented yet; the local preview does not provide multi-user isolation.

## Current status

| Area | Status |
| --- | --- |
| Product and architecture plan | Proposed; decisions recorded in `docs/decisions.md` |
| Application code | Local upload and library preview for text-bearing PDF, DOCX, TXT, and Markdown; queued extraction, source passages, organization, versions, and deletion cleanup |
| Compose runtime | Five services started locally; API and web health endpoints and synthetic upload flow verified on localhost |
| Evaluation results | None |
| Public deployment | None |

Read the [product plan](docs/product-plan.md), [decision record](docs/decisions.md), [reference and CI analysis](docs/reference-and-delivery.md), [first vertical slice proposal](openspec/changes/farodocs-foundation/proposal.md), and [local verification record](docs/foundation-verification.md).

## Running locally

The library preview has no authentication, search, or chat. Install Docker Desktop with Compose and start its Linux engine. From the repository root, use:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:3000/api/health
```

The library preview is at <http://127.0.0.1:3000>. It starts in Spanish and offers English. Stop containers with `docker compose down`; this retains the local database, broker, and original-file volumes. Use `docker compose down --volumes` only when intentionally discarding all local data. The services use `restart: unless-stopped` so they return when Docker Desktop restarts, provided they were not explicitly stopped with Compose. The current Compose password default is for local development only. On 2026-11-21, `docker compose up --build -d` succeeded from new volumes and both health endpoints returned `ok`.

If Docker Desktop reports a healthy web container but its published port closes connections, run the built Next.js preview directly from `web/`:

```powershell
npm ci
npm run build
node node_modules/next/dist/bin/next start --hostname 127.0.0.1 --port 3011
```

Open <http://127.0.0.1:3011>. This direct preview served the original empty-library page and health route on 2026-11-21 after Docker Desktop's port 3000 stopped returning responses. Stop the direct server with Ctrl+C. For the current document operations, run the full Compose stack and set `FARODOCS_API_URL=http://127.0.0.1:8000` when starting the web server directly.

Compose uses these settings:

| Setting | Source | Current use |
| --- | --- | --- |
| `POSTGRES_PASSWORD` | Optional host environment variable; default `local-development-only` | Password for the local database. Set before creating the volume if you want a different password. |
| `DATABASE_URL` | Built by Compose for API and worker | Internal PostgreSQL connection; do not set it on the host for the Compose path. |
| `CELERY_BROKER_URL` | Built by Compose for API and worker | Internal Redis connection. |
| `FARODOCS_API_URL` | Built by Compose for web | Internal API address. |
| `FARODOCS_STORAGE_ROOT` | Built by Compose for API and worker | Private, shared volume for original files. |

To restart while retaining data, use `docker compose down` followed by `docker compose up --build -d`. To reset this project's local database and broker completely, use `docker compose down --volumes`, then `docker compose up --build -d`. The reset destroys all FaroDocs data in those volumes. Re-run the two health commands above after either path. Do not use a real provider key or private document in this unfinished local preview.

Web checks run from `web/` with `npm ci`, `npm run lint`, `npm run typecheck`, and `npm run build`. For Python 3.12+, install the backend and fixture generator dependency with `py -3.12 -m pip install -e backend reportlab==4.4.4`. The local library uses a 10 MiB file limit and a 100-page PDF limit. It rejects unsupported, mismatched, oversized, or malformed files with a reason. Image-only PDFs fail extraction with an OCR limitation message. See [library API and lifecycle](docs/library-api.md) and the [parser spike](docs/extraction-spike.md).

Generate synthetic samples and run the checks from the repository root:

```powershell
$env:PYTHONPATH='backend;backend/tests'
py -3.12 -c "from pathlib import Path; from generate_extraction_fixtures import generate; generate(Path('media/fixtures'))"
py -3.12 -m unittest backend.tests.test_extraction backend.tests.test_uploads -v
$env:FARODOCS_TEST_API_URL='http://127.0.0.1:8000'
py -3.12 -m unittest backend.tests.test_api_library -v
```

`media/` is ignored by Git. The HTTP test uploads only generated files, waits for processing, exercises a failed extraction and retry, and requests deletion afterward. The database-backed retry and stable-passage check runs in CI after migration. The same check can be run locally inside the API container by copying `backend/tests/test_processing.py` to `/tmp/test_processing.py` and executing `docker compose exec -T api python /tmp/test_processing.py`.

The API applies versioned SQL migrations before starting. They are stored in `backend/farodocs/sql/`; applied filenames are tracked in `schema_migrations`. To rerun pending migrations, use `docker compose exec -T api python -m farodocs.migrate`. The database URL comes from `DATABASE_URL` in Compose. The migration is idempotent; the schema constraint check can be run with `Get-Content -Raw backend/tests/schema_constraints.sql | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U farodocs -d farodocs`.

The [CI workflow](.github/workflows/validate.yaml) checks the web build, Python imports and parser fixtures, database migration and constraints, database-backed passage stability, Compose syntax, and a full Compose synthetic HTTP document flow on pushes and pull requests.

## Working agreements

- Technical documentation and code are written in English. The initial UI language will be Spanish, with English available.
- Record product decisions in `docs/decisions.md` and measured experiments with corpus details and limits when they occur.
- Keep implemented behavior, verified behavior, and future plans distinct.
- The repository is linked to `https://github.com/nicovon24/FaroDocs`; publication of source does not imply readiness for public product use. No deployment is planned yet.
