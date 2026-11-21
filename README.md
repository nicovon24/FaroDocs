# FaroDocs (working title)

FaroDocs is an original document intelligence portfolio project in early implementation. The intended product is a local-first web application for organizing documents, searching their contents, and asking questions with inspectable source passages. The name needs trademark and domain checks before product publication.

The selected architecture is Next.js (React/TypeScript), FastAPI and a Python document worker, PostgreSQL/pgvector, and Docker Compose. See the [system designs](system-design/README.md) for planned flows.

Google sign-in, account-scoped chat history, and saved user-selected AI provider credentials are planned in the [identity and provider credential design](docs/identity-and-provider-keys.md). They are not implemented yet.

## Current status

| Area | Status |
| --- | --- |
| Product and architecture plan | Proposed; decisions recorded in `docs/decisions.md` |
| Application code | Compose skeleton, API and web health endpoints, and a placeholder page only |
| Compose runtime | Configuration parsed; full startup not yet verified |
| Evaluation results | None |
| Public deployment | None |

Read the [product plan](docs/product-plan.md), [decision record](docs/decisions.md), [reference and CI analysis](docs/reference-and-delivery.md), and [first vertical slice proposal](openspec/changes/farodocs-foundation/proposal.md).

## Running locally

The current skeleton has no library, authentication, search, or chat. With Docker Desktop running, use:

```powershell
docker compose up --build -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:3000/api/health
```

The placeholder page is at <http://127.0.0.1:3000>. Stop containers with `docker compose down`; this retains the local database and broker volumes. Use `docker compose down --volumes` only when intentionally discarding all local data. The current Compose password default is for local development only. The full Compose startup has not yet been verified on this machine because Docker Desktop stopped during image download.

Web checks run from `web/` with `npm ci`, `npm run lint`, `npm run typecheck`, and `npm run build`. The Python package can be installed with `py -3 -m pip install -e backend`. API and web health endpoints returned `200` when the processes were run directly on 2026-11-21. Upload, fixtures, database migrations, and behavior tests arrive with the library slice.

## Working agreements

- Technical documentation and code are written in English. The initial UI language will be Spanish, with English available.
- Record product decisions in `docs/decisions.md` and measured experiments with corpus details and limits when they occur.
- Keep implemented behavior, verified behavior, and future plans distinct.
- The repository is linked to `https://github.com/nicovon24/FaroDocs`; publication of source does not imply readiness for public product use. No deployment is planned yet.
