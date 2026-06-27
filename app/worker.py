"""
Celery worker configuration.
Run with: celery -A app.tasks worker --loglevel=info --pool=solo
"""

from celery import Celery
import os
from dotenv import load_dotenv

from celery.schedules import crontab

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "perfume_platform",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_expires=3600,
    task_always_eager=False,
    result_backend_transport_options={},
    task_reject_on_worker_lost=False,
    beat_schedule={
        "daily-refresh-scan": {
            "task": "scan_and_refresh_due_analyses",
            "schedule": crontab(hour=2, minute=0),
        }
    },
    timezone="UTC"
)