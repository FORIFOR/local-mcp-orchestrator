import json
import unittest
from pathlib import Path


class TestPatchFlow(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.tmp_dir = self.root / "tmp"
        self.tmp_dir.mkdir(exist_ok=True)

    def test_create_modify_conflict_delete(self):
        # Import functions directly
        from tools.edit.plan_patch import plan_patch
        from tools.edit.apply_patch import run as apply_run

        p = self.tmp_dir / "e2e_hello.txt"
        rel = str(p.relative_to(self.root))

        # 1) Create new file (ensure clean)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        pp = plan_patch({"path": rel, "new_content": "hi\n"})
        self.assertFalse(pp.get("no_changes"))
        out = apply_run(json.dumps(pp))
        self.assertIn("ok: 1 file(s) updated", out)
        self.assertTrue(p.exists())
        self.assertEqual(p.read_text(), "hi\n")

        # 2) No change
        same = plan_patch({"path": rel, "new_content": "hi\n"})
        self.assertTrue(same.get("no_changes"))

        # 3) Modify then simulate conflict
        mod = plan_patch({"path": rel, "new_content": "hi there\n"})
        # external change
        p.write_text("external change\n", encoding="utf-8")
        out2 = apply_run(json.dumps(mod))
        self.assertIn("conflict", out2)

        # 4) Delete
        # Recompute plan on current content to avoid conflict
        pp2 = plan_patch({"path": rel, "new_content": ""})
        out3 = apply_run(json.dumps(pp2))
        # allow either ok: updated or delete mode message depending on implementation
        self.assertTrue("ok: 1 file(s) updated" in out3 or "mode\":\"delete\"" in out3)
        self.assertFalse(p.exists())

    def test_create_conflict(self):
        from tools.edit.plan_patch import plan_patch
        from tools.edit.apply_patch import run as apply_run

        p = self.tmp_dir / "e2e_conflict.txt"
        rel = str(p.relative_to(self.root))
        if p.exists():
            p.unlink()
        plan = plan_patch({"path": rel, "new_content": "hello\n"})
        # file appears by external actor
        p.write_text("external\n", encoding="utf-8")
        out = apply_run(json.dumps(plan))
        self.assertIn("conflict", out)

    def test_exec_bit_preserved(self):
        import os, stat
        from tools.edit.plan_patch import plan_patch
        from tools.edit.apply_patch import run as apply_run
        sh = self.tmp_dir / "e2e_tool.sh"
        rel = str(sh.relative_to(self.root))
        sh.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
        os.chmod(sh, os.stat(sh).st_mode | stat.S_IXUSR)
        plan = plan_patch({"path": rel, "new_content": "#!/bin/sh\necho hi!\n"})
        out = apply_run(json.dumps(plan))
        mode = os.stat(sh).st_mode
        self.assertTrue(mode & stat.S_IXUSR)

    def test_crlf_bom_roundtrip(self):
        from tools.edit.plan_patch import plan_patch
        from tools.edit.apply_patch import run as apply_run
        f = self.tmp_dir / "e2e_crlf.txt"
        rel = str(f.relative_to(self.root))
        # write CRLF
        f.write_bytes(b"a\r\nb\r\n")
        # append line with CRLF
        new = "a\r\nb\r\nc\r\n"
        plan = plan_patch({"path": rel, "new_content": new})
        out = apply_run(json.dumps(plan))
        self.assertIn("ok: 1 file(s) updated", out)
        # plan again with same content should be no_changes
        same = plan_patch({"path": rel, "new_content": new})
        self.assertTrue(same.get("no_changes"))


if __name__ == "__main__":
    unittest.main()
