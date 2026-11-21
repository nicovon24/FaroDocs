"""HTTP checks against a running local Compose stack, using synthetic files only."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import uuid

from generate_extraction_fixtures import generate
from farodocs.uploads import MAX_UPLOAD_BYTES
from reportlab.pdfgen import canvas


BASE_URL = os.environ.get("FARODOCS_TEST_API_URL")


def request(method: str, path: str, *, body: bytes | None = None, content_type: str | None = None):
    headers = {"Content-Type": content_type} if content_type else {}
    call = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        response = urlopen(call, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        content = response.read()
        kind = response.headers.get("Content-Type", "")
        return response.status, json.loads(content) if "application/json" in kind else content


def upload(path: str, filename: str, data: bytes):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
            "Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    return request("POST", path, body=body, content_type=f"multipart/form-data; boundary={boundary}")


@unittest.skipUnless(BASE_URL, "Set FARODOCS_TEST_API_URL for the running-stack HTTP test")
class LibraryApiTest(unittest.TestCase):
    def wait_version(self, document_id: str, state: str):
        for _ in range(40):
            _, detail = request("GET", f"/documents/{document_id}")
            if detail["versions"][0]["status"] == state:
                return detail["versions"][0]
            time.sleep(0.5)
        self.fail(f"Version did not reach {state}: {detail}")

    def test_supported_uploads_and_rejections(self):
        created = []
        try:
            with TemporaryDirectory() as directory:
                root = Path(directory)
                generate(root)
                for extension in ("pdf", "docx", "txt", "md"):
                    with self.subTest(extension=extension):
                        filename = f"sample.{extension}"
                        content = (root / filename).read_bytes()
                        status, result = upload("/documents", filename, content)
                        self.assertEqual(201, status, result)
                        created.append(result["id"])
                        self.assertIn(result["status"], ("queued", "failed"))
                        status, original = request("GET", f"/documents/{result['id']}/versions/{result['version_id']}/original")
                        self.assertEqual(200, status)
                        self.assertEqual(content, original)
                        self.assertEqual("ready", self.wait_version(result["id"], "ready")["status"])

                for filename, content in (
                    ("too-large.txt", b"x" * (MAX_UPLOAD_BYTES + 1)),
                    ("mismatch.pdf", b"plain text"),
                    ("broken.pdf", b"%PDF-not-a-document"),
                    ("broken.docx", b"PK\x03\x04bad"),
                    ("binary.md", b"\xff"),
                ):
                    with self.subTest(filename=filename):
                        status, result = upload("/documents", filename, content)
                        self.assertEqual(422, status, result)
                        self.assertTrue(result["detail"])
        finally:
            for document_id in created:
                request("DELETE", f"/documents/{document_id}")

    def test_failed_extraction_can_be_retried(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "empty.pdf"
            pdf = canvas.Canvas(str(path))
            pdf.showPage()
            pdf.save()
            status, result = upload("/documents", path.name, path.read_bytes())
            self.assertEqual(201, status, result)
            try:
                failed = self.wait_version(result["id"], "failed")
                self.assertIn("No text", failed["error_message"])
                self.assertEqual(result["job_id"], failed["job_id"])
                _, first_job = request("GET", f"/jobs/{result['job_id']}")
                self.assertEqual(1, first_job["attempt"])
                status, retried = request("POST", f"/jobs/{result['job_id']}/retry", body=b"")
                self.assertEqual(202, status, retried)
                for _ in range(40):
                    _, second_job = request("GET", f"/jobs/{result['job_id']}")
                    if second_job["attempt"] == 2 and second_job["status"] == "failed":
                        break
                    time.sleep(0.5)
                self.assertEqual(2, second_job["attempt"])
                self.assertEqual("failed", second_job["status"])
                self.assertEqual("failed", self.wait_version(result["id"], "failed")["status"])
            finally:
                request("DELETE", f"/documents/{result['id']}")

    def test_deletion_hides_document_immediately(self):
        status, result = upload("/documents", "delete-test.txt", b"Synthetic deletion passage.\n")
        self.assertEqual(201, status, result)
        self.wait_version(result["id"], "ready")
        status, deleted = request("DELETE", f"/documents/{result['id']}")
        self.assertEqual(202, status, deleted)
        for path in (
            f"/documents/{result['id']}",
            f"/documents/{result['id']}/versions/{result['version_id']}/passages",
            f"/documents/{result['id']}/versions/{result['version_id']}/original",
        ):
            self.assertEqual(404, request("GET", path)[0])
        _, documents = request("GET", "/documents")
        self.assertNotIn(result["id"], [document["id"] for document in documents])
        for _ in range(40):
            _, job = request("GET", f"/jobs/{deleted['job_id']}")
            if job["status"] in ("ready", "failed"):
                break
            time.sleep(0.5)
        self.assertEqual("ready", job["status"], job)


if __name__ == "__main__":
    unittest.main()
