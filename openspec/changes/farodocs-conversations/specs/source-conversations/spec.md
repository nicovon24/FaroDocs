# Spec Delta

## Purpose

Source conversations let the local owner ask questions about visible documents, inspect evidence, and reopen previous messages without storing a provider secret.

## ADDED Requirements

### Requirement: Local conversation history
The system SHALL let the local owner create, list, reopen, and delete conversations and SHALL preserve messages across browser reloads.

#### Scenario: Reopen a conversation
- **WHEN** the owner asks a question and reloads the browser
- **THEN** the conversation and its messages remain available

#### Scenario: Delete a conversation
- **WHEN** the owner deletes a conversation
- **THEN** it and its messages are no longer listed or accessible

### Requirement: User-key Groq answer
The system SHALL accept a Groq key for an answer request without storing it, SHALL send only bounded retrieved passages to the provider, and SHALL identify the model used.

#### Scenario: Answerable question
- **WHEN** a question matches visible passages and the provider returns an answer with valid source references
- **THEN** the answer and its source links are saved and displayed

#### Scenario: No evidence
- **WHEN** no visible passage matches a question
- **THEN** the system abstains without calling the provider

#### Scenario: Provider failure
- **WHEN** Groq rejects or cannot complete the request
- **THEN** the owner sees a useful error and the key is absent from the response and stored records

### Requirement: Citation integrity and lifecycle
The system SHALL accept only references to passages retrieved for the current question and SHALL remove history that cites a deleted document.

#### Scenario: Invalid provider citation
- **WHEN** the provider refers to an unknown passage or returns an unsupported uncited answer
- **THEN** the system records an abstention rather than presenting the answer as sourced

#### Scenario: Delete a cited document
- **WHEN** a cited document is deleted
- **THEN** conversations containing its cited passage are no longer accessible
