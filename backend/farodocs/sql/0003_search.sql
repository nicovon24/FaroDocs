CREATE INDEX chunks_search_idx ON chunks USING gin (to_tsvector('simple', text_content));
