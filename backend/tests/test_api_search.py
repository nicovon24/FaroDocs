"""Synthetic HTTP checks for current, visible passage search."""

import os
import time
import unittest
from urllib.parse import quote

from test_api_library import request, upload


@unittest.skipUnless(os.environ.get("FARODOCS_TEST_API_URL"), "Set FARODOCS_TEST_API_URL")
class SearchApiTest(unittest.TestCase):
    def wait_ready(self, document_id):
        for _ in range(40):
            _, detail = request("GET", f"/documents/{document_id}")
            if detail["versions"][0]["status"] == "ready":
                return
            time.sleep(0.5)
        self.fail("Synthetic version did not become ready")

    def test_current_visible_passages_and_query_bounds(self):
        token = "farosearchuniquetoken"
        status, first = upload("/documents", "search.txt", f"{token} original passage.\n".encode())
        self.assertEqual(201, status)
        document_id = first["id"]
        try:
            self.wait_ready(document_id)
            status, rows = request("GET", f"/search?q={quote(token)}")
            self.assertEqual(200, status)
            own = next(row for row in rows if row["document_id"] == document_id)
            self.assertTrue(own["passage_id"])
            self.assertIn(f"«{token}»", own["text_content"])
            self.assertEqual((200, []), request("GET", "/search?q=missingfarosearchtoken"))
            self.assertEqual(422, request("GET", "/search?q=%20%20")[0])
            self.assertEqual(422, request("GET", "/search?q=" + "x" * 201)[0])

            status, replacement = upload(f"/documents/{document_id}/versions", "replacement.txt", b"New unrelated replacement passage.\n")
            self.assertEqual(201, status)
            self.wait_ready(document_id)
            _, rows = request("GET", f"/search?q={quote(token)}")
            self.assertFalse(any(row["document_id"] == document_id for row in rows))
        finally:
            request("DELETE", f"/documents/{document_id}")
        _, rows = request("GET", "/search?q=replacement")
        self.assertFalse(any(row["document_id"] == document_id for row in rows))


if __name__ == "__main__":
    unittest.main()
