"""Bounded file admission checks with original synthetic files."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from farodocs.uploads import InvalidUpload, MAX_UPLOAD_BYTES, store_original, validate_upload
from generate_extraction_fixtures import generate


class UploadValidationTest(unittest.TestCase):
    def test_supported_files_and_private_storage(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate(root)
            for extension in ("pdf", "docx", "txt", "md"):
                with self.subTest(extension=extension):
                    name = f"sample.{extension}"
                    data = (root / name).read_bytes()
                    self.assertEqual(f".{extension}", validate_upload(name, data)[0])
                    key, digest = store_original(data, root / "private")
                    self.assertNotIn(name, key)
                    self.assertEqual(data, (root / "private" / key).read_bytes())
                    self.assertEqual(64, len(digest))

    def test_rejects_oversized_mismatched_malformed_and_paths(self) -> None:
        archive = BytesIO()
        with ZipFile(archive, "w", ZIP_DEFLATED) as docx:
            docx.writestr("word/document.xml", b"x" * (33 * 1024 * 1024))
        samples = (
            ("huge.txt", b"a" * (MAX_UPLOAD_BYTES + 1)),
            ("wrong.pdf", b"ordinary text"),
            ("broken.pdf", b"%PDF-not-a-real-document"),
            ("wrong.txt", b"%PDF-1.7"),
            ("bad.docx", b"PK\x03\x04junk"),
            ("expanded.docx", archive.getvalue()),
            ("bad.md", b"\xff"),
            ("../escape.txt", b"valid"),
            ("sample.exe", b"valid"),
        )
        for name, data in samples:
            with self.subTest(name=name):
                with self.assertRaises(InvalidUpload):
                    validate_upload(name, data)


if __name__ == "__main__":
    unittest.main()
