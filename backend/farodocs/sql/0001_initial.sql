CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE app_users (
    id uuid PRIMARY KEY,
    google_subject text UNIQUE,
    display_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT app_users_name_nonempty CHECK (length(trim(display_name)) > 0)
);

CREATE TABLE workspaces (
    id uuid PRIMARY KEY,
    owner_id uuid NOT NULL REFERENCES app_users(id),
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT workspaces_name_nonempty CHECK (length(trim(name)) > 0)
);

CREATE TABLE folders (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    parent_id uuid,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, id),
    FOREIGN KEY (workspace_id, parent_id) REFERENCES folders(workspace_id, id),
    CONSTRAINT folders_name_nonempty CHECK (length(trim(name)) > 0),
    CONSTRAINT folders_not_self_parent CHECK (parent_id IS DISTINCT FROM id)
);

CREATE TABLE documents (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    folder_id uuid,
    title text NOT NULL,
    is_deleted boolean NOT NULL DEFAULT false,
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, id),
    FOREIGN KEY (workspace_id, folder_id) REFERENCES folders(workspace_id, id),
    CONSTRAINT documents_title_nonempty CHECK (length(trim(title)) > 0),
    CONSTRAINT documents_tombstone_consistent CHECK (is_deleted = (deleted_at IS NOT NULL))
);
CREATE INDEX documents_workspace_visible_idx ON documents(workspace_id, created_at DESC)
    WHERE is_deleted = false;

CREATE TABLE blobs (
    id uuid PRIMARY KEY,
    storage_key text NOT NULL UNIQUE,
    sha256 char(64) NOT NULL,
    size_bytes bigint NOT NULL,
    media_type text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT blobs_nonempty_key CHECK (length(storage_key) > 0),
    CONSTRAINT blobs_sha256_hex CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT blobs_size_positive CHECK (size_bytes > 0)
);

CREATE TABLE document_versions (
    id uuid PRIMARY KEY,
    document_id uuid NOT NULL REFERENCES documents(id),
    version_number integer NOT NULL,
    blob_id uuid NOT NULL UNIQUE REFERENCES blobs(id),
    filename text NOT NULL,
    status text NOT NULL DEFAULT 'queued',
    error_code text,
    error_message text,
    extraction_recipe text,
    is_current boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_number),
    CONSTRAINT document_versions_number_positive CHECK (version_number > 0),
    CONSTRAINT document_versions_status_valid CHECK (status IN ('queued', 'processing', 'ready', 'failed')),
    CONSTRAINT document_versions_error_on_failure CHECK (
        (status = 'failed' AND error_code IS NOT NULL AND error_message IS NOT NULL)
        OR (status <> 'failed' AND error_code IS NULL AND error_message IS NULL)
    )
);
CREATE UNIQUE INDEX document_versions_one_current_idx ON document_versions(document_id)
    WHERE is_current = true;

CREATE TABLE processing_jobs (
    id uuid PRIMARY KEY,
    version_id uuid NOT NULL REFERENCES document_versions(id),
    kind text NOT NULL,
    status text NOT NULL DEFAULT 'queued',
    attempt integer NOT NULL DEFAULT 0,
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT processing_jobs_kind_valid CHECK (kind IN ('extract', 'delete')),
    CONSTRAINT processing_jobs_status_valid CHECK (status IN ('queued', 'processing', 'ready', 'failed')),
    CONSTRAINT processing_jobs_attempt_nonnegative CHECK (attempt >= 0)
);
CREATE INDEX processing_jobs_version_idx ON processing_jobs(version_id, created_at DESC);

CREATE TABLE chunks (
    id text PRIMARY KEY,
    version_id uuid NOT NULL REFERENCES document_versions(id),
    extraction_recipe text NOT NULL,
    ordinal integer NOT NULL,
    text_content text NOT NULL,
    text_sha256 char(64) NOT NULL,
    locator jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (version_id, extraction_recipe, ordinal),
    CONSTRAINT chunks_ordinal_nonnegative CHECK (ordinal >= 0),
    CONSTRAINT chunks_text_nonempty CHECK (length(text_content) > 0),
    CONSTRAINT chunks_sha256_hex CHECK (text_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT chunks_locator_object CHECK (jsonb_typeof(locator) = 'object')
);
CREATE INDEX chunks_version_idx ON chunks(version_id, ordinal);

CREATE TABLE tags (
    id uuid PRIMARY KEY,
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    name text NOT NULL,
    UNIQUE (workspace_id, id),
    UNIQUE (workspace_id, name),
    CONSTRAINT tags_name_nonempty CHECK (length(trim(name)) > 0)
);

CREATE TABLE document_tags (
    workspace_id uuid NOT NULL,
    document_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (workspace_id, document_id) REFERENCES documents(workspace_id, id),
    FOREIGN KEY (workspace_id, tag_id) REFERENCES tags(workspace_id, id)
);

CREATE TABLE favorites (
    user_id uuid NOT NULL REFERENCES app_users(id),
    document_id uuid NOT NULL REFERENCES documents(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, document_id)
);
