from __future__ import annotations

import json
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]

EXCLUDES = [
    "-g", "!.git",
    "-g", "!node_modules",
    "-g", "!.venv",
    "-g", "!__pycache__",
    "-g", "!dist",
    "-g", "!build",
]


@dataclass
class ScanInput:
    query: str
    limit: int = 100
    mode: str = "literal"  # literal | regex | word
    context: int = 2
    pyright: Dict[str, Any] | None = None  # optional env/options


def _rg_mode_flags(mode: str) -> List[str]:
    m = (mode or "literal").lower()
    if m == "regex":
        return ["-S"]
    if m == "word":
        return ["-S", "-w", "-F"]
    # default literal
    return ["-S", "-F"]


def _rg_search(inp: ScanInput) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    q = (inp.query or "").strip()
    if not q:
        return [], {"error": "empty query"}
    try:
        cmd = [
            "rg", "-n", "--no-heading", "--hidden",
            *_rg_mode_flags(inp.mode),
            *EXCLUDES,
            q, ".",
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return [], {"error": "ripgrep (rg) not installed", "installed": False}

    hits: List[Dict[str, Any]] = []
    for line in (proc.stdout or "").splitlines():
        try:
            path, line_no, text = line.split(":", 2)
            hits.append({"path": path, "line": int(line_no), "text": text.rstrip("\n")})
            if len(hits) >= inp.limit:
                break
        except ValueError:
            continue
    return hits, {"installed": True, "mode": inp.mode, "context": inp.context}


def _add_context(hits: List[Dict[str, Any]], context: int) -> None:
    if context <= 0 or not hits:
        return
    # group hits by file for efficient reads
    by_file: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for h in hits:
        by_file[h["path"]].append(h)
    for path, items in by_file.items():
        try:
            with open(Path(ROOT_DIR) / path, "r", encoding="utf-8", errors="ignore", newline="") as f:
                lines = f.read().splitlines()
        except Exception:
            lines = []
        n = len(lines)
        for h in items:
            ln = h.get("line", 0)
            a = max(0, ln - 1 - context)
            b = min(n, ln + context)
            before = lines[a: max(0, ln - 1)] if n else []
            after = lines[min(n, ln): b] if n else []
            if before:
                h["context_before"] = before
            if after:
                h["context_after"] = after


def _run_pyright_on(files: List[str], opts: Dict[str, Any] | None) -> Dict[str, Any]:
    # only consider python files
    py_files = [f for f in files if f.endswith(".py")]
    used: Dict[str, Any] = {}
    if opts:
        # pass through reported env options for transparency
        for k in ("pythonVersion", "venvPath", "venv"):
            if k in opts:
                used[k] = opts[k]
    try:
        if not py_files:
            return {"used": used, "diagnostics": []}
        # If pyright not present, clean skip
        proc = subprocess.run(["pyright", "--outputjson", *py_files], cwd=str(ROOT_DIR), capture_output=True, text=True)
    except FileNotFoundError:
        used.update({"installed": False})
        return {"error": "pyright not installed", "used": used, "diagnostics": []}
    used.update({"installed": True})
    stdout = proc.stdout or ""
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {"error": "pyright output parse error", "used": used, "stdout": stdout, "stderr": proc.stderr}
    diags = []
    for d in data.get("generalDiagnostics", []):
        rng = d.get("range") or {}
        start = (rng.get("start") or {})
        diags.append({
            "path": d.get("file"),
            "line": start.get("line"),
            "col": start.get("character"),
            "severity": d.get("severity"),
            "message": d.get("message"),
            "rule": d.get("rule"),
        })
    return {"used": used, "diagnostics": diags}


def impact_scan(payload: Dict[str, Any]) -> Dict[str, Any]:
    inp = ScanInput(
        query=(payload.get("query") or ""),
        limit=int(payload.get("limit", 100) or 100),
        mode=str(payload.get("mode", "literal") or "literal"),
        context=int(payload.get("context", 2) or 2),
        pyright=payload.get("pyright"),
    )

    hits, rg_used = _rg_search(inp)
    out: Dict[str, Any] = {"hits": hits, "files_ranked": [], "suggestions": [], "used": {"ripgrep": rg_used}}
    if rg_used.get("error"):
        out["error"] = rg_used["error"]
        return out

    # add context lines
    _add_context(hits, inp.context)

    # rank files by frequency
    counts = Counter(h["path"] for h in hits)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    out["files_ranked"] = [{"path": p, "score": c} for p, c in ranked]

    # optional pyright on top-N python files
    py_files = [p for p, _ in ranked if p.endswith(".py")][:20]
    if py_files:
        pry = _run_pyright_on(py_files, inp.pyright or {})
        out["used"]["pyright"] = pry.get("used", {"installed": False})
        if pry.get("error"):
            out["used"]["pyright"]["error"] = pry["error"]
        out["pyright_diagnostics"] = pry.get("diagnostics", [])

    # suggestions
    total = len(hits)
    nfiles = len(counts)
    if total:
        top = ", ".join(f"{p} ({c})" for p, c in ranked[:3])
        out["suggestions"].append(f"Found {total} matches across {nfiles} files. Top: {top}")
    if out.get("pyright_diagnostics"):
        sev_counts = Counter(d.get("severity") for d in out["pyright_diagnostics"])
        sev_str = ", ".join(f"{k}:{v}" for k, v in sev_counts.items())
        out["suggestions"].append(f"Pyright diagnostics in matched files: {sev_str}")
    elif py_files:
        # if we attempted pyright but got none/skip
        pry_used = out["used"].get("pyright", {})
        if not pry_used.get("installed"):
            out["suggestions"].append("Pyright not installed; skipped diagnostics on matched Python files.")

    return out


def run(input_str: str) -> str:
    try:
        payload = json.loads(input_str)
    except Exception as e:
        return json.dumps({"error": f"bad input: {type(e).__name__}: {e}"}, ensure_ascii=False)
    try:
        out = impact_scan(payload)
        return json.dumps(out, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"failed: {type(e).__name__}: {e}"}, ensure_ascii=False)


if __name__ == "__main__":
    print(run(json.dumps({"query": "def ", "limit": 20, "mode": "regex", "context": 1})))

