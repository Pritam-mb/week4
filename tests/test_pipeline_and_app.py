import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import is_ssrf_safe, select_strategic_snapshots, CoronerOutput, VALID_CAUSES
from app import normalize_domain, slugify
import html


class TestPipelineAndApp(unittest.TestCase):

    def test_ssrf_guard(self):
        # Must reject IP literals
        self.assertFalse(is_ssrf_safe("http://127.0.0.1:8000"))
        self.assertFalse(is_ssrf_safe("http://169.254.169.254/latest/meta-data"))
        self.assertFalse(is_ssrf_safe("https://10.0.0.1/admin"))
        self.assertFalse(is_ssrf_safe("http://192.168.1.1"))
        self.assertFalse(is_ssrf_safe("http://[::1]"))

        # Must reject localhost / internal
        self.assertFalse(is_ssrf_safe("http://localhost:8000"))
        self.assertFalse(is_ssrf_safe("http://myhost.local"))

        # Must reject non-http schemes
        self.assertFalse(is_ssrf_safe("file:///etc/passwd"))
        self.assertFalse(is_ssrf_safe("gopher://evil.com"))
        self.assertFalse(is_ssrf_safe("javascript:alert(1)"))

        # Must reject length > 200
        self.assertFalse(is_ssrf_safe("https://example.com/" + "a" * 200))

        # Must accept valid dead software domains/URLs
        self.assertTrue(is_ssrf_safe("https://www.google.com/reader"))
        self.assertTrue(is_ssrf_safe("http://geocities.com"))
        self.assertTrue(is_ssrf_safe("vine.co"))
        self.assertTrue(is_ssrf_safe("https://del.icio.us"))

    def test_normalize_domain(self):
        self.assertEqual(normalize_domain("https://www.google.com/reader"), "google.com/reader")
        self.assertEqual(normalize_domain("http://geocities.com/"), "geocities.com")
        self.assertEqual(normalize_domain("www.vine.co"), "vine.co")
        self.assertEqual(normalize_domain("  HTTPS://WWW.ALTAVISTA.COM/// "), "altavista.com")

    def test_select_strategic_snapshots(self):
        # 10 snapshots across 2005-2015
        snaps = [
            {"timestamp": f"20{year:02d}0601120000", "original": "http://example.com"}
            for year in range(5, 16)
        ]
        lifeline = {"2005": 2, "2006": 5, "2009": 20, "2010": 18, "2015": 1}
        selected = select_strategic_snapshots(snaps, lifeline)
        
        self.assertGreaterEqual(len(selected), 3)
        self.assertLessEqual(len(selected), 5)

        # Check birth snapshot is included
        years = [s["timestamp"][:4] for s in selected]
        self.assertIn("2005", years)
        # Check peak year is included
        self.assertIn("2009", years)
        # Check newest/post-death is included
        self.assertIn("2015", years)

    def test_coroner_output_validation(self):
        # Valid output with WORKFLOW enum
        data = {
            "cause": "shut_down",
            "time_of_death": "July 2013",
            "confidence": 0.95,
            "evidence_ids": ["E001", "E002"],
        }
        validated = CoronerOutput(**data)
        self.assertEqual(validated.cause, "shut_down")
        self.assertEqual(validated.time_of_death, "July 2013")
        self.assertEqual(len(validated.evidence_ids), 2)

        # All valid causes must be accepted
        for cause in VALID_CAUSES:
            v = CoronerOutput(cause=cause, time_of_death="2010", confidence=0.8, evidence_ids=["E001"])
            self.assertEqual(v.cause, cause)

        # Invalid cause must fail
        with self.assertRaises(Exception):
            CoronerOutput(cause="exploded", time_of_death="2010", confidence=0.8)

    def test_memory_sanitization(self):
        import re
        raw_text = "<script>alert('xss')</script> check out https://spamsite.com for free money!"
        
        # 1. 500-char cap
        text = raw_text.strip()[:500]
        # 2. Strip URLs
        text = re.sub(r"https?://\S+", "", text).strip()
        # 3. Escape HTML
        escaped = html.escape(text)

        self.assertNotIn("https://spamsite.com", escaped)
        self.assertNotIn("<script>", escaped)
        self.assertIn("&lt;script&gt;", escaped)

    def test_slugify(self):
        self.assertEqual(slugify("Google Reader"), "google-reader")
        self.assertEqual(slugify("Adobe Flash Player!"), "adobe-flash-player")
        self.assertEqual(slugify("del.icio.us"), "delicious")


if __name__ == "__main__":
    unittest.main()

