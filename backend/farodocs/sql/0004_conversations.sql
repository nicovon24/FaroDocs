CREATE TABLE conversations (
    id uuid PRIMARY KEY,
    owner_id uuid NOT NULL REFERENCES app_users(id),
    workspace_id uuid NOT NULL REFERENCES workspaces(id),
    title text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversations_title_nonempty CHECK (length(trim(title)) > 0)
);
CREATE INDEX conversations_owner_recent_idx ON conversations(owner_id, workspace_id, updated_at DESC);

CREATE TABLE conversation_messages (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    model_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversation_messages_content_nonempty CHECK (length(trim(content)) > 0)
);
CREATE INDEX conversation_messages_order_idx ON conversation_messages(conversation_id, created_at, id);

CREATE TABLE conversation_citations (
    message_id uuid NOT NULL REFERENCES conversation_messages(id) ON DELETE CASCADE,
    passage_id text NOT NULL REFERENCES chunks(id),
    source_number integer NOT NULL CHECK (source_number > 0),
    PRIMARY KEY (message_id, passage_id),
    UNIQUE (message_id, source_number)
);
CREATE INDEX conversation_citations_passage_idx ON conversation_citations(passage_id);
