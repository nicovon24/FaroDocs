"""HTTP API for the single-owner local library."""

import uuid

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from farodocs.library import OWNER_ID, WORKSPACE_ID, connection, dispatch, ensure_owner, storage_root
from farodocs.search import search_passages
from farodocs.conversations import router as conversation_router
from farodocs.uploads import InvalidUpload, MAX_UPLOAD_BYTES, store_original, validate_upload

app = FastAPI(title="FaroDocs API", version="0.1.0")
app.include_router(conversation_router)


@app.get("/search")
def search(q: str = Query(min_length=1, max_length=200)) -> list[dict]:
    if not q.strip():
        raise HTTPException(422, "Search query must not be empty")
    return search_passages(q.strip())


def _document(db, document_id):
    row = db.execute("SELECT id, title, folder_id, is_deleted FROM documents WHERE id=%s AND workspace_id=%s", (document_id, WORKSPACE_ID)).fetchone()
    if row is None or row["is_deleted"]:
        raise HTTPException(404, "Document not found")
    return row


async def _upload(file: UploadFile, document_id: uuid.UUID | None = None):
    replacing = document_id is not None
    filename = file.filename or ""
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    try:
        _, media_type = validate_upload(filename, data)
    except InvalidUpload as exc:
        raise HTTPException(422, str(exc)) from exc
    root = storage_root()
    key, digest = store_original(data, root)
    blob_id, version_id, job_id = (uuid.uuid4() for _ in range(3))
    document_id = document_id or uuid.uuid4()
    try:
        with connection() as db:
            ensure_owner(db)
            if replacing:
                existing = db.execute(
                    "SELECT id FROM documents WHERE id=%s AND workspace_id=%s AND NOT is_deleted FOR UPDATE",
                    (document_id, WORKSPACE_ID),
                ).fetchone()
                if existing is None:
                    raise HTTPException(404, "Document not found")
            prior = db.execute("SELECT coalesce(max(version_number),0) AS n FROM document_versions WHERE document_id=%s", (document_id,)).fetchone()
            if not replacing:
                db.execute("INSERT INTO documents (id, workspace_id, title) VALUES (%s,%s,%s)", (document_id, WORKSPACE_ID, filename))
            db.execute("INSERT INTO blobs (id, storage_key, sha256, size_bytes, media_type) VALUES (%s,%s,%s,%s,%s)", (blob_id, key, digest, len(data), media_type))
            db.execute("INSERT INTO document_versions (id, document_id, version_number, blob_id, filename, is_current) VALUES (%s,%s,%s,%s,%s,%s)", (version_id, document_id, prior["n"] + 1, blob_id, filename, not replacing))
            db.execute("INSERT INTO processing_jobs (id, version_id, kind) VALUES (%s,%s,'extract')", (job_id, version_id))
    except Exception:
        (root / key).unlink(missing_ok=True)
        raise
    queue_failed = False
    try:
        dispatch(job_id, "extract")
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE processing_jobs SET status='failed', error_message=%s WHERE id=%s", (f"Queue unavailable: {exc}"[:500], job_id))
            db.execute("UPDATE document_versions SET status='failed', error_code='queue_unavailable', error_message='Processing queue unavailable; retry the job' WHERE id=%s", (version_id,))
        queue_failed = True
    return {"id": document_id, "version_id": version_id, "job_id": job_id, "filename": filename, "status": "failed" if queue_failed else "queued"}


@app.get("/documents")
def list_documents(folder: uuid.UUID | None = None, tag: uuid.UUID | None = None, favorite: bool | None = None, q: str = "") -> list[dict]:
    with connection() as db:
        return db.execute(
            "SELECT d.id,d.title,d.folder_id,d.created_at,v.id AS version_id,v.filename,v.version_number,v.status,v.error_message,"
            "EXISTS(SELECT 1 FROM favorites f WHERE f.document_id=d.id AND f.user_id=%s) AS favorite,"
            "coalesce((SELECT json_agg(json_build_object('id',t.id,'name',t.name) ORDER BY t.name) FROM document_tags dt JOIN tags t ON t.id=dt.tag_id WHERE dt.document_id=d.id),'[]'::json) AS tags "
            "FROM documents d JOIN document_versions v ON v.document_id=d.id AND v.is_current "
            "WHERE d.workspace_id=%s AND NOT d.is_deleted AND (%s::uuid IS NULL OR d.folder_id=%s) "
            "AND (%s::uuid IS NULL OR EXISTS(SELECT 1 FROM document_tags dt WHERE dt.document_id=d.id AND dt.tag_id=%s)) "
            "AND (%s::boolean IS NULL OR EXISTS(SELECT 1 FROM favorites f WHERE f.document_id=d.id AND f.user_id=%s)=%s) "
            "AND (%s='' OR d.title ILIKE '%%' || %s || '%%') ORDER BY d.created_at DESC",
            (OWNER_ID, WORKSPACE_ID, folder, folder, tag, tag, favorite, OWNER_ID, favorite, q, q),
        ).fetchall()


