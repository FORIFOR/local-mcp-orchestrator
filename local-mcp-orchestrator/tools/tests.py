from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import json
import re

ROOT_DIR = Path(__file__).resolve().parents[1]


def _summarize(framework: str, rc: int, out: str, err: str) -> str:
    data = {
        "framework": framework,
        "returncode": rc,
        "summary": {},
        "stdout": out,
        "stderr": err,
    }
    text = out + "\n" + err
    # naive parses
    if framework == "pytest":
        m = re.findall(r"(\d+) passed| (\d+) failed| (\d+) skipped| (\d+) error", text)
        # not robust; keep raw output too
    else:
        m = re.search(r"Ran (\d+) tests? in ([0-9\.]+)s", text)
        if m:
            data["summary"]["collected"] = int(m.group(1))
            data["summary"]["duration_sec"] = float(m.group(2))
        data["summary"]["ok"] = (rc == 0)
    return json.dumps(data, ensure_ascii=False)


def run(kind: str = "auto", timeout: int = 60) -> str:
    """Run project tests and return combined output.

    - kind="pytest" forces pytest; kind="unittest" forces unittest; kind="auto" tries pytest then unittest.
    """
    def _run(cmd):
        try:
            proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return f"[tests] timeout after {timeout}s"
        out = proc.stdout or ""
        err = proc.stderr or ""
        return f"[tests] returncode={proc.returncode}\n" + ("[stdout]\n" + out if out else "") + ("[stderr]\n" + err if err else "")

    if kind == "pytest" or (kind == "auto" and shutil.which("pytest")):
        res = _run(["pytest", "-q"])
        # parse header: first line includes returncode
        lines = res.splitlines()
        rc = 0
        if lines and lines[0].startswith('[tests] returncode='):
            try:
                rc = int(lines[0].split('=')[1])
            except Exception:
                rc = 1
        out = res.split('[stdout]\n',1)[1] if '[stdout]\n' in res else ''
        err = res.split('[stderr]\n',1)[1] if '[stderr]\n' in res else ''
        return _summarize("pytest", rc, out, err)
    # fallback to unittest
    res = _run(["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py", "-v"])  # verbose
    lines = res.splitlines()
    rc = 0
    if lines and lines[0].startswith('[tests] returncode='):
        try:
            rc = int(lines[0].split('=')[1])
        except Exception:
            rc = 1
    out = res.split('[stdout]\n',1)[1] if '[stdout]\n' in res else ''
    err = res.split('[stderr]\n',1)[1] if '[stderr]\n' in res else ''
    return _summarize("unittest", rc, out, err)


if __name__ == "__main__":
    print(run("auto"))
