from django.urls import reverse
from rest_framework import serializers
from .models import Video

PUBLIC_STATUS = {"uploaded": "pending", "queued": "pending"}  # the UI polls on pending/processing

def public_status(s):
    return PUBLIC_STATUS.get(s, s)

class VideoSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.FloatField(source="duration", read_only=True)
    status = serializers.SerializerMethodField()
    raw_status = serializers.CharField(source="status", read_only=True)
    progress = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    frames_processed = serializers.SerializerMethodField()
    error = serializers.CharField(source="error_message", read_only=True)

    class Meta:
        model = Video
        fields = ["id", "title", "uploaded_at", "processed_at", "duration_seconds", "status", "raw_status", "progress", "file_size",
                  "mime_type", "file_url", "thumbnail_url", "frames_processed", "error"]

    def _job(self, obj):
        jobs = getattr(obj, "_prefetched_objects_cache", {}).get("jobs")
        return (jobs[0] if jobs else None) if jobs is not None else obj.jobs.first()

    def get_status(self, obj): return public_status(obj.status)
    def get_thumbnail_url(self, obj): return None
    def get_file_url(self, obj):
        return self.context["request"].build_absolute_uri(reverse("video-stream", args=[obj.pk]))
    def get_frames_processed(self, obj):
        j = self._job(obj); return j.processed_frames if j else 0
    def get_progress(self, obj):
        if obj.status == "completed": return 100
        j = self._job(obj)
        return min(99, int(j.processed_frames * 100 / j.total_frames)) if j and j.total_frames else None

class VideoDetailSerializer(VideoSerializer):
    analysis = serializers.SerializerMethodField()
    frames_extracted = serializers.SerializerMethodField()
    class Meta(VideoSerializer.Meta):
        fields = VideoSerializer.Meta.fields + ["analysis", "frames_extracted"]
    def get_frames_extracted(self, obj): return obj.frames.count()
    def get_analysis(self, obj):
        qs = obj.frames.select_related("description").order_by("timestamp_seconds")
        return [{"timestamp_seconds": f.timestamp_seconds, "description": f.description.description} for f in qs if hasattr(f, "description")]

class VideoUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
