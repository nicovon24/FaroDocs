# Extraction and locator spike (2026-11-21)

## Decision

Use `pypdf==7.0.0` for text-bearing PDF, `python-docx==1.2.0` for DOCX, and Python's UTF-8 decoder for TXT and Markdown. The first extraction recipe emits ordered blocks with explicit locators. `reportlab==4.4.4` is used only by the synthetic PDF fixture generator, not by the application runtime. The application parser dependencies are pinned in `backend/pyproject.toml`.

The project uses these libraries through their public APIs; it does not incorporate their source. `pypdf` is [BSD 3-Clause](https://github.com/py-pdf/pypdf/blob/main/LICENSE) and `python-docx` is [MIT](https://github.com/python-openxml/python-docx/blob/master/LICENSE). Their official documentation describes [page text extraction](https://pypdf.readthedocs.io/en/latest/user/extract-text.html) and [ordered DOCX body content](https://python-docx.readthedocs.io/en/latest/api/document.html).

## Reproducible experiment

From the repository root with Python 3.12 and `pypdf==7.0.0`, `python-docx==1.2.0`, and `reportlab==4.4.4` installed:

```powershell
$env:PYTHONPATH='backend;backend/tests'
python -m unittest backend.tests.test_extraction -v
```

The test generates four original synthetic files in a temporary directory. Each contains a review date; the PDF has it on page 2, the DOCX also has a table, and TXT/Markdown use blank-line paragraphs. On 2026-11-21, the test passed for all four formats. The test checks that the date is extracted, every block has a locator, the PDF date points to page 2, TXT/Markdown character ranges reproduce the extracted text, and a DOCX table cell is located by body block, row, and column. This is a functional smoke test, not an accuracy evaluation.

## Locator contract and limits

| Format | Locator | What can be inspected |
| --- | --- | --- |
| PDF | 1-based page and offsets within extracted page text | The original page and text excerpt. No pixel-accurate highlight is claimed. |
| DOCX | 1-based body block; table row and column when applicable | The paragraph or table cell in the document body. Page number is not available from DOCX structure. |
| TXT / Markdown | Character start and end in UTF-8-decoded text | The precise substring; character offsets are not byte offsets. |

`pypdf` cannot OCR image-only pages. PDF reading order can differ from visual order, especially in columns and complex layouts. The current code caps PDF page count at 100 and uncompressed content stream size at 8 MiB per page, but neither bound is a complete defense against all pathological PDF structures; upload byte bounds and worker resource limits are separate upcoming work. The DOCX adapter covers top-level paragraphs and table cells; it does not yet cover nested tables, headers, footers, tracked changes, images, or text boxes. Markdown is treated as text; links and markup remain in excerpts. The current paragraph splitter uses blank lines; chunking and stable passage IDs are not implemented. These limits will be visible when real upload and processing are added.
