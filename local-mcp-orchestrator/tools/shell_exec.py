from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def run(cmd: str, timeout: int = 20) -> str:
    """Run a shell command safely within the workspace.

    - Executes with cwd at project root.
    - Uses shlex.split to avoid shell injection; no shell=True.
    - Captures stdout/stderr; applies timeout and truncation.
    """
    cmd = (cmd or "").strip()
    if not cmd:
        return "[sh] empty command"

    try:
        args = shlex.split(cmd)
    except Exception as e:
        return f"[sh] parse error: {type(e).__name__}: {e}"

    try:
        proc = subprocess.run(
            args,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"[sh] timeout after {timeout}s"
    except FileNotFoundError:
        return f"[sh] command not found: {args[0]}"
    except Exception as e:
        return f"[sh] failed: {type(e).__name__}: {e}"

    out = (proc.stdout or "")
    err = (proc.stderr or "")
    rc = proc.returncode

    combined = "".join([
        f"[sh] returncode={rc}\n",
        ("[stdout]\n" + out if out else ""),
        ("[stderr]\n" + err if err else ""),
    ]).strip()

    if len(combined) > 6000:
        combined = combined[:6000] + "\n…(truncated)"
    return combined

