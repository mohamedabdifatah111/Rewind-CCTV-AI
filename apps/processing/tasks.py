import logging, threading
from django.conf import settings
from django.db import transaction
from .services.pipeline import process_video

logger = logging.getLogger(__name__)
try:
    from celery import shared_task
except ImportError:  # pragma: no cover
    shared_task = None

if shared_task:
    @shared_task(name="processing.process_video")
    def process_video_task(job_id):
        process_video(job_id)

def queue_processing(job_id):
    """Start processing after the DB transaction commits. Mode comes from PROCESSING_MODE."""
    mode = settings.PROCESSING_MODE
    def start():
        if mode == "sync":
            process_video(job_id)
        elif mode == "thread":
            threading.Thread(target=process_video, args=(job_id,), daemon=True).start()
        else:
            process_video_task.delay(job_id)
    transaction.on_commit(start)
