import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from starlette.testclient import TestClient
from app import app


class TestRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Disable limiter for general functional tests
        app.state.limiter.enabled = False
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.state.limiter.enabled = True

    def test_health_route(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertIn("llm_provider", data)
        self.assertIn("browserbase_configured", data)
        self.assertIn("sentry_configured", data)
        # Ensure no secrets leaked
        text = resp.text.lower()
        self.assertNotIn("bb_live", text)
        self.assertNotIn("gsk_", text)
        self.assertNotIn("aq.", text)

    def test_cemetery_route(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Graveyard", resp.text)
        self.assertIn("Google Reader", resp.text)

    def test_grave_route(self):
        resp = self.client.get("/grave/google-reader")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Google Reader", resp.text)
        self.assertIn("Eulogy written by", resp.text)

    def test_marigold_route(self):
        resp = self.client.post("/marigold/google-reader")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("marigolds", data)
        self.assertGreaterEqual(data["marigolds"], 1)

    def test_memory_route_and_sanitization(self):
        resp = self.client.post(
            "/memory/google-reader",
            data={"text": "I loved Google Reader! Visit https://spam.com for news."}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("memories", data)
        latest = data["memories"][-1]["text"]
        self.assertNotIn("https://spam.com", latest)
        self.assertIn("I loved Google Reader!", latest)

    def test_benchmark_route(self):
        resp = self.client.get("/benchmark")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Benchmark", resp.text)
        # Ensure no emojis in rendered HTML
        for char in resp.text:
            code = ord(char)
            self.assertFalse(
                0x1F300 <= code <= 0x1F9FF or 0x2600 <= code <= 0x27BF,
                f"Emoji found in benchmark HTML: {char!r} (U+{code:04X})"
            )

    def test_bury_ssrf_protection(self):
        # Localhost rejection
        resp1 = self.client.post("/bury", data={"url": "http://127.0.0.1:8000"})
        self.assertEqual(resp1.status_code, 400)

        # AWS metadata IP rejection
        resp2 = self.client.post("/bury", data={"url": "http://169.254.169.254/latest"})
        self.assertEqual(resp2.status_code, 400)

        # File scheme rejection
        resp3 = self.client.post("/bury", data={"url": "file:///etc/passwd"})
        self.assertEqual(resp3.status_code, 400)

    def test_bury_deduplication(self):
        # Google Reader is already in graveyard.db
        resp = self.client.post("/bury", data={"url": "https://www.google.com/reader", "name": "Google Reader"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("job_id"))
        self.assertEqual(data.get("existing_slug"), "google-reader")
        self.assertIn("Already in the graveyard", data.get("message", ""))


if __name__ == "__main__":
    unittest.main()
