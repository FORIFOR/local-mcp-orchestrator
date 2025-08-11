import json
import unittest


class TestImpactScan(unittest.TestCase):
    def run_scan(self, payload):
        from tools.impact_scan import run
        out = run(json.dumps(payload))
        return json.loads(out)

    def test_literal_mode_with_context(self):
        # search for a known symbol present in multiple files
        res = self.run_scan({"query": "divide", "mode": "literal", "context": 1, "limit": 50})
        self.assertFalse(res.get("error"), msg=res.get("error"))
        hits = res.get("hits") or []
        self.assertGreater(len(hits), 0)
        # ensure context fields exist on at least one hit
        has_ctx = any("context_before" in h or "context_after" in h for h in hits)
        self.assertTrue(has_ctx)
        self.assertIn("files_ranked", res)
        self.assertIn("used", res)
        self.assertEqual(res["used"].get("ripgrep", {}).get("mode"), "literal")

    def test_regex_mode(self):
        # regex for function def
        res = self.run_scan({"query": r"def\s+divide", "mode": "regex", "limit": 50})
        self.assertFalse(res.get("error"))
        hits = res.get("hits") or []
        self.assertGreater(len(hits), 0)

    def test_word_mode(self):
        res = self.run_scan({"query": "divide", "mode": "word", "limit": 50})
        self.assertFalse(res.get("error"))
        hits = res.get("hits") or []
        self.assertGreater(len(hits), 0)

    def test_pyright_env_options_passed(self):
        res = self.run_scan({
            "query": "def ",
            "mode": "regex",
            "limit": 10,
            "pyright": {"pythonVersion": "3.11", "venvPath": "/tmp/x", "venv": "venv"},
        })
        used = (res.get("used") or {}).get("pyright") or {}
        # pyright may be missing; still should echo options
        self.assertEqual(used.get("pythonVersion"), "3.11")
        self.assertEqual(used.get("venvPath"), "/tmp/x")
        self.assertEqual(used.get("venv"), "venv")


if __name__ == "__main__":
    unittest.main()

