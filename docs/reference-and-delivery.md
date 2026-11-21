# Reference analysis and delivery plan

Observed on 2026-11-21. This is a read-only comparison of [Blandskron/AgenteIADocumental](https://github.com/Blandskron/AgenteIADocumental), not a source for FaroDocs code, prose, prompts, visuals, assets, or directory layout. Its stated features and dated verification evidence belong to that repository, not to FaroDocs.

## What the reference demonstrates

The reference README describes document upload, organization, search, contextual chat with inspectable sources, conversation history, PDF export, access control, and optional Drive import. Its current architecture uses Django for identity plus eleven application services, React/TypeScript, PostgreSQL/pgvector, CPU embeddings, and Groq for generation. FaroDocs has overlapping product goals but will make its own decisions from requirements and measured tradeoffs. In particular, the proposed modular FastAPI backend plus Python worker does not split each domain capability into a deployable service; a measured scaling, deployment, ownership, or fault-isolation need would have to justify another service.

Sources: [reference README](https://github.com/Blandskron/AgenteIADocumental/blob/main/README.md), [reference architecture](https://github.com/Blandskron/AgenteIADocumental/blob/main/docs/architecture.md).

## CI/CD observed in the reference

The single [GitHub Actions workflow](https://github.com/Blandskron/AgenteIADocumental/blob/main/.github/workflows/validate.yml) runs on pull requests and pushes to `main`, with read-only repository permissions. Its jobs are `release`, `frontend`, `compose`, `auth`, `postgres`, `rag-groq`, and `auth-db-roles`.

| Area | Observed checks | FaroDocs lesson |
| --- | --- | --- |
| Frontend | `npm ci`, dependency audit, lint, typecheck, format check, tests, build, and browser tests in a pinned Playwright container | Keep the browser suite tied to the built UI and synthetic contracts; adopt checks as each script exists. |
| Compose | Render and assert service configuration, loopback binding, environment exposure, health/dependency conditions, and runtime restrictions | Validate the real local topology and avoid leaking server secrets into client configuration. |
| Backend and data | Service-specific tests and lint, DB role checks, runtime-image checks, migration/integrity probes | Start with focused FastAPI and data-layer tests plus migration checks; add tenancy and DB-role gates when those boundaries exist. |
| Cross-service release | Build a synthetic Compose installation, run a document flow, audit final images and dependency graphs, upload JSON evidence, then tear down only the synthetic environment | Keep an end-to-end synthetic gate and dated artifacts once the vertical path exists. |

The [release verification guide](https://github.com/Blandskron/AgenteIADocumental/blob/main/docs/release/README.md) distinguishes simulated Groq/OAuth checks from live integration and records image/commit-specific evidence. The workflow is **CI validation**, not evidence of an automated production deployment: no deploy job was observed in `validate.yml`. A successful synthetic run cannot establish live provider behavior or public readiness. The current workflow is large for a new project; duplicating all of its jobs before FaroDocs has those components would add maintenance and runtime without coverage value. Some third-party actions are referenced by major tags in the observed workflow; FaroDocs can consider immutable SHA pinning when CI is introduced.

## Skills and frontend practice

The reference uses versioned, domain-specific skills under `.agents/skills`, indexed by its [maintainers guide](https://github.com/Blandskron/AgenteIADocumental/blob/main/docs/maintainers.md). Its [frontend skill](https://github.com/Blandskron/AgenteIADocumental/blob/main/.agents/skills/documental-frontend/SKILL.md) points to frontend instructions and verification, and calls out session/tenant continuity, responsive layouts, keyboard focus, contrast, and a build before browser checks. Its [frontend development guide](https://github.com/Blandskron/AgenteIADocumental/blob/main/frontend/docs/DEVELOPMENT.md) names audit, lint, typecheck, format, unit, build, and browser commands. Those procedures are useful checkpoints; FaroDocs will write its own local guidance when the UI exists.

For FaroDocs, use the installed **Impeccable** skill when shaping or reviewing the UI, **Playwright CLI** for navigation, flows, responsive checks, and screenshots, and **web-design-guidelines** for requested Vercel interface audits. These were also used in the local `ai-engineering-projects/projects/document-intelligence` visual work. Its optional warm visual foundation is context, not a design to copy. FaroDocs needs its own `DESIGN.md`, semantic tokens, Spanish-first copy, English translation, accessible source inspection, and narrow/desktop verification when implemented.

The local `ai-engineering-projects/AGENTS.md` requests Astra high for substantial architecture/planning, bounded delegation with explicit ownership and verification, and separate requested vs runtime-confirmed model records. FaroDocs adopts that orchestration preference in its own `AGENTS.md`. This document does not claim that the current planning turn ran on Astra high; the runtime did not expose a main-model selector or confirmed identity.

## FaroDocs CI plan, by stage

1. **Foundation/library:** add a local validation script and CI only after the corresponding project exists: Python format/lint and focused FastAPI/data-layer tests, migration checks, TypeScript lint/typecheck/unit/build, Compose config, and synthetic upload/library flow. Capture failing fixture names and exact commands.
2. **Search/chat:** add deterministic retrieval and citation/abstention tests, then a synthetic Compose end-to-end flow. Keep model quality evaluation separate from code correctness checks.
3. **Permissions/OCR/Drive:** add two-user leak tests, deletion/limit checks, scanned-PDF fixtures, and mocked OAuth. A live OAuth or model smoke check requires explicit credentials and must be labeled separately.
4. **Demo gate:** audit dependencies and final images, verify clean installation and restart/persistence, run adversarial-document cases, and record the corpus, revisions, image IDs, and residual risks.

No CI workflow or deployment pipeline exists in FaroDocs yet. Do not add automated deployment until the user requests a destination and the public-readiness gates pass.
