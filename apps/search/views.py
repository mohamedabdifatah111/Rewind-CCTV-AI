from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.videos.models import Video
from .models import SearchLog
from .services import search_frames

class SearchRequest(serializers.Serializer):
    query = serializers.CharField(min_length=2, max_length=500)
    video_id = serializers.IntegerField(required=False, allow_null=True)

class SearchView(APIView):
    def post(self, request):
        ser = SearchRequest(data=request.data); ser.is_valid(raise_exception=True)
        q, vid = ser.validated_data["query"], ser.validated_data.get("video_id")
        video = None
        if vid:
            video = Video.objects.filter(pk=vid).first()
            if not video: return Response({"detail": "Video not found."}, status=404)
        try:
            results = search_frames(q, vid)
        except ValueError as e:
            return Response({"query": [str(e)]}, status=400)
        SearchLog.objects.create(query=q, video=video, video_title=video.title if video else "", result_count=len(results))
        msg = "" if results else "No matching moments. Only sampled frames are analysed, so brief events between samples can be missed."
        return Response({"results": results, "count": len(results), "message": msg})
