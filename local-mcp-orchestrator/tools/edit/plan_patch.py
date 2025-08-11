from __future__ import annotations

import json
import io
import difflib
from pathlib import Path
import hashlib
import os
import difflib
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parents[2]

MAX_BYTES = 2_000_000
EXCLUDES = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}


def _safe_path(rel_path: str) -> Path:
    p = (ROOT_DIR / rel_path).resolve()
    if not str(p).startswith(str(ROOT_DIR)):
        raise ValueError("path escapes workspace")
    return p


def _read_text_safe(p: Path) -> str:
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return p.read_text(errors="ignore")


def _is_binary(b: bytes) -> bool:
    return b"\x00" in b


def make_unified_diff(path: str, new_content: str, context: int = 3) -> str:
    p = _safe_path(path)
    exists = p.exists()
    old = _read_text_safe(p)
    old_lines = old.splitlines(keepends=True)
    new_lines = (new_content or "").splitlines(keepends=True)

    fromfile = f"a/{path}" if exists else "/dev/null"
    tofile = f"b/{path}" if new_content != "" else "/dev/null"
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=fromfile, tofile=tofile, n=context)
    return "".join(diff)


def plan_patch(payload: dict) -> dict:
    rel = payload["path"]
    new_text: str = payload.get("new_content", "")
    ctx = int(payload.get("context", 3))

    # path safety
    root = os.path.realpath(str(ROOT_DIR))
    tgt = os.path.realpath(os.path.join(root, rel))
    if os.path.commonpath([root, tgt]) != root:
        return {"error": "path escapes workspace"}

    p = Path(tgt)
    exists = p.exists()
    base_b = p.read_bytes() if exists else b""
    new_b = new_text.encode("utf-8", "surrogatepass")
    if len(base_b) > MAX_BYTES or len(new_b) > MAX_BYTES:
        return {"error": "file too large"}
    if _is_binary(base_b) or _is_binary(new_b):
        return {"error": "binary file not supported"}

    base_text = base_b.decode("utf-8", errors="surrogatepass") if exists else ""
    base_hash = hashlib.sha256(base_b).hexdigest() if exists else None

    if not exists and new_text == "":
        return {"path": rel, "base_hash": None, "diff": "", "no_changes": True}

    if exists and base_text == new_text:
        return {"path": rel, "base_hash": base_hash, "diff": "", "no_changes": True}

    fromfile = f"a/{rel}" if exists else "/dev/null"
    tofile = f"b/{rel}" if new_text != "" else "/dev/null"
    diff_lines = list(difflib.unified_diff(
        base_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=fromfile, tofile=tofile, n=ctx,
    ))
    return {"path": rel, "base_hash": base_hash, "diff": "".join(diff_lines), "no_changes": False}


def run(input_str: str) -> str:
    """Plan patch wrapper. Input JSON -> Output JSON string."""
    try:
        obj = json.loads(input_str)
    except Exception as e:
        return f"[plan_patch] bad input: {type(e).__name__}: {e}"
    try:
        out = plan_patch(obj)
        return json.dumps(out, ensure_ascii=False)
    except Exception as e:
        return f"[plan_patch] failed: {type(e).__name__}: {e}"


if __name__ == "__main__":
    print(run(json.dumps({"path": "tmp/example.txt", "new_content": "hello\n"})))
