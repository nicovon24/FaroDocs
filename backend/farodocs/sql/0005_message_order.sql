ALTER TABLE conversation_messages ADD COLUMN position integer;
WITH ordered AS (
    SELECT id, row_number() OVER (PARTITION BY conversation_id ORDER BY created_at,id) AS n
    FROM conversation_messages
)
UPDATE conversation_messages m SET position=ordered.n FROM ordered WHERE m.id=ordered.id;
ALTER TABLE conversation_messages ALTER COLUMN position SET NOT NULL;
ALTER TABLE conversation_messages ADD CONSTRAINT conversation_messages_position_unique UNIQUE (conversation_id,position);
