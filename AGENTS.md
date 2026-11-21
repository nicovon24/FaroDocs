# FaroDocs agent guide

Read `README.md`, `docs/product-plan.md`, and `docs/decisions.md` before implementation. The OpenSpec change for the active vertical slice is the behavioral contract. Technical documentation and code use English; user-facing UI starts in Spanish and offers English.

## Originality and evidence

- `Blandskron/AgenteIADocumental` is a comparison reference. Analyze its practices without copying its code, documentation, prompts, UI, assets, or file structure into FaroDocs.
- Label proposed, implemented, and evaluated behavior separately. Record corpus size, model/provider configuration, measured results, and limitations before making quality claims.
- Use synthetic documents for development and verification. Keep uploaded files and credentials out of Git.

## Planning and orchestration

- Request `gpt-6-astra` with high reasoning effort for substantial architecture, planning, and coordination when model selection is available. If the runtime cannot select or confirm the coordinator model, continue with the assigned model and report requested versus confirmed model/effort as separate fields; use `unconfirmed` for unavailable confirmation.
- Delegate only bounded tasks with an objective, exclusive file/module ownership, acceptance criteria, a verification step, and an expected handoff. Keep at most two subagents active and have only the coordinator delegate.
- Apply OpenSpec one vertical slice at a time. Review the diff and the affected behavior before closing a slice.

## Frontend

- Use the installed `impeccable` skill when designing, shaping, or reviewing product UI. Create FaroDocs-specific product and visual documentation and tokens; do not import a reference project's visual system.
- Use the installed `playwright-cli` skill and command for browser navigation, user flows, responsive checks, and screenshots. Build before browser verification when tests serve compiled assets.
- Use `web-design-guidelines` when asked to audit the interface against Vercel's guidelines.
- Verify Spanish and English copy, keyboard/focus behavior, contrast, narrow layouts, and citation navigation for affected screens.

## Delivery

- Start CI with checks that correspond to implemented modules; expand it with search, chat, permissions, OCR, and integrations as they land. Keep synthetic and live-provider evidence distinct.
- Do not create a remote, push, deploy, or describe FaroDocs as ready for public use without a later user request and the required security/privacy verification.