@app.post("/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)) -> dict:
    return await _upload(file)


@app.post("/documents/{document_id}/versions", status_code=201)
async def upload_version(document_id: uuid.UUID, file: UploadFile = File(...)) -> dict:
    with connection() as db:
        _document(db, document_id)
    return await _upload(file, document_id)


@app.get("/documents/{document_id}")
def get_document(document_id: uuid.UUID) -> dict:
    with connection() as db:
        document = _document(db, document_id)
        versions = db.execute(
            "SELECT v.id,v.version_number,v.filename,v.status,v.error_message,v.extraction_recipe,v.is_current,v.created_at,"
            "(SELECT j.id FROM processing_jobs j WHERE j.version_id=v.id AND j.kind='extract' ORDER BY j.created_at DESC LIMIT 1) AS job_id,"
            "EXISTS(SELECT 1 FROM processing_jobs j WHERE j.version_id=v.id AND j.kind='extract' "
            "AND (j.status='failed' OR (j.status='queued' AND j.updated_at < now() - interval '1 minute'))) AS can_retry "
            "FROM document_versions v WHERE v.document_id=%s ORDER BY v.version_number DESC",
            (document_id,),
        ).fetchall()
    return {**document, "versions": versions}


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    folder_id: uuid.UUID | None = None
    favorite: bool | None = None
    tag_ids: list[uuid.UUID] | None = None


@app.patch("/documents/{document_id}")
def update_document(document_id: uuid.UUID, update: DocumentUpdate) -> dict:
    with connection() as db:
        _document(db, document_id)
        fields = update.model_fields_set
        if "title" in fields:
            if not update.title or not update.title.strip():
                raise HTTPException(422, "Title must not be empty")
            db.execute("UPDATE documents SET title=%s WHERE id=%s", (update.title.strip(), document_id))
        if "folder_id" in fields:
            if update.folder_id and not db.execute("SELECT 1 FROM folders WHERE id=%s AND workspace_id=%s", (update.folder_id, WORKSPACE_ID)).fetchone():
                raise HTTPException(404, "Folder not found")
            db.execute("UPDATE documents SET folder_id=%s WHERE id=%s", (update.folder_id, document_id))
        if "favorite" in fields:
            if update.favorite:
                db.execute("INSERT INTO favorites (user_id,document_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (OWNER_ID, document_id))
            else:
                db.execute("DELETE FROM favorites WHERE user_id=%s AND document_id=%s", (OWNER_ID, document_id))
        if "tag_ids" in fields:
            ids = list(dict.fromkeys(update.tag_ids or []))
            if ids and db.execute("SELECT count(*) AS n FROM tags WHERE id=ANY(%s) AND workspace_id=%s", (ids, WORKSPACE_ID)).fetchone()["n"] != len(ids):
                raise HTTPException(404, "Tag not found")
            db.execute("DELETE FROM document_tags WHERE document_id=%s", (document_id,))
            for tag_id in ids:
                db.execute("INSERT INTO document_tags (workspace_id,document_id,tag_id) VALUES (%s,%s,%s)", (WORKSPACE_ID, document_id, tag_id))
    return {"id": document_id, "updated": True}


@app.get("/documents/{document_id}/versions/{version_id}/passages")
def list_passages(document_id: uuid.UUID, version_id: uuid.UUID) -> list[dict]:
    with connection() as db:
        _document(db, document_id)
        if not db.execute("SELECT 1 FROM document_versions WHERE id=%s AND document_id=%s", (version_id, document_id)).fetchone():
            raise HTTPException(404, "Version not found")
        return db.execute("SELECT id,ordinal,text_content,locator FROM chunks WHERE version_id=%s ORDER BY ordinal", (version_id,)).fetchall()


@app.get("/documents/{document_id}/versions/{version_id}/original")
def get_original(document_id: uuid.UUID, version_id: uuid.UUID):
    with connection() as db:
        _document(db, document_id)
        row = db.execute("SELECT v.filename,b.storage_key,b.media_type FROM document_versions v JOIN blobs b ON b.id=v.blob_id WHERE v.id=%s AND v.document_id=%s", (version_id, document_id)).fetchone()
    if not row:
        raise HTTPException(404, "Original not found")
    path = storage_root() / row["storage_key"]
    if not path.is_file():
        raise HTTPException(404, "Original file missing")
    return FileResponse(path, media_type=row["media_type"], filename=row["filename"], content_disposition_type="inline")


class NamedItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)


@app.get("/folders")
def list_folders() -> list[dict]:
    with connection() as db:
        return db.execute("SELECT id,name FROM folders WHERE workspace_id=%s ORDER BY name", (WORKSPACE_ID,)).fetchall()


@app.post("/folders", status_code=201)
def create_folder(item: NamedItem) -> dict:
    name = item.name.strip()
    if not name:
        raise HTTPException(422, "Folder name must not be empty")
    item_id = uuid.uuid4()
    with connection() as db:
        ensure_owner(db)
        db.execute("INSERT INTO folders (id,workspace_id,name) VALUES (%s,%s,%s)", (item_id, WORKSPACE_ID, name))
    return {"id": item_id, "name": name}


@app.get("/tags")
def list_tags() -> list[dict]:
    with connection() as db:
        return db.execute("SELECT id,name FROM tags WHERE workspace_id=%s ORDER BY name", (WORKSPACE_ID,)).fetchall()


@app.post("/tags", status_code=201)
def create_tag(item: NamedItem) -> dict:
    name = item.name.strip()
    if not name:
        raise HTTPException(422, "Tag name must not be empty")
    with connection() as db:
        ensure_owner(db)
        return db.execute("INSERT INTO tags (id,workspace_id,name) VALUES (%s,%s,%s) ON CONFLICT (workspace_id,name) DO UPDATE SET name=excluded.name RETURNING id,name", (uuid.uuid4(), WORKSPACE_ID, name)).fetchone()


@app.delete("/documents/{document_id}", status_code=202)
def delete_document(document_id: uuid.UUID) -> dict:
    job_id = uuid.uuid4()
    with connection() as db:
        locked = db.execute(
            "SELECT id FROM documents WHERE id=%s AND workspace_id=%s AND NOT is_deleted FOR UPDATE",
            (document_id, WORKSPACE_ID),
        ).fetchone()
        if locked is None:
            raise HTTPException(404, "Document not found")
        db.execute(
            "DELETE FROM conversations WHERE id IN ("
            "SELECT DISTINCT m.conversation_id FROM conversation_citations cc "
            "JOIN conversation_messages m ON m.id=cc.message_id "
            "JOIN chunks c ON c.id=cc.passage_id "
            "JOIN document_versions v ON v.id=c.version_id "
            "WHERE v.document_id=%s)", (document_id,),
        )
        version = db.execute("SELECT id FROM document_versions WHERE document_id=%s AND is_current", (document_id,)).fetchone()
        db.execute("UPDATE documents SET is_deleted=true,deleted_at=now() WHERE id=%s", (document_id,))
        db.execute(
            "UPDATE processing_jobs SET status='failed',error_message='Document deleted',updated_at=now() "
            "WHERE kind='extract' AND status='queued' AND version_id IN "
            "(SELECT id FROM document_versions WHERE document_id=%s)", (document_id,),
        )
        db.execute("INSERT INTO processing_jobs (id,version_id,kind) VALUES (%s,%s,'delete')", (job_id, version["id"]))
    queue_failed = False
    try:
        dispatch(job_id, "delete")
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE processing_jobs SET status='failed',error_message=%s WHERE id=%s", (f"Queue unavailable: {exc}"[:500], job_id))
        queue_failed = True
    return {"job_id": job_id, "status": "failed" if queue_failed else "queued"}


@app.get("/jobs/{job_id}")
def get_job(job_id: uuid.UUID) -> dict:
    with connection() as db:
        row = db.execute("SELECT j.id,j.kind,j.status,j.attempt,j.error_message,j.updated_at FROM processing_jobs j JOIN document_versions v ON v.id=j.version_id JOIN documents d ON d.id=v.document_id WHERE j.id=%s AND d.workspace_id=%s", (job_id, WORKSPACE_ID)).fetchone()
    if not row:
        raise HTTPException(404, "Job not found")
    return row


@app.post("/jobs/{job_id}/retry", status_code=202)
def retry_job(job_id: uuid.UUID) -> dict:
    with connection() as db:
        row = db.execute("SELECT j.kind,j.status,j.version_id,j.updated_at FROM processing_jobs j JOIN document_versions v ON v.id=j.version_id JOIN documents d ON d.id=v.document_id WHERE j.id=%s AND d.workspace_id=%s AND (j.kind='delete' OR NOT d.is_deleted)", (job_id, WORKSPACE_ID)).fetchone()
        if not row:
            raise HTTPException(404, "Job not found")
        stale_queued = row["status"] == "queued" and db.execute("SELECT %s < now() - interval '1 minute' AS stale", (row["updated_at"],)).fetchone()["stale"]
        if row["status"] != "failed" and not stale_queued:
            raise HTTPException(409, "Only failed or stale queued jobs can be retried")
        db.execute("UPDATE processing_jobs SET status='queued',error_message=NULL,updated_at=now() WHERE id=%s", (job_id,))
        if row["kind"] == "extract":
            db.execute("UPDATE document_versions SET status='queued',error_code=NULL,error_message=NULL WHERE id=%s", (row["version_id"],))
    try:
        dispatch(job_id, row["kind"])
    except Exception as exc:
        with connection() as db:
            db.execute("UPDATE processing_jobs SET status='failed',error_message=%s WHERE id=%s", (f"Queue unavailable: {exc}"[:500], job_id))
            if row["kind"] == "extract":
                db.execute("UPDATE document_versions SET status='failed',error_code='queue_unavailable',error_message='Processing queue unavailable; retry the job' WHERE id=%s", (row["version_id"],))
        raise HTTPException(503, "Processing queue unavailable") from exc
    return {"id": job_id, "status": "queued"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
