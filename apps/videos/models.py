import os, uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

def upload_path(instance, filename):
    """Server-chosen name: the client filename never touches the filesystem."""
    ext = os.path.splitext(filename)[1].lower()
    return f"videos/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{ext}"

class Video(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded"; QUEUED = "queued"; PROCESSING = "processing"; COMPLETED = "completed"; FAILED = "failed"
    title = models.CharField(max_length=255)
    original_file = models.FileField(upload_to=upload_path, max_length=255)
    file_size = models.BigIntegerField(default=0)
    duration = models.FloatField(null=True, blank=True, help_text="seconds")
    mime_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.UPLOADED)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["-uploaded_at"])]

    def __str__(self):
        return self.title

@receiver(post_delete, sender=Video)
def delete_video_file(sender, instance, **kwargs):
    if instance.original_file:
        instance.original_file.delete(save=False)
