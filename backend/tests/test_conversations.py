"""Database-backed local conversation tests with a fake Groq response."""

from hashlib import sha256
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time
import unittest
from unittest.mock import patch
import uuid

from fastapi import HTTPException
from pydantic import SecretStr

from farodocs.conversations import Question, ask, create_conversation, delete_conversation, get_conversation, list_conversations
from farodocs.groq import GroqUnavailable
from farodocs.library import WORKSPACE_ID, connection, ensure_owner, process_cleanup
from farodocs.main import delete_document


class ConversationTest(unittest.TestCase):
    def setUp(self):
        self.document_id, self.version_id, self.blob_id = (uuid.uuid4() for _ in range(3))
        self.token = "syntheticcoriander" + uuid.uuid4().hex[:8]
        text = f"The {self.token} review date is December first."
        self.passage_id = sha256(text.encode()).hexdigest()
        with connection() as db:
            ensure_owner(db)
            db.execute("INSERT INTO documents (id,workspace_id,title) VALUES (%s,%s,'Synthetic search document')", (self.document_id, WORKSPACE_ID))
            db.execute("INSERT INTO blobs (id,storage_key,sha256,size_bytes,media_type) VALUES (%s,%s,%s,1,'text/plain')",
                       (self.blob_id, str(self.blob_id), sha256(b'x').hexdigest()))
            db.execute("INSERT INTO document_versions (id,document_id,version_number,blob_id,filename,status,extraction_recipe) "
                       "VALUES (%s,%s,1,%s,'synthetic.txt','ready','blocks-v1')",
                       (self.version_id, self.document_id, self.blob_id))
            db.execute("INSERT INTO chunks (id,version_id,extraction_recipe,ordinal,text_content,text_sha256,locator) "
                       "VALUES (%s,%s,'blocks-v1',0,%s,%s,%s)",
                       (self.passage_id, self.version_id, text, sha256(text.encode()).hexdigest(), json.dumps({'start': 0, 'end': len(text)})))
        self.conversation_id = create_conversation()["id"]

    def tearDown(self):
        with connection() as db:
            db.execute("DELETE FROM conversations WHERE id=%s", (self.conversation_id,))
            db.execute("DELETE FROM chunks WHERE version_id=%s", (self.version_id,))
            db.execute("DELETE FROM processing_jobs WHERE version_id=%s", (self.version_id,))
            db.execute("DELETE FROM document_versions WHERE id=%s", (self.version_id,))
            db.execute("DELETE FROM blobs WHERE id=%s", (self.blob_id,))
            db.execute("DELETE FROM documents WHERE id=%s", (self.document_id,))

    def test_history_citation_and_document_deletion(self):
        secret = "gsk_synthetic_secret_do_not_store"
        with patch("farodocs.conversations.generate_answer", return_value="The date is December first [1].") as provider:
            result = ask(self.conversation_id, Question(question=self.token, api_key=SecretStr(secret), language="en"))
        provider.assert_called_once()
        self.assertEqual(2, len(result["messages"]))
        self.assertEqual(self.passage_id, result["messages"][1]["citations"][0]["passage_id"])
        self.assertEqual("openai/gpt-oss-20b", result["messages"][1]["model_id"])
        self.assertIn(self.conversation_id, [row["id"] for row in list_conversations()])
        self.assertEqual(result["messages"], get_conversation(self.conversation_id)["messages"])
        with connection() as db:
            stored = db.execute("SELECT string_agg(content,' ') AS text FROM conversation_messages WHERE conversation_id=%s", (self.conversation_id,)).fetchone()["text"]
        self.assertNotIn(secret, stored)
        with patch("farodocs.main.dispatch"):
            delete_document(self.document_id)
        with self.assertRaises(HTTPException) as missing:
            get_conversation(self.conversation_id)
        self.assertEqual(404, missing.exception.status_code)

    def test_abstention_invalid_citation_and_provider_error(self):
        with patch("farodocs.conversations.generate_answer") as provider:
            result = ask(self.conversation_id, Question(question="nomatch" + uuid.uuid4().hex, language="en"))
        provider.assert_not_called()
        self.assertEqual([], result["messages"][-1]["citations"])
        with patch("farodocs.conversations.generate_answer", return_value="Unsupported answer [9]."):
            result = ask(self.conversation_id, Question(question=self.token, api_key=SecretStr("fake"), language="en"))
        self.assertEqual([], result["messages"][-1]["citations"])
        self.assertNotIn("Unsupported", result["messages"][-1]["content"])
        with patch("farodocs.conversations.generate_answer", side_effect=GroqUnavailable("Groq request failed")):
            with self.assertRaises(HTTPException) as failure:
                ask(self.conversation_id, Question(question=self.token, api_key=SecretStr("private-key")))
        self.assertEqual(502, failure.exception.status_code)
        self.assertNotIn("private-key", str(failure.exception.detail))
        delete_conversation(self.conversation_id)
        with self.assertRaises(HTTPException):
            get_conversation(self.conversation_id)

    def test_deletion_waits_for_in_flight_citation_and_cleanup_completes(self):
        source_locked = Event()
        release_answer = Event()

        class PausedConnection:
            def __init__(self):
                self.inner = connection()

            def __enter__(self):
                self.inner.__enter__()
                return self

            def __exit__(self, *args):
                return self.inner.__exit__(*args)

            def execute(self, query, params=None):
                result = self.inner.execute(query, params)
                if "FOR SHARE OF d" in query:
                    source_locked.set()
                    if not release_answer.wait(10):
                        raise TimeoutError("Synthetic answer pause timed out")
                return result

        with ThreadPoolExecutor(max_workers=2) as executor:
            try:
                with patch("farodocs.conversations.connection", side_effect=PausedConnection), \
                     patch("farodocs.conversations.generate_answer", return_value="The date is December first [1]."), \
                     patch("farodocs.main.dispatch"):
                    answering = executor.submit(ask, self.conversation_id, Question(question=self.token, api_key=SecretStr("fake")))
                    self.assertTrue(source_locked.wait(10), "Answer did not lock its cited source")
                    deleting = executor.submit(delete_document, self.document_id)
                    time.sleep(0.2)
                    self.assertFalse(deleting.done(), "Deletion did not wait for the cited source")
                    release_answer.set()
                    try:
                        answering.result(timeout=10)
                    except HTTPException as exc:
                        self.assertEqual(404, exc.status_code)
                    deleted = deleting.result(timeout=10)
            finally:
                release_answer.set()

        process_cleanup(str(deleted["job_id"]))
        with connection() as db:
            job = db.execute("SELECT status FROM processing_jobs WHERE id=%s", (deleted["job_id"],)).fetchone()
        self.assertEqual("ready", job["status"])
        with self.assertRaises(HTTPException):
            get_conversation(self.conversation_id)


if __name__ == "__main__":
    unittest.main()
