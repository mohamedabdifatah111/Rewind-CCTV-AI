from django.db import models
class SearchLog(models.Model):
    query = models.CharField(max_length=500)
    video = models.ForeignKey("videos.Video", null=True, blank=True, on_delete=models.SET_NULL)
    video_title = models.CharField(max_length=255, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at"]
