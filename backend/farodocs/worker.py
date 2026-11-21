"""Celery entry point for retryable document jobs."""

import os

from celery import Celery

celery_app = Celery(
    "farodocs",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
)


@celery_app.task(name="farodocs.extract_document")
def extract_document(job_id: str) -> None:
    from farodocs.library import process_extraction

    process_extraction(job_id)


@celery_app.task(name="farodocs.cleanup_document")
def cleanup_document(job_id: str) -> None:
    from farodocs.library import process_cleanup

    process_cleanup(job_id)
