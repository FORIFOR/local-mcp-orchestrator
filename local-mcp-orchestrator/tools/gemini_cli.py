from __future__ import annotations

import shlex
import subprocess


def run(prompt: str, timeout: int = 30) -> str:
    prompt = (prompt or "").strip()
    if not prompt:
        return "[gemini] empty prompt"
    try:
        # Expect a local `gemini` CLI available in PATH
        # Example: gemini -p "<prompt>"
        args = ["gemini", "-p", prompt]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode != 0:
            return f"[gemini] returncode={proc.returncode}\n{err or out}"
        return out or "[gemini] (no output)"
    except FileNotFoundError:
        return "[gemini] CLI not found. Install a `gemini` CLI and ensure it is in PATH."
    except subprocess.TimeoutExpired:
        return f"[gemini] timeout after {timeout}s"
    except Exception as e:
        return f"[gemini] failed: {type(e).__name__}: {e}"

