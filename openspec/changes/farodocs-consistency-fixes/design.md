# Design

## Context

See proposal.md. PostgreSQL holds current-version and citation state; extraction runs in a separate worker. The browser loads conversation details asynchronously.

## Goals / Non-Goals

**Goals:** Preserve a ready search target through replacement processing, serialize citation writes with deletion, and tie rendered messages to the selected thread.

**Non-Goals:** Add accounts, change retrieval ranking, or alter provider behavior.

## Decisions

- A replacement is inserted as noncurrent when a current version exists. Extraction holds the document row lock, writes passages, and promotes a successful version only if its version number exceeds the current version. The current ready version stays available on failure. This uses the existing unique-current index and avoids a new schema state.
- A question locks its cited document rows before the conversation row in the final save transaction. Deletion locks the document row before deleting cited conversations and marking the document deleted. This gives both paths the same lock order. The source visibility check remains inside the answer transaction.
- The chat UI clears detail on selection and cancels or ignores obsolete detail requests. It renders a detail only when its ID matches the selected ID.
- Library polling watches pending versions in the open detail, since the library row remains ready during replacement processing.

## Risks / Trade-offs

- Keeping an older ready version current means replacement content is visible only in its version tab until extraction succeeds. The library should keep polling the pending version.
- Multiple pending replacements can complete out of order. Version-number comparison prevents an older completion from downgrading the current version.
- PostgreSQL lock contention can delay deletion or answer save briefly. A bounded provider request occurs before these locks are acquired.

## Migration Plan

No schema migration is required. Existing documents retain their current-version flag. The change applies to new replacements after the updated API and worker start.
