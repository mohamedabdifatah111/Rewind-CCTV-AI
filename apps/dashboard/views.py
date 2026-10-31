from rest_framework.response import Response
from rest_framework.views import APIView
from apps.search.models import SearchLog
from apps.videos.models import Video
from apps.videos.serializers import VideoSerializer

class StatsView(APIView):
    def get(self, request):
        c = lambda *s: Video.objects.filter(status__in=s).count()
        recent = Video.objects.prefetch_related("jobs")[:5]
        return Response({
            "total_videos": Video.objects.count(), "processed_videos": c("completed"),
            "processing_videos": c("uploaded", "queued", "processing"), "failed_videos": c("failed"),
            "recent_videos": VideoSerializer(recent, many=True, context={"request": request}).data,
            "recent_searches": [{"id": s.id, "query": s.query, "video_title": s.video_title, "result_count": s.result_count,
                                 "created_at": s.created_at} for s in SearchLog.objects.all()[:5]],
        })
