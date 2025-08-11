from __future__ import annotations

import subprocess
from typing import Optional


def run(code: str, timeout: int = 10) -> str:
    """Execute short Python code in a subprocess and return combined output.

    - Time-limited via `timeout`.
    - Returns both stdout and stderr.
    - Truncates long outputs.
    """
    code = (code or "").strip()
    if not code:
        return "[code_exec] empty code"

    try:
        proc = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"[code_exec] timeout after {timeout}s"
    except Exception as e:  # pragma: no cover
        return f"[code_exec] failed: {type(e).__name__}: {e}"

    out = (proc.stdout or "")
    err = (proc.stderr or "")
    rc = proc.returncode

    combined = "".join([
        f"[code_exec] returncode={rc}\n",
        ("[stdout]\n" + out if out else ""),
        ("[stderr]\n" + err if err else ""),
    ]).strip()

    # Truncate if extremely long
    if len(combined) > 4000:
        combined = combined[:4000] + "\n…(truncated)"
    return combined


if __name__ == "__main__":
    print(run("print('hello from code_exec')"))

