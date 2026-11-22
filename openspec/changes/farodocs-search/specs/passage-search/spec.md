# Spec Delta

## Purpose

Passage search lets the local owner locate source text across the ready current versions in the document library and inspect each result in its original context.

## ADDED Requirements

### Requirement: Ranked passage search
The system SHALL accept a nonempty bounded query and return ranked matching passages with document title, version, passage ID, and source locator.

#### Scenario: Matching passages
- **WHEN** the owner searches for words present in extracted passages
- **THEN** matching passages appear with a useful excerpt and source information

#### Scenario: Empty or unmatched query
- **WHEN** the query is empty or has no matches
- **THEN** the interface shows guidance or an explicit no-results state without unrelated documents

### Requirement: Current visible scope
The system SHALL search only ready current versions of documents visible in the local workspace.

#### Scenario: Replacement and deletion
- **WHEN** a document is replaced or deleted
- **THEN** search excludes superseded or deleted passages

### Requirement: Source navigation
The system SHALL provide an inspectable source link for each search result, with a PDF page anchor when its locator includes a page.

#### Scenario: Open result
- **WHEN** the owner opens a result source
- **THEN** the original document version opens at its available location
