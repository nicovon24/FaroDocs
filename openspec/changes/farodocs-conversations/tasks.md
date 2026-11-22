# Tasks

## 1. Conversation storage and lifecycle

- [x] 1.1 Add migrations and scoped create/list/read/delete routes; verify local history persists and deletion hides it in database-backed tests.
- [x] 1.2 Remove conversations citing a deleted document before passage cleanup; verify with a synthetic citation lifecycle test.

## 2. Provider answer flow

- [x] 2.1 Add a bounded Groq adapter and question route with citation validation, abstention, and secret-safe errors; verify using a fake provider and synthetic passages.
- [x] 2.2 Document key handling, provider data transfer, model, API, and unverified quality limits; verify examples against the local stack.

## 3. Interface

- [x] 3.1 Add bilingual conversation list, key entry, composer, messages, and source links; verify history, errors, focus, and narrow layouts in the browser.

## 4. Integration review

- [x] 4.1 Run affected backend/web checks, inspect the diff, and record remaining limitations.

## Workflow follow-up

- Archive after review and acceptance.
