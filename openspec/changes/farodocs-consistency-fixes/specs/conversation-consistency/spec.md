# Spec Delta

## Purpose

Conversation consistency keeps cited history aligned with document deletion and makes the displayed messages match the thread selected by the local owner.

## ADDED Requirements

### Requirement: Deleted sources leave no cited history
The system SHALL remove conversations citing a document during its deletion, including citations being saved concurrently, so cleanup can remove the document's passages.

#### Scenario: Answer overlaps deletion
- **WHEN** an answer citing a document and deletion of that document overlap
- **THEN** the answer is either rejected because its source is gone or its conversation is removed by deletion, and document cleanup can complete

### Requirement: Selected thread owns displayed messages
The interface SHALL display messages only for the currently selected conversation.

#### Scenario: Switch between conversations
- **WHEN** the owner selects a different conversation while a detail request is pending
- **THEN** messages from the prior conversation disappear and late responses cannot replace the selected conversation's detail

#### Scenario: Begin a new conversation
- **WHEN** the owner starts a new conversation
- **THEN** the message area shows that new thread's empty state rather than a previous thread's messages
