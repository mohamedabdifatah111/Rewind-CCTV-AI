from django.urls import path
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import views

@api_view(["GET"])
def health(request): return Response({"status": "ok"})

@api_view(["GET"])
def config(request):
    return Response({"max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB, "supported_formats": settings.SUPPORTED_FORMATS,
                     "app_version": "1.0.0", "retention_days": settings.DATA_RETENTION_DAYS and int(settings.DATA_RETENTION_DAYS),
                     "model": settings.GEMMA_MODEL, "frame_interval_seconds": settings.FRAME_INTERVAL_SECONDS})

urlpatterns = [
    path("health/", health), path("config/", config),
    path("videos/", views.VideoListCreateView.as_view()),
    path("videos/upload/", views.VideoUploadView.as_view()),
    path("videos/<int:pk>/", views.VideoDetailView.as_view()),
    path("videos/<int:pk>/stream/", views.VideoStreamView.as_view(), name="video-stream"),
]
