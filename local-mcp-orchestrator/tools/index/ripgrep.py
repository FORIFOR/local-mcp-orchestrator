from __future__ import annotations

import subprocess
from typing import Dict, Any

EXCLUDES = [
    "-g", "!.git",
    "-g", "!node_modules",
    "-g", "!.venv",
    "-g", "!__pycache__",
    "-g", "!dist",
    "-g", "!build",
]


def search(q: str, limit: int = 200) -> Dict[str, Any]:
    q = (q or "").strip()
    if not q:
        return {"error": "empty query"}
    try:
        cmd = ["rg", "-n", "-S", "--no-heading", "--hidden", *EXCLUDES, q, "."]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return {"error": "ripgrep (rg) not installed"}

    hits = []
    for line in (proc.stdout or "").splitlines():
        try:
            path, line_no, text = line.split(":", 2)
            hits.append({"path": path, "line": int(line_no), "text": text.strip()})
            if len(hits) >= limit:
                break
        except ValueError:
            continue
    return {"hits": hits, "tool": "ripgrep"}

