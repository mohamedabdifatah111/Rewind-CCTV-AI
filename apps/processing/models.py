from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

class ProcessingJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued"; PROCESSING = "processing"; COMPLETED = "completed"; FAILED = "failed"
    video = models.ForeignKey("videos.Video", on_delete=models.CASCADE, related_name="jobs")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_frames = models.PositiveIntegerField(default=0, help_text="estimated; 0 = unknown")
    processed_frames = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status"])]

class VideoFrame(models.Model):
    video = models.ForeignKey("videos.Video", on_delete=models.CASCADE, related_name="frames")
    timestamp_seconds = models.FloatField()
    frame_number = models.PositiveIntegerField()
    frame_image_path = models.CharField(max_length=500, blank=True, help_text="unused by default: frames are analysed in memory and not retained")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["video_id", "timestamp_seconds"]
        indexes = [models.Index(fields=["video", "timestamp_seconds"])]
        constraints = [models.UniqueConstraint(fields=["video", "frame_number"], name="uniq_video_frame_number")]

class FrameDescription(models.Model):
    frame = models.OneToOneField(VideoFrame, on_delete=models.CASCADE, related_name="description")
    description = models.TextField()
    visible_objects = models.JSONField(default=list)
    visible_actions = models.JSONField(default=list)
    confidence = models.FloatField(null=True, blank=True)
    search_text = models.TextField(blank=True, help_text="description + objects + actions; the full-text search column")
    created_at = models.DateTimeField(auto_now_add=True)

@receiver(pre_save, sender=FrameDescription)
def build_search_text(sender, instance, **kwargs):
    instance.search_text = " . ".join([instance.description, *map(str, instance.visible_objects), *map(str, instance.visible_actions)])
