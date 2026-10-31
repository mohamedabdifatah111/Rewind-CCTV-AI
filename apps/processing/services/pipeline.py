
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.ai_engine.services.gemini_service import (
    AIFatalError,
    AIRateLimitError,
    AIServiceError,
    get_analyzer,
)
from apps.processing.models import (
    FrameDescription,
    ProcessingJob,
    VideoFrame,
)
from apps.videos.models import Video

from .frames import (
    VideoReadError,
    estimate_total,
    iter_sampled_frames,
    probe_video,
)

logger = logging.getLogger(__name__)


def _fail(video, job, message):
    """Mark the processing job and video as failed."""

    now = timezone.now()

    job.status = ProcessingJob.Status.FAILED
    job.error_message = message
    job.completed_at = now

    job.save(
        update_fields=[
            "status",
            "error_message",
            "completed_at",
        ]
    )

    video.status = Video.Status.FAILED
    video.error_message = message

    video.save(
        update_fields=[
            "status",
            "error_message",
        ]
    )

    logger.error(
        "VIDEO PROCESSING FAILED | Video ID: %s | Job ID: %s | Reason: %s",
        video.pk,
        job.pk,
        message,
    )


def process_video(job_id):
    """
    Process one video from start to finish.

    Failures are recorded on the processing job and video.
    Individual AI frame failures are logged for debugging.
    """

    try:
        job = ProcessingJob.objects.select_related("video").get(
            pk=job_id
        )

    except ProcessingJob.DoesNotExist:
        logger.warning(
            "Processing job %s does not exist.",
            job_id,
        )
        return

    video = job.video

    logger.info(
        "STARTING VIDEO PROCESSING | Video ID: %s | Job ID: %s",
        video.pk,
        job.pk,
    )

    try:
        _run(job, video)

    except Video.DoesNotExist:
        logger.info(
            "Video %s was deleted during processing.",
            video.pk,
        )

    except (
        AIFatalError,
        AIRateLimitError,
        VideoReadError,
    ) as error:
        _fail(video, job, str(error))

    except Exception as error:
        logger.exception(
            "UNEXPECTED PROCESSING ERROR | Job ID: %s",
            job_id,
        )

        _fail(
            video,
            job,
            "Processing failed unexpectedly. Check server logs.",
        )


def _run(job, video):
    """Extract frames, analyse them, and save descriptions."""

    # Initialise the AI service.
    analyzer = get_analyzer()

    job.status = ProcessingJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.processed_frames = 0

    job.save(
        update_fields=[
            "status",
            "started_at",
            "processed_frames",
        ]
    )

    video.status = Video.Status.PROCESSING
    video.save(update_fields=["status"])

    path = video.original_file.path

    interval = settings.FRAME_INTERVAL_SECONDS

    logger.info(
        "VIDEO FILE: %s",
        path,
    )

    logger.info(
        "FRAME INTERVAL: %s seconds",
        interval,
    )

    # Read video metadata.
    info = probe_video(path)

    video.duration = info.duration
    video.save(update_fields=["duration"])

    job.total_frames = estimate_total(
        info.duration,
        interval,
    )

    job.save(update_fields=["total_frames"])

    logger.info(
        "VIDEO METADATA | Duration: %.2f seconds | Expected frames: %s",
        info.duration,
        job.total_frames,
    )

    # Remove previous frame descriptions before reprocessing.
    VideoFrame.objects.filter(video=video).delete()

    done = 0
    skipped = 0

    # Track individual errors for debugging.
    frame_errors = []

    # Extract and analyse sampled frames.
    for sf in iter_sampled_frames(
        path,
        interval,
        settings.FRAME_MAX_SIDE_PX,
    ):

        if not Video.objects.filter(pk=video.pk).exists():
            raise Video.DoesNotExist

        logger.info(
            "ANALYSING FRAME | Video: %s | Frame: %s | Timestamp: %.2fs | JPEG bytes: %s",
            video.pk,
            sf.frame_number,
            sf.timestamp,
            len(sf.jpeg) if sf.jpeg else 0,
        )

        try:
            # Send frame to Gemma.
            result = analyzer.analyze_frame(sf.jpeg)

            logger.info(
                "FRAME ANALYSIS SUCCESSFUL | Video: %s | Frame: %s",
                video.pk,
                sf.frame_number,
            )

        except (AIFatalError, AIRateLimitError):
            logger.exception(
                "FATAL AI ERROR | Video: %s | Frame: %s",
                video.pk,
                sf.frame_number,
            )
            raise

        except AIServiceError as error:
            skipped += 1

            error_message = str(error)

            frame_errors.append(error_message)

            # This prints the actual reason into your Django terminal.
            logger.error(
                "\n"
                "========== GEMMA FRAME ANALYSIS FAILED ==========\n"
                "Video ID: %s\n"
                "Frame number: %s\n"
                "Timestamp: %.2f seconds\n"
                "JPEG size: %s bytes\n"
                "Error type: %s\n"
                "Error message: %s\n"
                "=================================================",
                video.pk,
                sf.frame_number,
                sf.timestamp,
                len(sf.jpeg) if sf.jpeg else 0,
                type(error).__name__,
                error_message,
                exc_info=True,
            )

            continue

        # Save successfully analysed frames.
        with transaction.atomic():

            frame = VideoFrame.objects.create(
                video=video,
                timestamp_seconds=sf.timestamp,
                frame_number=sf.frame_number,
            )

            FrameDescription.objects.create(
                frame=frame,
                description=result.description,
                visible_objects=result.visible_objects,
                visible_actions=result.visible_actions,
                confidence=result.confidence,
            )

        done += 1

        job.processed_frames = done

        job.save(
            update_fields=[
                "processed_frames",
            ]
        )

        logger.info(
            "FRAME SAVED | Video: %s | Successful: %s | Skipped: %s",
            video.pk,
            done,
            skipped,
        )

    logger.info(
        "FRAME PROCESSING SUMMARY | Video: %s | Successful: %s | Failed: %s",
        video.pk,
        done,
        skipped,
    )

    # If every sampled frame failed, stop processing.
    if done == 0:

        if skipped > 0:
            unique_errors = list(dict.fromkeys(frame_errors))

            logger.error(
                "ALL SAMPLED FRAMES FAILED | Video: %s | Errors: %s",
                video.pk,
                unique_errors,
            )

        raise _NoFrames(
            skipped=skipped,
            errors=frame_errors,
        )

    # Mark processing as completed.
    now = timezone.now()

    job.status = ProcessingJob.Status.COMPLETED
    job.completed_at = now
    job.total_frames = max(job.total_frames, done)

    job.error_message = (
        f"{skipped} sampled frame(s) could not be analysed and were skipped."
        if skipped
        else ""
    )

    job.save(
        update_fields=[
            "status",
            "completed_at",
            "total_frames",
            "error_message",
        ]
    )

    video.status = Video.Status.COMPLETED
    video.processed_at = now
    video.error_message = ""

    video.save(
        update_fields=[
            "status",
            "processed_at",
            "error_message",
        ]
    )

    logger.info(
        "VIDEO PROCESSING COMPLETED | Video: %s | Analysed: %s | Skipped: %s",
        video.pk,
        done,
        skipped,
    )


class _NoFrames(VideoReadError):

    def __init__(self, skipped=0, errors=None):

        self.skipped = skipped
        self.errors = errors or []

        message = (
            f"No sampled frame could be analysed. "
            f"{skipped} frame(s) failed. "
            "Check the Django server logs for the actual Gemini errors."
        )

        super().__init__(message)
