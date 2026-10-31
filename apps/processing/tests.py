import os, shutil, tempfile
from unittest import mock
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from apps.ai_engine.services.gemini_service import AIFatalError, AIRateLimitError, AIServiceError, FrameAnalysis
from apps.common.testing import make_video, video_bytes
from apps.processing.models import FrameDescription, ProcessingJob, VideoFrame
from apps.processing.services import frames, pipeline
from apps.videos.models import Video

MEDIA = tempfile.mkdtemp()

class FakeAnalyzer:
    def __init__(self, behaviour=None): self.calls = 0; self.behaviour = behaviour
    def analyze_frame(self, jpeg):
        self.calls += 1
        if self.behaviour: return self.behaviour(self.calls)
        return FrameAnalysis(f"A person carrying a dark bag (call {self.calls}).", ["bag"], ["carrying"])

@override_settings(MEDIA_ROOT=MEDIA, FRAME_INTERVAL_SECONDS=2)
class ProcessingTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); shutil.rmtree(MEDIA, ignore_errors=True)
    def make(self, **kw):
        v = Video.objects.create(title="t.mp4", original_file=ContentFile(video_bytes(**kw), name="t.mp4"), status="queued")
        return v, ProcessingJob.objects.create(video=v)
    def run_job(self, job, analyzer):
        with mock.patch.object(pipeline, "get_analyzer", return_value=analyzer): pipeline.process_video(job.pk)
        job.refresh_from_db(); job.video.refresh_from_db()

    def test_timestamps_are_exact_seconds(self):
        path = os.path.join(MEDIA, "ts.mp4"); make_video(path, seconds=7, fps=10)
        got = [(f.frame_number, f.timestamp) for f in frames.iter_sampled_frames(path, 2)]
        self.assertEqual(got, [(0, 0.0), (20, 2.0), (40, 4.0), (60, 6.0)])
        self.assertAlmostEqual(frames.probe_video(path).duration, 7.0, places=1)

    def test_corrupt_file_raises(self):
        p = os.path.join(MEDIA, "bad.mp4"); open(p, "wb").write(b"garbage" * 100)
        with self.assertRaises(frames.VideoReadError): frames.probe_video(p)

    def test_successful_processing_stores_descriptions(self):
        v, job = self.make(seconds=5); a = FakeAnalyzer(); self.run_job(job, a)
        v.refresh_from_db(); self.assertEqual((job.status, v.status, a.calls), ("completed", "completed", 3))
        self.assertEqual(list(VideoFrame.objects.filter(video=v).values_list("timestamp_seconds", flat=True)), [0.0, 2.0, 4.0])
        d = FrameDescription.objects.first()
        self.assertIn("dark bag", d.search_text); self.assertIsNone(d.confidence)
        self.assertEqual((job.processed_frames, job.total_frames), (3, 3)); self.assertIsNotNone(v.processed_at)

    def test_gemini_auth_failure_fails_job_without_leaking_internals(self):
        v, job = self.make(); self.run_job(job, FakeAnalyzer(lambda n: (_ for _ in ()).throw(AIFatalError("Gemini API rejected the request (403)."))))
        v.refresh_from_db(); self.assertEqual((job.status, v.status), ("failed", "failed")); self.assertIn("403", v.error_message)
        self.assertEqual(VideoFrame.objects.count(), 0)

    def test_rate_limit_stops_job(self):
        v, job = self.make(); a = FakeAnalyzer(lambda n: (_ for _ in ()).throw(AIRateLimitError("quota")))
        self.run_job(job, a); self.assertEqual((job.status, a.calls), ("failed", 1))

    def test_transient_frame_failures_are_skipped_and_reported(self):
        def b(n):
            if n == 2: raise AIServiceError("boom")
            return FrameAnalysis("ok")
        v, job = self.make(seconds=5); self.run_job(job, FakeAnalyzer(b))
        self.assertEqual((job.status, job.processed_frames), ("completed", 2)); self.assertIn("1 sampled frame", job.error_message)

    def test_all_frames_failing_fails_job(self):
        v, job = self.make(); self.run_job(job, FakeAnalyzer(lambda n: (_ for _ in ()).throw(AIServiceError("x"))))
        self.assertEqual(job.status, "failed")

    def test_missing_api_key_fails_cleanly(self):
        v, job = self.make()
        with override_settings(GEMINI_API_KEY=""): pipeline.process_video(job.pk)
        job.refresh_from_db(); self.assertEqual(job.status, "failed"); self.assertIn("GEMINI_API_KEY", job.error_message)

    def test_api_endpoints_for_frames_jobs_processing_and_stats(self):
        v, job = self.make(); self.run_job(job, FakeAnalyzer())
        self.assertEqual(self.client.get(f"/api/videos/{v.pk}/frames/").data["count"], 3)
        self.assertEqual(self.client.get(f"/api/videos/{v.pk}/processing/").data["status"], "completed")
        self.assertEqual(self.client.get("/api/jobs/").data["results"][0]["frames_processed"], 3)
        self.assertEqual(len(self.client.get(f"/api/videos/{v.pk}/").data["analysis"]), 3)
        s = self.client.get("/api/dashboard/stats/").data
        self.assertEqual((s["total_videos"], s["processed_videos"], s["failed_videos"]), (1, 1, 0))
