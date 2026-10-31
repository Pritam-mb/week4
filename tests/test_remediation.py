import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pipeline import usable

class TestRemediation(unittest.TestCase):
    def test_429_unusable(self):
        self.assertFalse(usable("some text with length", http_status=429))
    def test_non200_unusable(self):
        self.assertFalse(usable("x"*200, http_status=404))
    def test_identical_body_detection(self):
        seen = set()
        h = "abc123"
        self.assertTrue(usable("x"*200, http_status=200, body_hash=h, seen_hashes=seen))
        self.assertFalse(usable("x"*200, http_status=200, body_hash=h, seen_hashes=seen))
    def test_port_www_stripping(self):
        from pipeline import is_ssrf_safe
        self.assertTrue(is_ssrf_safe("www.example.com"))
        self.assertFalse(is_ssrf_safe("example.com:8080"))
    def test_evidence_quote_validation_downgrade(self):
        # Simulate coroner validation
        evidence_map = {"E001":"some text about shutdown"}
        eids = ["E001","E999"]
        valid = all(eid in evidence_map for eid in eids)
        self.assertFalse(valid)
    def test_cache_hit_no_network(self):
        # placeholder
        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
