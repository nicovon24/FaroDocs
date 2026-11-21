-- Run with psql -v ON_ERROR_STOP=1. The transaction is rolled back.
BEGIN;

INSERT INTO app_users (id, display_name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Local test owner');
INSERT INTO workspaces (id, owner_id, name)
VALUES ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'A');
INSERT INTO documents (id, workspace_id, title)
VALUES ('00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000002', 'Example');
INSERT INTO blobs (id, storage_key, sha256, size_bytes, media_type)
VALUES ('00000000-0000-0000-0000-000000000004', 'test/blob-a', repeat('a', 64), 4, 'text/plain');
INSERT INTO blobs (id, storage_key, sha256, size_bytes, media_type)
VALUES ('00000000-0000-0000-0000-000000000005', 'test/blob-b', repeat('b', 64), 4, 'text/plain');
INSERT INTO document_versions (id, document_id, version_number, blob_id, filename)
VALUES ('00000000-0000-0000-0000-000000000006', '00000000-0000-0000-0000-000000000003', 1,
        '00000000-0000-0000-0000-000000000004', 'a.txt');

DO $$
BEGIN
    BEGIN
        INSERT INTO document_versions (id, document_id, version_number, blob_id, filename)
        VALUES ('00000000-0000-0000-0000-000000000007', '00000000-0000-0000-0000-000000000003', 2,
                '00000000-0000-0000-0000-000000000005', 'b.txt');
        RAISE EXCEPTION 'expected one-current-version constraint';
    EXCEPTION WHEN unique_violation THEN
        NULL;
    END;

    BEGIN
        INSERT INTO chunks (id, version_id, extraction_recipe, ordinal, text_content, text_sha256, locator)
        VALUES ('bad', '00000000-0000-0000-0000-000000000006', 'v1', 0, 'Text', repeat('a', 64), '[]');
        RAISE EXCEPTION 'expected object locator constraint';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;

    BEGIN
        UPDATE documents SET is_deleted = true
        WHERE id = '00000000-0000-0000-0000-000000000003';
        RAISE EXCEPTION 'expected tombstone constraint';
    EXCEPTION WHEN check_violation THEN
        NULL;
    END;
END $$;

ROLLBACK;
