from __future__ import annotations

import subprocess
import json
from typing import Dict, Any


def python_pyright(project_root: str = ".") -> Dict[str, Any]:
    try:
        proc = subprocess.run(["pyright", "--outputjson"], cwd=project_root, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return {"error": "pyright not installed"}
    stdout = proc.stdout or ""
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {"error": "pyright output parse error", "stdout": stdout, "stderr": proc.stderr}
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
    return {"framework": "pyright", "diagnostics": diags}

