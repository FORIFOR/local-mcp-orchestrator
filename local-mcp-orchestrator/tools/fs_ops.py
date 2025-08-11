from __future__ import annotations

from pathlib import Path
from typing import List


ROOT_DIR = Path(__file__).resolve().parents[1]


def _safe_path(rel_path: str) -> Path:
    p = (ROOT_DIR / rel_path).resolve()
    if not str(p).startswith(str(ROOT_DIR)):
        raise ValueError("path escapes workspace")
    return p


def read_file(path: str) -> str:
    p = _safe_path(path)
    if not p.exists():
        return f"[fs.read] not found: {path}"
    if p.is_dir():
        return f"[fs.read] is directory: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"[fs.read] error: {type(e).__name__}: {e}"


def write_file(path: str, content: str, make_dirs: bool = True) -> str:
    p = _safe_path(path)
    try:
        if make_dirs:
            p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[fs.write] ok: {path} ({len(content)} bytes)"
    except Exception as e:
        return f"[fs.write] error: {type(e).__name__}: {e}"


def append_file(path: str, content: str, make_dirs: bool = True) -> str:
    p = _safe_path(path)
    try:
        if make_dirs:
            p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(content)
        return f"[fs.append] ok: {path} (+{len(content)} bytes)"
    except Exception as e:
        return f"[fs.append] error: {type(e).__name__}: {e}"


def delete_path(path: str) -> str:
    p = _safe_path(path)
    try:
        if p.is_dir():
            # Only remove empty dir to avoid big mistakes; agent can remove files first.
            p.rmdir()
            return f"[fs.delete] removed dir: {path}"
        if p.exists():
            p.unlink()
            return f"[fs.delete] removed file: {path}"
        return f"[fs.delete] not found: {path}"
    except Exception as e:
        return f"[fs.delete] error: {type(e).__name__}: {e}"


def list_dir(path: str = ".", recursive: bool = False) -> str:
    p = _safe_path(path)
    if not p.exists():
        return f"[fs.ls] not found: {path}"
    if not p.is_dir():
        return f"[fs.ls] not a directory: {path}"

    def fmt(entry: Path) -> str:
        rel = entry.relative_to(ROOT_DIR)
        kind = "d" if entry.is_dir() else "f"
        size = entry.stat().st_size if entry.is_file() else 0
        return f"{kind} {rel} {size}"

    results: List[str] = []
    if recursive:
        for e in p.rglob("*"):
            results.append(fmt(e))
    else:
        for e in p.iterdir():
            results.append(fmt(e))
    return "\n".join(sorted(results))


def make_dirs(path: str) -> str:
    p = _safe_path(path)
    try:
        p.mkdir(parents=True, exist_ok=True)
        return f"[fs.mkdir] ok: {path}"
    except Exception as e:
        return f"[fs.mkdir] error: {type(e).__name__}: {e}"

