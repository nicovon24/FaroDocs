"""Executable synthetic locator spike, independent of database and external AI."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from farodocs.extraction import extract_blocks
from generate_extraction_fixtures import generate


class ExtractionSpikeTest(unittest.TestCase):
    def test_all_four_formats_retain_inspectable_location(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generate(root)
            for extension in ("txt", "md", "docx", "pdf"):
                with self.subTest(extension=extension):
                    filename = f"sample.{extension}"
                    blocks = extract_blocks(filename, (root / filename).read_bytes())
                    self.assertTrue(any("2026-12-01" in block.text for block in blocks))
                    self.assertTrue(all(block.locator for block in blocks))
                    if extension == "pdf":
                        self.assertEqual(2, next(block.locator["page"] for block in blocks if "2026-12-01" in block.text))
                    elif extension in ("txt", "md"):
                        block = next(block for block in blocks if "2026-12-01" in block.text)
                        decoded = (root / filename).read_bytes().decode("utf-8")
                        self.assertEqual(block.text, decoded[block.locator["start"]:block.locator["end"]])
                    else:
                        self.assertTrue(any(block.locator.get("kind") == "docx_cell" for block in blocks))


if __name__ == "__main__":
    unittest.main()
