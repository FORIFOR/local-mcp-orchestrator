#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory


MODEL_PATH = \
    "/Users/saiteku/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf"


def _llama_fallback(prompt: str) -> str:
    try:
        from llama_cpp import Llama
    except Exception as e:  # pragma: no cover
        return f"[fallback:llama_cpp] import failed: {type(e).__name__}: {e}"

    model_path = MODEL_PATH
    if os.path.islink("model.gguf") or os.path.isfile("model.gguf"):
        model_path = os.path.abspath("model.gguf")

    try:
        llm = Llama(model_path=model_path, n_ctx=4096, verbose=False)
        out = llm("""SYSTEM: You are a helpful assistant.\nUSER: {prompt}\nASSISTANT:""".format(prompt=prompt), max_tokens=400)
        # llama-cpp-python returns various shapes depending on version
        txt = out.get("choices", [{}])[0].get("text") or str(out)
        return txt.strip()
    except Exception as e:  # pragma: no cover
        return f"[fallback:llama_cpp] inference failed: {type(e).__name__}: {e}"


def ask_via_mcp(prompt: str) -> Optional[str]:
    try:
        from utils.mcp_client import ask_via_mcp as _ask
    except Exception:
        return None

    try:
        return _ask(prompt, server_command=os.environ.get("MCP_SERVER_CMD", "mcp-server"), config_path=os.environ.get("MCP_CONFIG", "mcp-server.yaml"))
    except Exception:
        return None


def main() -> int:
    print("[cli_chat] starting. Type 'exit' to quit. Using MCP if available.")
    history = FileHistory(".cli_chat_history")
    session = PromptSession(history=history)

    while True:
        try:
            text = session.prompt(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if text is None:
            continue
        text = text.strip()
        if text.lower() in {"exit", "quit", ":q"}:
            break
        if not text:
            continue

        # Try MCP first
        resp = ask_via_mcp(text)
        if resp:
            print(resp)
            continue

        # Fallback to local llama_cpp
        print(_llama_fallback(text))

    print("[cli_chat] bye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
