"""Synthetic replacement tests for current-version availability."""

import asyncio
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import uuid

from fastapi import UploadFile

from farodocs.library import WORKSPACE_ID, connection, ensure_owner, passage_id, process_extraction
from farodocs.main import get_document, list_documents, upload_version
from farodocs.search import search_passages
from farodocs.uploads import store_original


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "Set DATABASE_URL for database-backed checks")
class VersionAvailabilityTest(unittest.TestCase):
    def test_failed_and_out_of_order_replacements_keep_latest_ready_current(self):
        document_id, old_version_id, old_blob_id = (uuid.uuid4() for _ in range(3))
        token = uuid.uuid4().hex
        old_text = f"faroold{token} stable source."
        newer_text = f"faronewer{token} published source."
        previous_root = os.environ.get("FARODOCS_STORAGE_ROOT")
        with TemporaryDirectory() as directory:
            os.environ["FARODOCS_STORAGE_ROOT"] = directory
            old_key, old_digest = store_original(old_text.encode(), Path(directory))
            try:
                with connection() as db:
                    ensure_owner(db)
                    db.execute("INSERT INTO documents (id,workspace_id,title) VALUES (%s,%s,'Synthetic version continuity')", (document_id, WORKSPACE_ID))
                    db.execute("INSERT INTO blobs (id,storage_key,sha256,size_bytes,media_type) VALUES (%s,%s,%s,%s,'text/plain')",
                               (old_blob_id, old_key, old_digest, len(old_text.encode())))
                    db.execute("INSERT INTO document_versions (id,document_id,version_number,blob_id,filename,status,extraction_recipe) "
                               "VALUES (%s,%s,1,%s,'old.txt','ready','blocks-v1')", (old_version_id, document_id, old_blob_id))
                    db.execute("INSERT INTO chunks (id,version_id,extraction_recipe,ordinal,text_content,text_sha256,locator) "
                               "VALUES (%s,%s,'blocks-v1',0,%s,%s,%s)",
                               (passage_id(old_version_id, 0, old_text), old_version_id, old_text,
                                sha256(old_text.encode()).hexdigest(), '{"kind":"text","start":0,"end":40}'))

                def upload_text(name, content):
                    file = UploadFile(file=BytesIO(content.encode()), filename=name)
                    with patch("farodocs.main.dispatch"):
                        return asyncio.run(upload_version(document_id, file))

                older = upload_text("older.txt", f"faroolder{token} pending source.")
                newer = upload_text("newer.txt", newer_text)
                failed = upload_text("failed.txt", f"farofailed{token} unavailable source.")

                self.assertEqual(old_version_id, next(v["id"] for v in get_document(document_id)["versions"] if v["is_current"]))
                self.assertEqual(old_version_id, next(d["version_id"] for d in list_documents() if d["id"] == document_id))
                self.assertTrue(any(row["document_id"] == document_id for row in search_passages(f"faroold{token}")))

                with connection() as db:
                    key = db.execute("SELECT b.storage_key FROM document_versions v JOIN blobs b ON b.id=v.blob_id WHERE v.id=%s", (failed["version_id"],)).fetchone()["storage_key"]
                (Path(directory) / key).unlink()
                process_extraction(str(failed["job_id"]))
                self.assertEqual(old_version_id, next(v["id"] for v in get_document(document_id)["versions"] if v["is_current"]))

                process_extraction(str(newer["job_id"]))
                self.assertEqual(newer["version_id"], next(v["id"] for v in get_document(document_id)["versions"] if v["is_current"]))
                self.assertTrue(any(row["document_id"] == document_id for row in search_passages(f"faronewer{token}")))
                self.assertFalse(any(row["document_id"] == document_id for row in search_passages(f"faroold{token}")))

                process_extraction(str(older["job_id"]))
                self.assertEqual(newer["version_id"], next(v["id"] for v in get_document(document_id)["versions"] if v["is_current"]))
            finally:
                with connection() as db:
                    blob_ids = [row["blob_id"] for row in db.execute("SELECT blob_id FROM document_versions WHERE document_id=%s", (document_id,)).fetchall()]
                    db.execute("DELETE FROM chunks WHERE version_id IN (SELECT id FROM document_versions WHERE document_id=%s)", (document_id,))
                    db.execute("DELETE FROM processing_jobs WHERE version_id IN (SELECT id FROM document_versions WHERE document_id=%s)", (document_id,))
                    db.execute("DELETE FROM document_versions WHERE document_id=%s", (document_id,))
                    db.execute("DELETE FROM blobs WHERE id=ANY(%s)", (blob_ids,))
                    db.execute("DELETE FROM documents WHERE id=%s", (document_id,))
                if previous_root is None:
                    os.environ.pop("FARODOCS_STORAGE_ROOT", None)
                else:
                    os.environ["FARODOCS_STORAGE_ROOT"] = previous_root


if __name__ == "__main__":
    unittest.main()
