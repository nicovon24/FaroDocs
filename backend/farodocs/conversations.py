"""Local-owner conversation history and source-backed questions."""

import re
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, SecretStr

from farodocs.groq import DEFAULT_MODEL, SUPPORTED_MODELS, GroqUnavailable, generate_answer
from farodocs.library import OWNER_ID, WORKSPACE_ID, connection, ensure_owner
from farodocs.search import search_passages


router = APIRouter()
REFERENCES = re.compile(r"\[(\d+)\]")
ABSTAIN = {
    "es": "No puedo responder con respaldo en los documentos disponibles.",
    "en": "I cannot answer from the available documents.",
}


def _conversation(db, conversation_id):
    row = db.execute(
        "SELECT id,title,created_at,updated_at FROM conversations "
        "WHERE id=%s AND owner_id=%s AND workspace_id=%s",
        (conversation_id, OWNER_ID, WORKSPACE_ID),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Conversation not found")
    return row


@router.get("/conversations")
def list_conversations() -> list[dict]:
    with connection() as db:
        return db.execute(
            "SELECT c.id,c.title,c.created_at,c.updated_at,count(m.id) AS message_count "
            "FROM conversations c LEFT JOIN conversation_messages m ON m.conversation_id=c.id "
            "WHERE c.owner_id=%s AND c.workspace_id=%s "
            "GROUP BY c.id ORDER BY c.updated_at DESC,c.id DESC",
            (OWNER_ID, WORKSPACE_ID),
        ).fetchall()


@router.post("/conversations", status_code=201)
def create_conversation() -> dict:
    conversation_id = uuid.uuid4()
    with connection() as db:
        ensure_owner(db)
        return db.execute(
            "INSERT INTO conversations (id,owner_id,workspace_id,title) "
            "VALUES (%s,%s,%s,'New conversation') RETURNING id,title,created_at,updated_at",
            (conversation_id, OWNER_ID, WORKSPACE_ID),
        ).fetchone()


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: uuid.UUID) -> dict:
    with connection() as db:
        conversation = _conversation(db, conversation_id)
        messages = db.execute(
            "SELECT id,role,content,model_id,created_at FROM conversation_messages "
            "WHERE conversation_id=%s ORDER BY position",
            (conversation_id,),
        ).fetchall()
        for message in messages:
            message["citations"] = db.execute(
                "SELECT cc.source_number,c.id AS passage_id,left(c.text_content,1200) AS text_content,c.locator,"
                "d.id AS document_id,d.title,v.id AS version_id,v.version_number "
                "FROM conversation_citations cc JOIN chunks c ON c.id=cc.passage_id "
                "JOIN document_versions v ON v.id=c.version_id "
                "JOIN documents d ON d.id=v.document_id "
                "WHERE cc.message_id=%s AND d.workspace_id=%s AND NOT d.is_deleted "
                "ORDER BY cc.source_number",
                (message["id"], WORKSPACE_ID),
            ).fetchall()
    return {**conversation, "messages": messages}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: uuid.UUID) -> None:
    with connection() as db:
        _conversation(db, conversation_id)
        db.execute("DELETE FROM conversations WHERE id=%s", (conversation_id,))


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    api_key: SecretStr | None = None
    model: Literal["openai/gpt-oss-20b", "openai/gpt-oss-120b"] = DEFAULT_MODEL
    language: Literal["es", "en"] = "es"


@router.post("/conversations/{conversation_id}/messages")
def ask(conversation_id: uuid.UUID, request: Question) -> dict:
    question = request.question.strip()
    if not question:
        raise HTTPException(422, "Question must not be empty")
    if request.api_key and len(request.api_key.get_secret_value()) > 256:
        raise HTTPException(422, "Enter a valid Groq API key")
    with connection() as db:
        conversation = _conversation(db, conversation_id)
        history = db.execute(
            "SELECT role,content FROM conversation_messages WHERE conversation_id=%s "
            "ORDER BY position DESC LIMIT 6",
            (conversation_id,),
        ).fetchall()[::-1]
    sources = search_passages(question, 6)
    answer = ABSTAIN[request.language]
    citation_numbers: list[int] = []
    model_id = None
    if sources:
        key = request.api_key.get_secret_value().strip() if request.api_key else ""
        if not key or len(key) > 256:
            raise HTTPException(422, "Enter a valid Groq API key")
        if request.model not in SUPPORTED_MODELS:
            raise HTTPException(422, "Unsupported model")
        try:
            candidate = generate_answer(question, sources, history, key, request.model)
        except GroqUnavailable as exc:
            raise HTTPException(502, str(exc)) from None
        numbers = [int(number) for number in REFERENCES.findall(candidate)]
        if numbers and all(1 <= number <= len(sources) for number in numbers):
            answer = candidate
            citation_numbers = list(dict.fromkeys(numbers))
        model_id = request.model
    with connection() as db:
        if citation_numbers:
            ids = [sources[number - 1]["passage_id"] for number in citation_numbers]
            valid = db.execute(
                "SELECT c.id FROM chunks c JOIN document_versions v ON v.id=c.version_id "
                "JOIN documents d ON d.id=v.document_id "
                "WHERE c.id=ANY(%s) AND d.workspace_id=%s AND NOT d.is_deleted "
                "AND v.is_current AND v.status='ready' ORDER BY d.id,v.id FOR SHARE OF d",
                (ids, WORKSPACE_ID),
            ).fetchall()
            if len(valid) != len(ids):
                raise HTTPException(409, "Sources changed while answering; ask again")
        _conversation(db, conversation_id)
        db.execute("SELECT id FROM conversations WHERE id=%s FOR UPDATE", (conversation_id,))
        position = db.execute("SELECT coalesce(max(position),0) AS n FROM conversation_messages WHERE conversation_id=%s", (conversation_id,)).fetchone()["n"]
        user_id, assistant_id = uuid.uuid4(), uuid.uuid4()
        db.execute(
            "INSERT INTO conversation_messages (id,conversation_id,role,content,position) VALUES (%s,%s,'user',%s,%s)",
            (user_id, conversation_id, question, position + 1),
        )
        db.execute(
            "INSERT INTO conversation_messages (id,conversation_id,role,content,model_id,position) "
            "VALUES (%s,%s,'assistant',%s,%s,%s)",
            (assistant_id, conversation_id, answer, model_id, position + 2),
        )
        for number in citation_numbers:
            db.execute(
                "INSERT INTO conversation_citations (message_id,passage_id,source_number) VALUES (%s,%s,%s)",
                (assistant_id, sources[number - 1]["passage_id"], number),
            )
        title = question[:100] if conversation["title"] == "New conversation" else conversation["title"]
        db.execute("UPDATE conversations SET title=%s,updated_at=now() WHERE id=%s", (title, conversation_id))
    return get_conversation(conversation_id)
