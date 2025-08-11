from __future__ import annotations

import io
import re
from pathlib import Path
from typing import List, Tuple
import os
import json
import hashlib
import tempfile
import errno


ROOT_DIR = Path(__file__).resolve().parents[2]


def _safe_path(rel_path: str) -> Path:
    root = os.path.realpath(str(ROOT_DIR))
    tgt = os.path.realpath(os.path.join(root, rel_path))
    # commonpath raises on different drives; we normalize both under root
    if os.path.commonpath([root, tgt]) != root:
        raise ValueError("path escapes workspace (symlink/traversal)")
    return Path(tgt)


_RE_HUNK = re.compile(r"^@@ -(?P<a_start>\d+)(,(?P<a_count>\d+))? \+(?P<b_start>\d+)(,(?P<b_count>\d+))? @@")


class PatchError(Exception):
    pass


def _parse_file_header(lines: List[str], i: int) -> Tuple[str, str, int]:
    if i >= len(lines) or not lines[i].startswith('--- '):
        raise PatchError("expected --- header")
    a_path = lines[i][4:].strip()
    i += 1
    if i >= len(lines) or not lines[i].startswith('+++ '):
        raise PatchError("expected +++ header")
    b_path = lines[i][4:].strip()
    i += 1
    return a_path, b_path, i


def _apply_hunks_to_text(orig_lines: List[str], hunks: List[List[str]], a_start_first: int) -> List[str]:
    out: List[str] = []
    idx = 0  # 0-based index into orig_lines
    # Copy until first hunk start (a_start_first is 1-based)
    pre = max(a_start_first - 1, 0)
    out.extend(orig_lines[:pre])
    idx = pre
    for h in hunks:
        for hl in h:
            if not hl:
                continue
            tag = hl[0]
            text = hl[1:]
            if tag == ' ':
                # context line, must match
                if idx >= len(orig_lines) or orig_lines[idx] != text:
                    raise PatchError("context mismatch while applying hunk")
                out.append(orig_lines[idx])
                idx += 1
            elif tag == '-':
                # removal, must match original
                if idx >= len(orig_lines) or orig_lines[idx] != text:
                    raise PatchError("deletion mismatch while applying hunk")
                idx += 1
            elif tag == '+':
                # addition
                out.append(text)
            else:
                raise PatchError("invalid hunk line")
    # Append the remainder
    out.extend(orig_lines[idx:])
    return out


def _atomic_write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # write to a temp file in the same directory and replace
    # newline='' preserves line endings in data as-is (no translation)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='', dir=str(path.parent), delete=False) as tf:
        tmp_name = tf.name
        tf.write(data)
        tf.flush()
        os.fsync(tf.fileno())
    os.replace(tmp_name, str(path))


def apply_unified_diff(diff_text: str, dry_run: bool = False, base_hash: str = "", target_path: str = "") -> str:
    """Apply a minimal unified diff to files under ROOT_DIR.

    Limitations: no renames; expects same relative path in a/b headers; does not
    handle binary patches; simple hunk application with strict context checks.
    """
    lines = diff_text.splitlines(keepends=True)
    i = 0
    changed: List[str] = []
    processed_files = 0
    if not lines:
        return "[apply_patch] empty diff"

    while i < len(lines):
        # Skip empty lines
        if not lines[i].strip():
            i += 1
            continue
        a_path, b_path, i = _parse_file_header(lines, i)
        processed_files += 1
        if processed_files > 1:
            raise PatchError("multi-file diff not supported; split per file and re-apply")
        # Normalize paths (strip a/ and b/ prefixes), handle /dev/null
        def _norm(h: str):
            if h == '/dev/null':
                return None
            return h[2:] if h.startswith(('a/', 'b/')) else h
        a_rel = _norm(a_path)
        b_rel = _norm(b_path)
        if a_rel is not None and b_rel is not None and a_rel != b_rel:
            raise PatchError("renames not supported in this minimal applier")
        rel = b_rel if b_rel is not None else a_rel
        if rel is None or rel.startswith('/'):  # absolute forbidden or cannot infer
            raise PatchError("absolute paths not allowed")
        target = _safe_path(rel)

        # Collect hunks for this file
        hunks: List[List[str]] = []
        a_start_first = 1
        while i < len(lines) and lines[i].startswith('@@ '):
            m = _RE_HUNK.match(lines[i])
            if not m:
                raise PatchError("bad hunk header")
            if not hunks:
                a_start_first = int(m.group('a_start'))
            i += 1
            h: List[str] = []
            while i < len(lines):
                if lines[i].startswith(('--- ', '+++ ', '@@ ')):
                    break
                if not lines[i]:
                    break
                tag = lines[i][0]
                if tag in (' ', '+', '-'):
                    h.append(lines[i])
                    i += 1
                else:
                    # end of hunk (unexpected tag)
                    break
            hunks.append(h)
        # Handle create/delete/modify
        if a_rel is None and b_rel is not None:
            # Create new file: apply hunks to empty original
            orig_lines: List[str] = []
            new_lines = _apply_hunks_to_text(orig_lines, hunks, a_start_first)
            new_text = "".join(new_lines)
            if target.exists():
                raise PatchError("conflict: file appeared since plan")
            if not dry_run:
                _atomic_write_text(target, new_text)
            changed.append(str(target.relative_to(ROOT_DIR)))
        elif b_rel is None and a_rel is not None:
            # Delete existing file
            if target.exists():
                if not base_hash:
                    raise PatchError("delete requires base_hash (or force=true)")
                # optimistic lock on delete if applicable; compare raw bytes like planner
                if base_hash and target_path and target_path == str(target.relative_to(ROOT_DIR)):
                    try:
                        now_hash = hashlib.sha256(target.read_bytes()).hexdigest()
                    except Exception:
                        # fallback to text read if bytes fail unexpectedly
                        now_hash = hashlib.sha256(target.read_text(errors='ignore').encode()).hexdigest()
                    if now_hash != base_hash:
                        raise PatchError("conflict: file changed since plan (base_hash mismatch)")
                if not dry_run:
                    target.unlink()
                changed.append(str(target.relative_to(ROOT_DIR)))
        else:
            # Modify existing file
            if target.exists():
                try:
                    # Preserve original line endings (CRLF/LF) to match diff hunks
                    with open(target, 'r', encoding='utf-8', newline='') as f:
                        orig = f.read()
                except Exception:
                    orig = target.read_text(errors='ignore')
            else:
                orig = ""
            # optimistic lock for modifies
            if base_hash and target_path and target_path == str(target.relative_to(ROOT_DIR)):
                # compare raw bytes to align with planner's hashing and preserve CRLF/BOM semantics
                try:
                    now_hash = hashlib.sha256(target.read_bytes()).hexdigest()
                except Exception:
                    now_hash = hashlib.sha256(orig.encode()).hexdigest()
                if now_hash != base_hash:
                    raise PatchError("conflict: file changed since plan (base_hash mismatch)")
            orig_lines = orig.splitlines(keepends=True)
            new_lines = _apply_hunks_to_text(orig_lines, hunks, a_start_first)
            new_text = "".join(new_lines)
            if not dry_run:
                # preserve mode (exec bit etc.)
                try:
                    old_mode = os.stat(target).st_mode
                except FileNotFoundError:
                    old_mode = None
                _atomic_write_text(target, new_text)
                if old_mode is not None:
                    try:
                        os.chmod(target, old_mode)
                    except Exception:
                        pass
            changed.append(str(target.relative_to(ROOT_DIR)))

        # Skip until next file header or end
        while i < len(lines) and not lines[i].startswith('--- '):
            i += 1

    return f"[apply_patch] ok: {len(changed)} file(s) updated\n" + "\n".join(changed)


