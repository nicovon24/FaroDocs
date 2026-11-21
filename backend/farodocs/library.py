"""Local-owner library operations and idempotent background work."""

from hashlib import sha256
import json
import os
from pathlib import Path
import uuid

import psycopg
from psycopg.rows import dict_row

from farodocs.extraction import extract_blocks


OWNER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
WORKSPACE_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
RECIPE = "blocks-v1"


def connection() -> psycopg.Connection:
    url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
    return psycopg.connect(url, row_factory=dict_row)


def storage_root() -> Path:
    return Path(os.environ.get("FARODOCS_STORAGE_ROOT", "/app/private-files"))


def ensure_owner(db: psycopg.Connection) -> None:
    db.execute("INSERT INTO app_users (id, display_name) VALUES (%s, 'Local developer') ON CONFLICT DO NOTHING", (OWNER_ID,))
    db.execute("INSERT INTO workspaces (id, owner_id, name) VALUES (%s, %s, 'Personal') ON CONFLICT DO NOTHING", (WORKSPACE_ID, OWNER_ID))


def dispatch(job_id: uuid.UUID, kind: str) -> None:
    from farodocs.worker import cleanup_document, extract_document

    task = cleanup_document if kind == "delete" else extract_document
    task.delay(str(job_id))


def passage_id(version_id: uuid.UUID, ordinal: int, content: str) -> str:
    return sha256(f"{version_id}:{RECIPE}:{ordinal}:{sha256(content.encode()).hexdigest()}".encode()).hexdigest()


def process_extraction(job_id: str) -> None:
    with connection() as db:
        row = db.execute(
            "UPDATE processing_jobs SET status='processing', attempt=attempt+1, error_message=NULL, updated_at=now() "
            "WHERE id=%s AND kind='extract' AND status IN ('queued','failed') "
            "AND EXISTS (SELECT 1 FROM document_versions v JOIN documents d ON d.id=v.document_id "
            "WHERE v.id=processing_jobs.version_id AND NOT d.is_deleted) "
            "RETURNING version_id", (job_id,),
        ).fetchone()
        if row is None:
            return
        version_id = row["version_id"]
        version = db.execute(
            "SELECT v.filename, b.storage_key FROM document_versions v JOIN blobs b ON b.id=v.blob_id WHERE v.id=%s",
            (version_id,),
        ).fetchone()
        db.execute("UPDATE document_versions SET status='processing', error_code=NULL, error_message=NULL WHERE id=%s", (version_id,))
    try:
        if version is None:
            raise ValueError("Original file is unavailable")
        data = (storage_root() / version["storage_key"]).read_bytes()
        blocks = extract_blocks(version["filename"], data)
        if not blocks:
            raise ValueError("No text was found; scanned files need the later OCR stage")
        with connection() as db:
            visible = db.execute(
                "SELECT NOT d.is_deleted AS visible FROM document_versions v JOIN documents d ON d.id=v.document_id "
                "WHERE v.id=%s FOR UPDATE OF d", (version_id,),
            ).fetchone()
            if not visible or not visible["visible"]:
                db.execute("UPDATE processing_jobs SET status='failed', error_message='Document deleted', updated_at=now() WHERE id=%s", (job_id,))
                return
            db.execute("DELETE FROM chunks WHERE version_id=%s", (version_id,))
            for ordinal, block in enumerate(blocks):
                db.execute(
                    "INSERT INTO chunks (id, version_id, extraction_recipe, ordinal, text_content, text_sha256, locator) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (passage_id(version_id, ordinal, block.text), version_id, RECIPE, ordinal, block.text,
                     sha256(block.text.encode()).hexdigest(), json.dumps(block.locator)),
                )
            db.execute("UPDATE document_versions SET status='ready', extraction_recipe=%s, error_code=NULL, error_message=NULL WHERE id=%s", (RECIPE, version_id))
            db.execute("UPDATE processing_jobs SET status='ready', updated_at=now() WHERE id=%s", (job_id,))
    except Exception as exc:
        message = str(exc)[:500] or "Extraction failed"
        with connection() as db:
            visible = db.execute(
                "SELECT NOT d.is_deleted AS visible FROM document_versions v JOIN documents d ON d.id=v.document_id "
                "WHERE v.id=%s FOR UPDATE OF d", (version_id,),
            ).fetchone()
            if visible and visible["visible"]:
                db.execute("UPDATE document_versions SET status='failed', error_code='extraction_failed', error_message=%s WHERE id=%s", (message, version_id))
            db.execute("UPDATE processing_jobs SET status='failed', error_message=%s, updated_at=now() WHERE id=%s", (message, job_id))


def process_cleanup(job_id: str) -> None:
    with connection() as db:
        row = db.execute(
            "UPDATE processing_jobs SET status='processing', attempt=attempt+1, error_message=NULL, updated_at=now() "
            "WHERE id=%s AND kind='delete' AND status IN ('queued','failed') RETURNING version_id", (job_id,),
        ).fetchone()
        if row is None:
            return
        document = db.execute("SELECT document_id FROM document_versions WHERE id=%s", (row["version_id"],)).fetchone()
        document_id = document["document_id"]
    try:
        with connection() as db:
            blobs = db.execute(
                "SELECT b.id, b.storage_key FROM blobs b JOIN document_versions v ON v.blob_id=b.id WHERE v.document_id=%s",
                (document_id,),
            ).fetchall()
        for blob in blobs:
            (storage_root() / blob["storage_key"]).unlink(missing_ok=True)
        with connection() as db:
            db.execute("SELECT id FROM documents WHERE id=%s FOR UPDATE", (document_id,))
            db.execute("DELETE FROM chunks WHERE version_id IN (SELECT id FROM document_versions WHERE document_id=%s)", (document_id,))
            db.execute("UPDATE document_versions SET blob_id=NULL, status='failed', error_code='deleted', error_message='Document deleted' WHERE document_id=%s", (document_id,))
            db.execute("DELETE FROM blobs WHERE id=ANY(%s)", ([blob["id"] for blob in blobs],))
            db.execute("DELETE FROM document_tags WHERE document_id=%s", (document_id,))
            db.execute("DELETE FROM favorites WHERE document_id=%s", (document_id,))
            db.execute("UPDATE processing_jobs SET status='ready', updated_at=now() WHERE id=%s", (job_id,))
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE processing_jobs SET status='failed', error_message=%s, updated_at=now() WHERE id=%s", (str(exc)[:500], job_id))
