import os
from unittest import mock, skipUnless
from django.test import SimpleTestCase
from google.genai import errors
from apps.ai_engine.services import gemini_service as g

GOOD = '```json\n{"description": "A person walks in carrying a dark bag.", "visible_objects": ["bag", 3], "visible_actions": ["walking"]}\n```'

class ParseTests(SimpleTestCase):
    def test_parses_fenced_json_and_normalises(self):
        r = g.parse_model_output(GOOD)
        self.assertEqual(r.visible_objects, ["bag"]); self.assertIsNone(r.confidence)
    def test_invalid_outputs_rejected(self):
        for bad in ["", "no json here", '{"description": ""}', '{"description": 5}', "{broken"]:
            with self.assertRaises(g.AIInvalidResponse): g.parse_model_output(bad)

class ServiceFailureTests(SimpleTestCase):
    def svc(self): return g.GeminiService(api_key="k", model="m", max_retries=2)
    def test_retries_transient_then_succeeds(self):
        s = self.svc()
        with mock.patch.object(s, "_generate", side_effect=[errors.APIError(503, {"error": {"message": "x"}}), GOOD]), mock.patch.object(g, "_sleep"):
            self.assertIn("dark bag", s.analyze_frame(b"x").description)
    def test_auth_error_is_fatal_and_not_retried(self):
        s = self.svc()
        with mock.patch.object(s, "_generate", side_effect=errors.APIError(403, {"error": {"message": "x"}})) as m, mock.patch.object(g, "_sleep"):
            with self.assertRaises(g.AIFatalError): s.analyze_frame(b"x")
        self.assertEqual(m.call_count, 1)
    def test_rate_limit_after_retries(self):
        s = self.svc()
        with mock.patch.object(s, "_generate", side_effect=errors.APIError(429, {"error": {"message": "x"}})) as m, mock.patch.object(g, "_sleep"):
            with self.assertRaises(g.AIRateLimitError): s.analyze_frame(b"x")
        self.assertEqual(m.call_count, 3)
    def test_network_error_becomes_service_error(self):
        s = self.svc()
        with mock.patch.object(s, "_generate", side_effect=TimeoutError()), mock.patch.object(g, "_sleep"):
            with self.assertRaises(g.AIServiceError): s.analyze_frame(b"x")
    def test_missing_key_is_fatal(self):
        with self.assertRaises(g.AIFatalError): g.GeminiService(api_key="")

@skipUnless(os.environ.get("GEMINI_INTEGRATION_API_KEY"), "set GEMINI_INTEGRATION_API_KEY to run the paid, real-API test")
class RealApiIntegrationTest(SimpleTestCase):
    def test_real_frame(self):
        import cv2, numpy as np
        img = np.full((240, 320, 3), 200, np.uint8); cv2.rectangle(img, (100, 80), (220, 200), (30, 30, 30), -1)
        r = g.GeminiService(api_key=os.environ["GEMINI_INTEGRATION_API_KEY"]).analyze_frame(cv2.imencode(".jpg", img)[1].tobytes())
        self.assertTrue(r.description)
