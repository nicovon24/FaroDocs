"""Format adapters that retain the best source location available without OCR."""

from dataclasses import dataclass
from io import BytesIO
import re
from typing import Any

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader


MAX_PDF_PAGES = 100
MAX_PDF_PAGE_STREAM_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class TextBlock:
    text: str
    locator: dict[str, Any]


def _paragraphs(text: str, *, locator_prefix: dict[str, Any]) -> list[TextBlock]:
    blocks = []
    for match in re.finditer(r"(?:\A|\r?\n[ \t]*\r?\n)(.*?)(?=\r?\n[ \t]*\r?\n|\Z)", text, re.DOTALL):
        raw = match.group(1)
        content = raw.strip()
        if content:
            start = match.start(1) + len(raw) - len(raw.lstrip())
            blocks.append(TextBlock(content, {**locator_prefix, "start": start, "end": start + len(content)}))
    return blocks


def extract_blocks(filename: str, data: bytes) -> list[TextBlock]:
    """Extract ordered text blocks; offsets refer to decoded text, not rendered pixels."""
    suffix = filename.rsplit(".", 1)[-1].lower()
    if suffix in {"txt", "md"}:
        text = data.decode("utf-8-sig")
        return _paragraphs(text, locator_prefix={"kind": "text", "format": suffix})
    if suffix == "docx":
        document = Document(BytesIO(data))
        blocks = []
        for index, item in enumerate(document.iter_inner_content(), start=1):
            if isinstance(item, Paragraph) and item.text.strip():
                blocks.append(TextBlock(item.text.strip(), {"kind": "docx_paragraph", "block": index}))
            elif isinstance(item, Table):
                for row_number, row in enumerate(item.rows, start=1):
                    for column_number, cell in enumerate(row.cells, start=1):
                        if cell.text.strip():
                            blocks.append(TextBlock(cell.text.strip(), {"kind": "docx_cell", "block": index, "row": row_number, "column": column_number}))
        return blocks
    if suffix == "pdf":
        reader = PdfReader(BytesIO(data), strict=True)
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDF exceeds {MAX_PDF_PAGES} pages")
        blocks = []
        for page_number, page in enumerate(reader.pages, start=1):
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > MAX_PDF_PAGE_STREAM_BYTES:
                raise ValueError(f"PDF page {page_number} content stream is too large")
            blocks.extend(_paragraphs(page.extract_text() or "", locator_prefix={"kind": "pdf_page", "page": page_number}))
        return blocks
    raise ValueError("Unsupported document format")
