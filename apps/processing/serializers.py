from rest_framework import serializers
from apps.videos.serializers import public_status
from .models import FrameDescription, ProcessingJob, VideoFrame

class JobSerializer(serializers.ModelSerializer):
    video_id = serializers.IntegerField(read_only=True)
    video_title = serializers.CharField(source="video.title", read_only=True)
    status = serializers.SerializerMethodField()
    frames_processed = serializers.IntegerField(source="processed_frames", read_only=True)
    error = serializers.CharField(source="error_message", read_only=True)
    class Meta:
        model = ProcessingJob
        fields = ["id", "video_id", "video_title", "status", "created_at", "started_at", "completed_at", "total_frames", "frames_processed", "error"]
    def get_status(self, obj): return public_status(obj.status)

class FrameSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="description.description")
    visible_objects = serializers.JSONField(source="description.visible_objects")
    visible_actions = serializers.JSONField(source="description.visible_actions")
    confidence = serializers.FloatField(source="description.confidence")
    class Meta:
        model = VideoFrame
        fields = ["id", "timestamp_seconds", "frame_number", "description", "visible_objects", "visible_actions", "confidence"]
