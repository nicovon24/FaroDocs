# Spec Delta

## Purpose

The document library lets a local owner ingest, organize, version, and inspect documents and extracted passages before retrieval or chat features are introduced.

## ADDED Requirements

### Requirement: Supported document upload
The system SHALL accept text-bearing PDF, DOCX, TXT, and Markdown files within configured upload limits and SHALL reject unsupported, oversized, or malformed files with a clear reason.

#### Scenario: Valid document upload
- **WHEN** the owner uploads a supported file within the configured limits
- **THEN** the library creates a document version and shows its processing state

#### Scenario: Invalid upload
- **WHEN** the owner uploads an unsupported, oversized, or malformed file
- **THEN** the upload is rejected or marked failed with a reason visible in the library

### Requirement: Processing visibility
The system SHALL show queued, processing, ready, and failed states for each version and SHALL preserve a useful failure reason for a failed version.

#### Scenario: Processing completes
- **WHEN** extraction completes for a queued version
- **THEN** its state changes to ready and extracted passages become inspectable

#### Scenario: Processing fails
- **WHEN** extraction cannot complete
- **THEN** its state changes to failed and the owner can inspect the reason

### Requirement: Inspectable passages
The system SHALL associate each extracted passage with a document version, a stable ID for that version and extraction recipe, and a source locator that the owner can open.

#### Scenario: Open a PDF passage
- **WHEN** the owner opens a passage from a text-bearing PDF
- **THEN** the library shows the original document version and its page or a text fallback if precise positioning is unavailable

#### Scenario: Open a text passage
- **WHEN** the owner opens a passage from a DOCX, TXT, or Markdown version
- **THEN** the library shows its extracted text and paragraph or character location

### Requirement: Library organization
The system SHALL let the owner list, filter, and organize documents with folders, tags, and favorites.

#### Scenario: Organize a document
- **WHEN** the owner assigns a folder, tags, or favorite state to a document
- **THEN** the library reflects the change in the document list and relevant filters

### Requirement: Document versions
The system SHALL preserve prior versions when the owner uploads a replacement file and SHALL identify the current version.

#### Scenario: Upload replacement
- **WHEN** the owner adds a new file as a version of an existing document
- **THEN** the library shows the new processing state and retains access to prior versions

### Requirement: Local document deletion
The system SHALL let the owner delete a document and its locally stored original files and extracted data, and SHALL make the document unavailable immediately after deletion begins.

#### Scenario: Delete document
- **WHEN** the owner confirms deletion of a document
- **THEN** the document and its passages disappear from the library and local storage cleanup is recorded as completed or failed
