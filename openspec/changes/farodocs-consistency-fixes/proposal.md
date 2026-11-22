# Proposal

## Why

The local preview can lose search availability during a replacement upload, leave cited history behind during a concurrent deletion, or briefly show the wrong conversation. These are correctness issues in the existing document and chat flows.

## What Changes

- Keep the last ready document version searchable until a newer version becomes ready; a failed replacement leaves the ready version current.
- Serialize document deletion with citation creation so deleting a cited document cannot leave history that blocks cleanup.
- Clear stale conversation details and ignore out-of-order detail responses when the selected conversation changes.

## Capabilities

### New Capabilities

- `document-version-availability`: Continuity of the current searchable version through replacement processing and failure.
- `conversation-consistency`: Correct citation cleanup under concurrent deletion and correct selected-thread rendering.

### Modified Capabilities

None. Existing requirements are recorded in unarchived change deltas rather than main specs.

## Impact

The upload API, extraction worker, conversation API, chat UI, and synthetic integration checks change. No API route or external dependency changes.
