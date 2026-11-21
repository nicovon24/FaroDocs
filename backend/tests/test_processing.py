"""Database-backed extraction checks for a migrated local or CI database."""

import os
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import uuid

from farodocs.library import WORKSPACE_ID, connection, ensure_owner, process_cleanup, process_extraction
from farodocs.uploads import store_original


@unittest.skipUnless(os.environ.get("DATABASE_URL"), "Set DATABASE_URL for database-backed processing checks")
class ProcessingTest(unittest.TestCase):
    def test_cleanup_failure_is_retryable_and_removes_local_data(self):
        document_id, version_id, blob_id, job_id = (uuid.uuid4() for _ in range(4))
        content = b"Synthetic cleanup passage."
        previous_root = os.environ.get("FARODOCS_STORAGE_ROOT")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            os.environ["FARODOCS_STORAGE_ROOT"] = directory
            key, digest = store_original(content, root)
            try:
                with connection() as db:
                    ensure_owner(db)
                    db.execute("INSERT INTO documents (id,workspace_id,title,is_deleted,deleted_at) VALUES (%s,%s,'Synthetic cleanup test',true,now())", (document_id, WORKSPACE_ID))
                    db.execute("INSERT INTO blobs (id,storage_key,sha256,size_bytes,media_type) VALUES (%s,%s,%s,%s,'text/plain')", (blob_id, key, digest, len(content)))
                    db.execute("INSERT INTO document_versions (id,document_id,version_number,blob_id,filename,status) VALUES (%s,%s,1,%s,'cleanup.txt','ready')", (version_id, document_id, blob_id))
                    db.execute("INSERT INTO processing_jobs (id,version_id,kind) VALUES (%s,%s,'delete')", (job_id, version_id))
                    db.execute("INSERT INTO chunks (id,version_id,extraction_recipe,ordinal,text_content,text_sha256,locator) VALUES (%s,%s,'blocks-v1',0,%s,%s,%s)", (uuid.uuid4().hex, version_id, content.decode(), sha256(content).hexdigest(), '{"kind":"text","start":0,"end":26}'))

                with patch.object(Path, "unlink", side_effect=OSError("Synthetic storage failure")):
                    process_cleanup(str(job_id))
                with connection() as db:
                    failed = db.execute("SELECT status,attempt,error_message FROM processing_jobs WHERE id=%s", (job_id,)).fetchone()
                self.assertEqual(("failed", 1), (failed["status"], failed["attempt"]))
                self.assertIn("Synthetic storage failure", failed["error_message"])
                self.assertTrue((root / key).exists())

                process_cleanup(str(job_id))
                with connection() as db:
                    ready = db.execute("SELECT status,attempt FROM processing_jobs WHERE id=%s", (job_id,)).fetchone()
                    version = db.execute("SELECT blob_id FROM document_versions WHERE id=%s", (version_id,)).fetchone()
                    chunks = db.execute("SELECT count(*) AS n FROM chunks WHERE version_id=%s", (version_id,)).fetchone()["n"]
                    blobs = db.execute("SELECT count(*) AS n FROM blobs WHERE id=%s", (blob_id,)).fetchone()["n"]
                self.assertEqual(("ready", 2), (ready["status"], ready["attempt"]))
                self.assertIsNone(version["blob_id"])
                self.assertEqual((0, 0), (chunks, blobs))
                self.assertFalse((root / key).exists())
            finally:
                with connection() as db:
                    db.execute("DELETE FROM chunks WHERE version_id=%s", (version_id,))
                    db.execute("DELETE FROM processing_jobs WHERE version_id=%s", (version_id,))
                    db.execute("DELETE FROM document_versions WHERE id=%s", (version_id,))
                    db.execute("DELETE FROM blobs WHERE id=%s", (blob_id,))
                    db.execute("DELETE FROM documents WHERE id=%s", (document_id,))
                if previous_root is None:
                    os.environ.pop("FARODOCS_STORAGE_ROOT", None)
                else:
                    os.environ["FARODOCS_STORAGE_ROOT"] = previous_root

    def test_failed_job_retry_and_stable_passage_ids(self):
        document_id, version_id, blob_id, job_id = (uuid.uuid4() for _ in range(4))
        text = b"Synthetic first paragraph.\n\nSynthetic second paragraph.\n"
        previous_root = os.environ.get("FARODOCS_STORAGE_ROOT")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            os.environ["FARODOCS_STORAGE_ROOT"] = directory
            key, digest = store_original(text, root)
            path = root / key
            try:
                with connection() as db:
                    ensure_owner(db)
                    db.execute("INSERT INTO documents (id,workspace_id,title) VALUES (%s,%s,'Synthetic processing test')", (document_id, WORKSPACE_ID))
                    db.execute("INSERT INTO blobs (id,storage_key,sha256,size_bytes,media_type) VALUES (%s,%s,%s,%s,'text/plain')", (blob_id, key, digest, len(text)))
                    db.execute("INSERT INTO document_versions (id,document_id,version_number,blob_id,filename) VALUES (%s,%s,1,%s,'test.txt')", (version_id, document_id, blob_id))
                    db.execute("INSERT INTO processing_jobs (id,version_id,kind) VALUES (%s,%s,'extract')", (job_id, version_id))

                path.rename(root / "temporarily-missing")
                process_extraction(str(job_id))
                with connection() as db:
                    failed = db.execute("SELECT status,attempt,error_message FROM processing_jobs WHERE id=%s", (job_id,)).fetchone()
                self.assertEqual(("failed", 1), (failed["status"], failed["attempt"]))
                self.assertIn("No such file", failed["error_message"])

                (root / "temporarily-missing").rename(path)
                process_extraction(str(job_id))
                with connection() as db:
                    ready = db.execute("SELECT status,attempt FROM processing_jobs WHERE id=%s", (job_id,)).fetchone()
                    version = db.execute("SELECT status,extraction_recipe FROM document_versions WHERE id=%s", (version_id,)).fetchone()
                    first = db.execute("SELECT id,locator FROM chunks WHERE version_id=%s ORDER BY ordinal", (version_id,)).fetchall()
                self.assertEqual(("ready", 2), (ready["status"], ready["attempt"]))
                self.assertEqual(("ready", "blocks-v1"), (version["status"], version["extraction_recipe"]))
                self.assertEqual(2, len(first))
                self.assertEqual("text", first[0]["locator"]["kind"])

                with connection() as db:
                    db.execute("UPDATE processing_jobs SET status='failed' WHERE id=%s", (job_id,))
                    db.execute("UPDATE document_versions SET status='failed',error_code='test',error_message='Synthetic retry' WHERE id=%s", (version_id,))
                process_extraction(str(job_id))
                with connection() as db:
                    second = db.execute("SELECT id,locator FROM chunks WHERE version_id=%s ORDER BY ordinal", (version_id,)).fetchall()
                self.assertEqual(first, second)
            finally:
                with connection() as db:
                    db.execute("DELETE FROM chunks WHERE version_id=%s", (version_id,))
                    db.execute("DELETE FROM processing_jobs WHERE version_id=%s", (version_id,))
                    db.execute("DELETE FROM document_versions WHERE id=%s", (version_id,))
                    db.execute("DELETE FROM blobs WHERE id=%s", (blob_id,))
                    db.execute("DELETE FROM documents WHERE id=%s", (document_id,))
                if previous_root is None:
                    os.environ.pop("FARODOCS_STORAGE_ROOT", None)
                else:
                    os.environ["FARODOCS_STORAGE_ROOT"] = previous_root


if __name__ == "__main__":
    unittest.main()