def run(input_payload: str) -> str:
    payload = (input_payload or "").strip()
    if not payload:
        return "[apply_patch] empty diff"
    base_hash = ""
    target_rel = ""
    # Accept either raw diff or JSON {diff, base_hash?, path?}
    if payload.startswith('{'):
        try:
            obj = json.loads(payload)
            diff_text = obj.get("diff") or ""
            base_hash = (obj.get("base_hash") or "")
            target_rel = (obj.get("path") or "")
            if not diff_text.strip():
                return "[apply_patch] empty diff"
        except Exception as e:
            return f"[apply_patch] bad input: {type(e).__name__}: {e}"
    else:
        diff_text = payload
    # derive mode and counts for structured footer
    def _parse_mode_and_counts(diff_text: str):
        mode = "modify"
        path = ""
        added = 0
        removed = 0
        hunks_meta = []
        lines = diff_text.splitlines()
        for idx, ln in enumerate(lines):
            if ln.startswith('--- '):
                from_hdr = ln[4:].strip()
                to_hdr = lines[idx+1][4:].strip() if idx+1 < len(lines) and lines[idx+1].startswith('+++ ') else ''
                if from_hdr == '/dev/null' and to_hdr:
                    mode = 'create'
                    path = to_hdr[2:] if to_hdr.startswith('b/') else to_hdr
                elif to_hdr == '/dev/null' and from_hdr:
                    mode = 'delete'
                    path = from_hdr[2:] if from_hdr.startswith('a/') else from_hdr
                else:
                    path = to_hdr[2:] if to_hdr.startswith('b/') else to_hdr
            elif ln.startswith('@@ '):
                m = _RE_HUNK.match(ln + '\n') or _RE_HUNK.match(ln)
                if m:
                    a_start = int(m.group('a_start'))
                    a_count = int(m.group('a_count') or 0)
                    b_start = int(m.group('b_start'))
                    b_count = int(m.group('b_count') or 0)
                    hunks_meta.append({
                        'a_start': a_start,
                        'a_count': a_count,
                        'b_start': b_start,
                        'b_count': b_count,
                    })
            elif ln.startswith('+') and not ln.startswith('+++'):
                added += 1
            elif ln.startswith('-') and not ln.startswith('---'):
                removed += 1
        return mode, path, added, removed, hunks_meta
    try:
        status = apply_unified_diff(diff_text, dry_run=False, base_hash=base_hash, target_path=target_rel)
        mode, pth, added, removed, hunks_meta = _parse_mode_and_counts(diff_text)
        # compute hash_after
        hash_after = None
        if mode in ("create", "modify") and pth:
            try:
                tgt = _safe_path(pth)
                hash_after = hashlib.sha256(tgt.read_bytes()).hexdigest() if tgt.exists() else None
            except Exception:
                hash_after = None
        footer = json.dumps({
            "mode": mode,
            "path": pth or target_rel,
            "hash_after": hash_after,
            "lines_added": added,
            "lines_removed": removed,
            "strategy": "unified_diff",
            "hunks": hunks_meta,
        }, ensure_ascii=False)
        return f"{status}\n{footer}"
    except Exception as e:
        return f"[apply_patch] failed: {type(e).__name__}: {e}"


if __name__ == "__main__":
    print("Self-test is minimal; prefer unit tests.")
