"""Provider adapter contract without a live key or network call."""

import json
import unittest
from unittest.mock import patch

from farodocs.groq import DEFAULT_MODEL, GROQ_ENDPOINT, generate_answer


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _):
        return json.dumps({"choices": [{"message": {"content": "Answer [1]."}}]}).encode()


class GroqAdapterTest(unittest.TestCase):
    def test_fixed_endpoint_bounded_context_and_secret_header(self):
        source = {"title": "Synthetic", "version_number": 1, "text_content": "x" * 2000}
        with patch("farodocs.groq.urlopen", return_value=FakeResponse()) as call:
            answer = generate_answer("Question?", [source], [], "synthetic-private-key", DEFAULT_MODEL)
        self.assertEqual("Answer [1].", answer)
        request = call.call_args.args[0]
        self.assertEqual(GROQ_ENDPOINT, request.full_url)
        self.assertEqual("Bearer synthetic-private-key", request.get_header("Authorization"))
        body = json.loads(request.data)
        self.assertNotIn("synthetic-private-key", request.data.decode())
        self.assertEqual(DEFAULT_MODEL, body["model"])
        self.assertNotIn("x" * 1201, body["messages"][-1]["content"])


if __name__ == "__main__":
    unittest.main()
