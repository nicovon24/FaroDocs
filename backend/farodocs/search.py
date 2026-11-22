"""Bounded lexical retrieval over visible current document passages."""

from farodocs.library import WORKSPACE_ID, connection


def search_passages(query: str, limit: int = 20) -> list[dict]:
    with connection() as db:
        return db.execute(
            "WITH query AS (SELECT websearch_to_tsquery('simple', %s) AS terms) "
            "SELECT c.id AS passage_id, "
            "left(ts_headline('simple', c.text_content, query.terms, "
            "'MaxFragments=2,MaxWords=60,MinWords=15,StartSel=« ,StopSel= »'),1200) AS text_content, c.locator, "
            "d.id AS document_id, d.title, v.id AS version_id, v.version_number, "
            "ts_rank_cd(to_tsvector('simple', c.text_content), query.terms) AS rank "
            "FROM query CROSS JOIN chunks c "
            "JOIN document_versions v ON v.id=c.version_id "
            "JOIN documents d ON d.id=v.document_id "
            "WHERE d.workspace_id=%s AND NOT d.is_deleted AND v.is_current AND v.status='ready' "
            "AND to_tsvector('simple', c.text_content) @@ query.terms "
            "ORDER BY rank DESC, c.id LIMIT %s",
            (query, WORKSPACE_ID, limit),
        ).fetchall()
