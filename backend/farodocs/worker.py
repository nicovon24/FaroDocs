"""Celery entry point for retryable document jobs."""

import os

from celery import Celery

celery_app = Celery(
    "farodocs",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
)
