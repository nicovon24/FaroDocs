# Spec Delta

## Purpose

Document version availability keeps a usable ready version visible while a replacement is processed and publishes a successful replacement without a search gap.

## ADDED Requirements

### Requirement: Ready version remains available during replacement
The system SHALL keep the latest published ready version current and searchable until a newer replacement is ready.

#### Scenario: Replacement is processing
- **WHEN** a replacement version is queued or processing for a document with a ready current version
- **THEN** search and the library continue to use the ready current version, while the replacement remains inspectable by version

#### Scenario: Replacement fails
- **WHEN** extraction of a replacement version fails
- **THEN** the prior ready version remains current and searchable and the failed version remains inspectable for retry

### Requirement: Successful replacement is published atomically
The system SHALL promote a ready replacement as the sole current version without publishing an older replacement over a newer current version.

#### Scenario: Replacement becomes ready
- **WHEN** extraction of a newer replacement succeeds
- **THEN** that version becomes current and searchable, and the prior version stops appearing in current search

#### Scenario: Workers finish out of order
- **WHEN** an older replacement finishes after a newer version became current
- **THEN** the newer version remains current
