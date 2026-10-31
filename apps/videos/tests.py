import os, shutil, tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from apps.common.testing import video_bytes
from apps.processing.models import FrameDescription, ProcessingJob, VideoFrame
from apps.videos.models import Video

MEDIA = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=MEDIA, PROCESSING_MODE="thread", MAX_UPLOAD_SIZE_MB=1)
class UploadTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); shutil.rmtree(MEDIA, ignore_errors=True)

    def upload(self, content=None, name="cam1.mp4", ctype="video/mp4", url="/api/videos/upload/"):
        content = video_bytes() if content is None else content
        with self.captureOnCommitCallbacks(execute=False) as cbs:
            r = self.client.post(url, {"file": SimpleUploadedFile(name, content, content_type=ctype)}, format="multipart")
        return r, cbs

    def test_successful_upload_creates_video_and_job_and_queues(self):
        r, cbs = self.upload()
        self.assertEqual(r.status_code, 201, r.content)
        v = Video.objects.get(pk=r.data["id"])
        self.assertEqual((v.status, r.data["status"], r.data["raw_status"]), ("queued", "pending", "queued"))
        self.assertAlmostEqual(v.duration, 5.0, places=1)
        self.assertEqual(ProcessingJob.objects.filter(video=v, status="queued").count(), 1)
        self.assertEqual(len(cbs), 1)  # processing is queued after commit, not run inside the request
        self.assertNotIn(".mp4", v.original_file.name.split("/")[-1].replace(".mp4", "", 1) or "x")
        self.assertTrue(os.path.exists(v.original_file.path))

    def test_alias_endpoint_used_by_frontend(self):
        r, _ = self.upload(url="/api/videos/"); self.assertEqual(r.status_code, 201)

    def test_rejects_bad_type_empty_oversized_and_fake_content(self):
        self.assertEqual(self.upload(b"hello", "x.txt", "text/plain")[0].status_code, 400)
        self.assertEqual(self.upload(b"", "x.mp4")[0].status_code, 400)
        self.assertEqual(self.upload(b"\0" * (2 * 1024 * 1024), "big.mp4")[0].status_code, 400)
        self.assertEqual(self.upload(b"not really a video at all", "fake.mp4")[0].status_code, 400)
        self.assertEqual(self.upload(video_bytes(), "x.mp4", "image/png")[0].status_code, 400)
        self.assertEqual(Video.objects.count(), 0)

    def test_corrupt_video_with_valid_header_is_rejected_and_not_kept(self):
        r, _ = self.upload(b"\x00\x00\x00\x18ftypmp42" + os.urandom(2000))
        self.assertEqual(r.status_code, 400); self.assertEqual(Video.objects.count(), 0)

    def test_path_traversal_filename_is_neutralised(self):
        r, _ = self.upload(name="../../etc/evil.mp4")
        self.assertEqual(r.status_code, 201)
        v = Video.objects.get(); self.assertTrue(v.original_file.name.startswith("videos/")); self.assertNotIn("..", v.original_file.name)
        self.assertNotIn("/", v.title)

    def test_delete_removes_file_and_all_related_records(self):
        r, _ = self.upload(); v = Video.objects.get(pk=r.data["id"]); path = v.original_file.path
        f = VideoFrame.objects.create(video=v, timestamp_seconds=0, frame_number=0)
        FrameDescription.objects.create(frame=f, description="x")
        self.assertEqual(self.client.delete(f"/api/videos/{v.pk}/").status_code, 204)
        self.assertFalse(os.path.exists(path))
        self.assertEqual((Video.objects.count(), ProcessingJob.objects.count(), VideoFrame.objects.count(), FrameDescription.objects.count()), (0, 0, 0, 0))
        self.assertEqual(self.client.get(f"/api/videos/{v.pk}/").status_code, 404)

    def test_list_filter_stream_range_and_config(self):
        r, _ = self.upload(); vid = r.data["id"]
        self.assertEqual(self.client.get("/api/videos/?status=pending").data["count"], 1)
        self.assertEqual(self.client.get("/api/videos/?status=failed").data["count"], 0)
        self.assertEqual(self.client.get("/api/videos/?search=cam1").data["count"], 1)
        s = self.client.get(f"/api/videos/{vid}/stream/", HTTP_RANGE="bytes=0-99")
        self.assertEqual((s.status_code, len(b"".join(s.streaming_content))), (206, 100))
        self.assertEqual(self.client.get("/api/config/").data["supported_formats"], ["mp4", "mov", "avi"])
