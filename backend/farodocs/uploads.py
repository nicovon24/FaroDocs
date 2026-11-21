"""Bounded local upload validation and private original storage."""

from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import uuid
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader


MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOCX_EXPANDED_BYTES = 32 * 1024 * 1024
MAX_DOCX_ENTRIES = 2048
SUPPORTED = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".txt": "text/plain", ".md": "text/markdown"}


class InvalidUpload(ValueError):
    """A file cannot be admitted to the local library."""


def validate_upload(filename: str, data: bytes) -> tuple[str, str]:
    if not filename or Path(filename.replace("\\", "/")).name != filename:
        raise InvalidUpload("Filename must not contain a path")
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED:
        raise InvalidUpload("Supported formats: PDF, DOCX, TXT, Markdown")
    if not data:
        raise InvalidUpload("File is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidUpload(f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB limit")
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise InvalidUpload("File content does not match PDF extension")
        try:
            reader = PdfReader(BytesIO(data), strict=True)
            if not reader.pages:
                raise InvalidUpload("PDF has no pages")
            if len(reader.pages) > 100:
                raise InvalidUpload("PDF exceeds 100 pages")
        except Exception as exc:
            if isinstance(exc, InvalidUpload):
                raise
            raise InvalidUpload("Malformed PDF") from exc
    elif suffix == ".docx":
        if not data.startswith(b"PK"):
            raise InvalidUpload("File content does not match DOCX extension")
        try:
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > MAX_DOCX_ENTRIES or sum(entry.file_size for entry in entries) > MAX_DOCX_EXPANDED_BYTES:
                    raise InvalidUpload("DOCX expands beyond the processing limit")
                if "word/document.xml" not in archive.namelist() or archive.testzip() is not None:
                    raise InvalidUpload("Malformed DOCX")
        except (BadZipFile, OSError) as exc:
            raise InvalidUpload("Malformed DOCX") from exc
    else:
        if b"\x00" in data:
            raise InvalidUpload("Text file contains binary content")
        try:
            data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InvalidUpload("Text file must be UTF-8") from exc
        if data.startswith((b"%PDF-", b"PK\x03\x04")):
            raise InvalidUpload("File content does not match text extension")
    return suffix, SUPPORTED[suffix]


def store_original(data: bytes, root: Path) -> tuple[str, str]:
    """Use an opaque key; callers remove it if database commit fails."""
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = uuid.uuid4().hex
    path = root / key
    with path.open("xb") as output:
        output.write(data)
    if os.name != "nt":
        path.chmod(0o600)
    return key, sha256(data).hexdigest()
