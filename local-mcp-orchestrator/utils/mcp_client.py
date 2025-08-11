from __future__ import annotations

import asyncio
from typing import Optional
import os
import shlex


class MCPUnavailable(Exception):
    pass


async def _try_mcp_once(prompt: str, server_command: str, config_path: str) -> Optional[str]:
    """Attempt a minimal MCP stdio roundtrip.

    This function is intentionally conservative and may need adjustments for
    your specific MCP server/client implementation.
    """
    try:
        # The official Python SDK evolved; these imports may differ by version.
        from mcp.client.stdio import stdio_client
        from mcp.client.session import ClientSession
        from mcp.types import InitializeRequest
    except Exception as e:  # pragma: no cover
        raise MCPUnavailable(f"mcp client not available: {e}")

    # Build args from env if provided, else default to --config path
    args_env = os.environ.get("MCP_ARGS", "").strip()
    if args_env:
        args = shlex.split(args_env)
    else:
        args = ["--config", config_path]

    # Start server via stdio
    async with stdio_client(command=server_command, args=args) as (read, write):
        session = ClientSession(read, write)
        await session.initialize()

        # Minimal prompt-completion API differs per server.
        # Here we try a generic 'completion' or 'chat' tool; adjust as needed.
        try:
            # Some servers expose a simple tool-like call.
            result = await session.call_tool("completion", {"prompt": prompt})
            if result and isinstance(result, dict):
                text = result.get("text") or result.get("completion")
                if text:
                    return text
        except Exception:
            pass

        # Fallback: if the server exposes 'chat' interface
        try:
            result = await session.call_tool("chat", {"messages": [{"role": "user", "content": prompt}]})
            if result and isinstance(result, dict):
                text = result.get("text") or result.get("content")
                if isinstance(text, list):
                    text = "\n".join(map(str, text))
                if text:
                    return text
        except Exception:
            pass

        # If no generic tool exists, nothing to return.
        return None


def ask_via_mcp(prompt: str, server_command: str = "mcp-server", config_path: str = "mcp-server.yaml", timeout: int = 30) -> Optional[str]:
    """Sync wrapper to ask via MCP stdio server.

    Returns response text, or None if unsupported. Raises MCPUnavailable if
    mcp client package is missing.
    """
    try:
        return asyncio.run(asyncio.wait_for(_try_mcp_once(prompt, server_command, config_path), timeout=timeout))
    except MCPUnavailable:
        raise
    except Exception:
        return None
