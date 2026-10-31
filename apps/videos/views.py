import os, re
from django.db import transaction
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import get_valid_filename
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.processing.models import ProcessingJob
from apps.processing.services.frames import VideoReadError, probe_video
from apps.processing.tasks import queue_processing
from .models import Video
from .serializers import VideoDetailSerializer, VideoSerializer, VideoUploadSerializer
from .validators import validate_video_upload

STATUS_FILTER = {"pending": ["uploaded", "queued"], "processing": ["processing"], "completed": ["completed"], "failed": ["failed"],
                 "uploaded": ["uploaded"], "queued": ["queued"]}

def handle_upload(request):
    ser = VideoUploadSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    f = ser.validated_data["file"]
    _, mime = validate_video_upload(f)
    title = get_valid_filename(os.path.basename(ser.validated_data.get("title") or f.name))[:200] or "video"
    video = Video.objects.create(title=title, original_file=f, file_size=f.size, mime_type=mime)
    try:  # decode check on the stored copy
        info = probe_video(video.original_file.path)
    except VideoReadError as e:
        video.delete()
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        video.duration, video.status = info.duration, Video.Status.QUEUED
        video.save(update_fields=["duration", "status"])
        job = ProcessingJob.objects.create(video=video)
        queue_processing(job.pk)
    return Response(VideoSerializer(video, context={"request": request}).data, status=status.HTTP_201_CREATED)

class VideoListCreateView(ListCreateAPIView):
    """GET list (search, status, page, page_size) / POST upload (alias of /videos/upload/)."""
    serializer_class = VideoSerializer
    def get_queryset(self):
        qs = Video.objects.prefetch_related("jobs")
        q, st = self.request.query_params.get("search"), self.request.query_params.get("status")
        if q: qs = qs.filter(title__icontains=q)
        if st in STATUS_FILTER: qs = qs.filter(status__in=STATUS_FILTER[st])
        return qs
    def create(self, request, *a, **k): return handle_upload(request)

class VideoUploadView(APIView):
    def post(self, request): return handle_upload(request)

class VideoDetailView(RetrieveDestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoDetailSerializer
    def perform_destroy(self, instance):
        instance.delete()  # cascades jobs/frames/descriptions; post_delete removes the file

class VideoStreamView(APIView):
    """Serves the original file with HTTP Range support so <video> can seek. Media is not otherwise exposed."""
    def get(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        try: path = video.original_file.path
        except ValueError: raise Http404
        if not os.path.exists(path): raise Http404
        size = os.path.getsize(path)
        start, end, code = 0, size - 1, 200
        m = re.match(r"bytes=(\d*)-(\d*)$", request.headers.get("Range", ""))
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1)); end = int(m.group(2)) if m.group(2) else end
            else:
                start = max(size - int(m.group(2)), 0)
            end = min(end, size - 1)
            if start > end: return Response(status=416, headers={"Content-Range": f"bytes */{size}"})
            code = 206
        def chunks(remaining=end - start + 1):
            with open(path, "rb") as fh:
                fh.seek(start)
                while remaining > 0:
                    data = fh.read(min(1024 * 1024, remaining))
                    if not data: break
                    remaining -= len(data); yield data
        resp = StreamingHttpResponse(chunks(), status=code, content_type=video.mime_type or "video/mp4")
        resp["Accept-Ranges"] = "bytes"; resp["Content-Length"] = str(end - start + 1)
        if code == 206: resp["Content-Range"] = f"bytes {start}-{end}/{size}"
        return resp
