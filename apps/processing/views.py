from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.videos.models import Video
from .models import ProcessingJob, VideoFrame
from .serializers import FrameSerializer, JobSerializer

class JobListView(ListAPIView):
    serializer_class = JobSerializer
    def get_queryset(self):
        qs = ProcessingJob.objects.select_related("video")
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st in ProcessingJob.Status.values else qs

class VideoFramesView(ListAPIView):
    serializer_class = FrameSerializer
    def get_queryset(self):
        get_object_or_404(Video, pk=self.kwargs["pk"])
        return VideoFrame.objects.filter(video_id=self.kwargs["pk"], description__isnull=False).select_related("description")

class VideoProcessingView(APIView):
    def get(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        job = video.jobs.select_related("video").first()
        if not job:
            return Response({"detail": "No processing job for this video."}, status=404)
        return Response(JobSerializer(job).data)
