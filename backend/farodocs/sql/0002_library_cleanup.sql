ALTER TABLE document_versions ALTER COLUMN blob_id DROP NOT NULL;
ALTER TABLE document_versions ADD CONSTRAINT document_versions_blob_for_visible
    CHECK (blob_id IS NOT NULL OR status = 'failed');
