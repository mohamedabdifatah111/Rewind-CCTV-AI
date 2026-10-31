from django.test import TestCase
from apps.processing.models import FrameDescription, VideoFrame
from apps.search.models import SearchLog
from apps.search.services import normalise_query
from django.core.files.base import ContentFile
from apps.videos.models import Video

class SearchTests(TestCase):
    def setUp(self):
        self.v1 = Video.objects.create(title="office.mp4", original_file=ContentFile(b"x", name="a.mp4"), status="completed")
        self.v2 = Video.objects.create(title="lobby.mp4", original_file=ContentFile(b"x", name="b.mp4"), status="completed")
        for v, t, d, o, a in [(self.v1, 12.0, "A person enters the room carrying a dark bag.", ["bag", "door"], ["entering", "carrying a bag"]),
                              (self.v1, 20.0, "An empty desk with a chair.", ["desk", "chair"], []),
                              (self.v2, 4.0, "A person walks past a desk.", ["desk"], ["walking"])]:
            f = VideoFrame.objects.create(video=v, timestamp_seconds=t, frame_number=int(t * 10))
            FrameDescription.objects.create(frame=f, description=d, visible_objects=o, visible_actions=a)

    def post(self, **b): return self.client.post("/api/search/", b, content_type="application/json")

    def test_normalisation_drops_filler(self):
        self.assertEqual(normalise_query("Show me when someone entered the room carrying a bag"), ["entered", "room", "carrying", "bag"])

    def test_match_returns_timestamp_title_and_real_score(self):
        r = self.post(query="Find when someone entered carrying a bag").json()
        top = r["results"][0]
        self.assertEqual((top["video_title"], top["timestamp_seconds"]), ("office.mp4", 12.0))
        self.assertTrue(0 < top["relevance_score"] <= 1)
        self.assertEqual([x["relevance_score"] for x in r["results"]], sorted((x["relevance_score"] for x in r["results"]), reverse=True))

    def test_restrict_to_video(self):
        r = self.post(query="desk", video_id=self.v2.pk).json()
        self.assertEqual([x["video_id"] for x in r["results"]], [self.v2.pk])

    def test_no_match_returns_empty_with_message(self):
        r = self.post(query="helicopter landing"); self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["results"], []); self.assertIn("No matching", r.json()["message"])

    def test_validation_and_unknown_video(self):
        self.assertEqual(self.post(query="").status_code, 400)
        self.assertEqual(self.post(query="show me when").status_code, 400)
        self.assertEqual(self.post(query="desk", video_id=9999).status_code, 404)

    def test_search_is_logged(self):
        self.post(query="desk"); self.assertEqual(SearchLog.objects.get().result_count, 2)
