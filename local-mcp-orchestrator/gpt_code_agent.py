#!/usr/bin/env python3
from __future__ import annotations

import os
import json
from typing import Any, Optional
import argparse

from tools import web_search_run, code_exec_run, tests_run, plan_patch_run, apply_patch_run, ripgrep_search, lsp_python_pyright, impact_scan_run
from tools.fs_ops import read_file, write_file, append_file, delete_path, list_dir, make_dirs
from tools.shell_exec import run as shell_run
from tools.gemini_cli import run as gemini_run
from utils.mcp_client import ask_via_mcp


MODEL_PATH = \
    "/Users/saiteku/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf"

_NATIVE_LLAMA = None  # cache for direct chat


def _try_build_langchain_agent() -> Optional[Any]:
    try:
        from langchain.tools import Tool, StructuredTool
        from langchain.agents import AgentType, initialize_agent
        from langchain_community.llms import LlamaCpp
        from langchain.memory import ConversationBufferMemory
        from pydantic import BaseModel, Field
    except Exception as e:
        print(f"[gpt_code_agent] LangChain/LLM unavailable: {type(e).__name__}: {e}")
        return None

    def build_llm() -> Optional[LlamaCpp]:
        model_path = MODEL_PATH
        if os.path.islink("model.gguf") or os.path.isfile("model.gguf"):
            model_path = os.path.abspath("model.gguf")
        if not os.path.isfile(model_path):
            print(f"[gpt_code_agent] model not found: {model_path}")
            return None
        return LlamaCpp(model_path=model_path, n_ctx=4096, temperature=0.2, max_tokens=768, verbose=False)

    def _fs_write_adapter(s: str) -> str:
        try:
            obj = json.loads(s)
            return write_file(obj["path"], obj.get("content", ""), make_dirs=True)
        except Exception as e:
            return f"[FS.Write] bad input: {e}"

    def _fs_append_adapter(s: str) -> str:
        try:
            obj = json.loads(s)
            return append_file(obj["path"], obj.get("content", ""), make_dirs=True)
        except Exception as e:
            return f"[FS.Append] bad input: {e}"

    class StrInput(BaseModel):
        input: str = Field(..., description="Single string input")

    # Define wrappers that accept a named 'input' parameter
    def t_websearch(input: str) -> str:
        return web_search_run(input, max_results=5)

    def t_pyexec(input: str) -> str:
        return code_exec_run(input, timeout=12)

    def t_fs_read(input: str) -> str:
        return read_file(input)

    def t_fs_write(input: str) -> str:
        return _fs_write_adapter(input)

    def t_fs_append(input: str) -> str:
        return _fs_append_adapter(input)

    def t_fs_delete(input: str) -> str:
        return delete_path(input)

    def t_fs_list(input: str) -> str:
        return list_dir((input or "."), recursive=False)

    def t_fs_list_all(input: str) -> str:
        base = (input or ".").strip() or "."
        listing = list_dir(base, recursive=True)
        if not listing:
            return listing
        # keep only files `f path size`
        lines = []
        for ln in listing.splitlines():
            parts = ln.split(" ", 2)
            if parts and parts[0] == "f":
                # parts[1] is relative path
                lines.append(parts[1])
        return "\n".join(lines)

    def t_fs_mkdir(input: str) -> str:
        return make_dirs(input)

    def t_shell(input: str) -> str:
        return shell_run(input, timeout=20)

    def t_tests(input: str) -> str:
        kind = (input or "auto").strip() or "auto"
        return tests_run(kind, timeout=90)

    def t_plan_patch(input: str) -> str:
        return plan_patch_run(input)

    def t_apply_patch(input: str) -> str:
        return apply_patch_run(input)

    def t_rg(input: str) -> str:
        import json as _json
        return _json.dumps(ripgrep_search(input), ensure_ascii=False)

    def t_pyright(input: str) -> str:
        import json as _json
        root = (input or ".").strip() or "."
        return _json.dumps(lsp_python_pyright(root), ensure_ascii=False)

    tools: list[Tool] = []
    tools.append(StructuredTool.from_function(func=t_websearch, name="WebSearch", description="Search the web for up-to-date info. Input: query string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_pyexec, name="PyExec", description="Execute short Python code and return output. Input: code string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_read, name="FS.Read", description="Read a text file. Input: relative path from project root as string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_write, name="FS.Write", description="Write/overwrite a text file. Input: JSON string {path, content}.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_append, name="FS.Append", description="Append text to a file. Input: JSON string {path, content}.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_delete, name="FS.Delete", description="Delete a file or empty directory. Input: path string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_list, name="FS.List", description="List files in a directory. Input: path string or '.'", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_mkdir, name="FS.Mkdir", description="Create directories (parents ok). Input: path string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_shell, name="Shell", description="Run a shell command in the project root. Input: full command string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_tests, name="Tests.Run", description="Run tests: input 'auto'|'pytest'|'unittest' (default auto).", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_plan_patch, name="Edit.PlanPatch", description="Plan a patch as unified diff. Input JSON: {path, new_content, context?}" , args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_apply_patch, name="Edit.ApplyPatch", description="Apply a unified diff to the workspace. Input: diff text.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_rg, name="Search.Ripgrep", description="Search code via ripgrep. Input: query string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_pyright, name="LSP.Pyright", description="Python diagnostics via pyright. Input: project root path or '.'", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=lambda input: gemini_run(input, timeout=40), name="Gemini", description="Query the Gemini CLI for web research. Input: query string.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=lambda input: ask_via_mcp(input) or "[mcp] no response", name="MCP.Query", description="Send a prompt to the configured MCP server and return its response.", args_schema=StrInput))
    tools.append(StructuredTool.from_function(func=t_fs_list_all, name="FS.ListAll", description="List all files recursively relative to project root, one per line. Input: path or '.'", args_schema=StrInput))

    SYSTEM_PROMPT = (
        "You are a local code agent (gpt-code). "
        "You can edit files within the project workspace, run shell commands, and iterate to fix errors. "
        "Only operate under the current project directory. Always show what's changed and why. "
        "If the user asks general questions or says hello, answer directly without using tools. "
        "Use tools only when needed for file or shell actions."
    )

    llm = build_llm()
    if llm is None:
        return None
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    try:
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            memory=memory,
            agent_kwargs={"system_message": SYSTEM_PROMPT},
        )
        # keep a reference to raw llm for direct chat fallbacks
        setattr(agent, "_llm_ref", llm)
        print("[gpt_code_agent] LangChain agent ready.")
        return agent
    except Exception as e:
        print(f"[gpt_code_agent] Failed to init agent: {type(e).__name__}: {e}")
        return None


def _fallback_cli() -> int:
    print("[gpt_code_agent:fallback] Starting minimal CLI. Type 'help' for commands. 'exit' to quit.")
    # Optional local llama for chat if available
    _llama = None
    try:
        from llama_cpp import Llama  # type: ignore
        model_path = MODEL_PATH
        if os.path.islink("model.gguf") or os.path.isfile("model.gguf"):
            model_path = os.path.abspath("model.gguf")
        if os.path.isfile(model_path):
            _llama = Llama(model_path=model_path, n_ctx=4096, verbose=False)
            print("[fallback] llama_cpp available for chat.")
        else:
            print(f"[fallback] llama_cpp model not found: {model_path}")
    except Exception as e:
        print(f"[fallback] llama_cpp unavailable: {type(e).__name__}: {e}")
    help_text = (
        "Commands:\n"
        "  chat <text>            - echo chat (LLM unavailable in fallback)\n"
        "  ls [path]              - list directory\n"
        "  read <path>            - read file\n"
        "  write <path>           - write file (then enter lines, end with a single '.' line)\n"
        "  append <path>          - append to file (end with '.')\n"
        "  rm <path>              - delete file or empty dir\n"
        "  mkdir <path>           - make directories\n"
        "  sh <command>           - run shell command in project root\n"
        "  impact <query>         - quick impact scan summary\n"
        "  help                   - show this help\n"
    )
    print(help_text)

    # Optional better CLI with history
    _session = None
    try:
        from prompt_toolkit import PromptSession  # type: ignore
        from prompt_toolkit.history import FileHistory  # type: ignore
        _session = PromptSession(history=FileHistory(".gpt_code_history"))
    except Exception:
        _session = None

    while True:
        try:
            if _session:
                line = _session.prompt(">>> ").strip()
            else:
                line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"exit", "quit", ":q"}:
            break
        if line == "help":
            print(help_text)
            continue

        try:
            if line.startswith("chat "):
                msg = line[5:]
                if _llama is None:
                    print("[chat]", msg)
                else:
                    out = _llama(f"SYSTEM: You are a helpful assistant.\nUSER: {msg}\nASSISTANT:", max_tokens=400)
                    txt = out.get("choices", [{}])[0].get("text") or str(out)
                    print(txt.strip())
            elif line.startswith("ls"):
                path = line[2:].strip() or "."
                print(list_dir(path, recursive=False))
            elif line.startswith("read "):
                print(read_file(line[5:].strip()))
            elif line.startswith("write "):
                p = line[6:].strip()
                print("Enter content, end with a single '.' line:")
                buf = []
                while True:
                    ln = input()
                    if ln == ".":
                        break
                    buf.append(ln)
                print(write_file(p, "\n".join(buf)))
            elif line.startswith("append "):
                p = line[7:].strip()
                print("Enter content, end with '.' line:")
                buf = []
                while True:
                    ln = input()
                    if ln == ".":
                        break
                    buf.append(ln)
                print(append_file(p, "\n".join(buf)))
            elif line.startswith("rm "):
                print(delete_path(line[3:].strip()))
            elif line.startswith("mkdir "):
                print(make_dirs(line[6:].strip()))
            elif line.startswith("sh "):
                print(shell_run(line[3:].strip(), timeout=20))
            elif line.startswith("impact "):
                q = line[len("impact "):].strip()
                payload = {"query": q, "limit": 100, "mode": "literal", "context": 2}
                import json as _json
                res = impact_scan_run(_json.dumps(payload))
                try:
                    data = _json.loads(res)
                except Exception:
                    print(res)
                    continue
                ranked = data.get("files_ranked") or []
                sugg = data.get("suggestions") or []
                print("[impact] Top files:")
                for it in ranked[:5]:
                    print(f"- {it.get('path')} ({it.get('score')})")
                if sugg:
                    print("[impact] Suggestions:")
                    for s in sugg:
                        print(f"- {s}")
            else:
                print("[fallback] unknown command. Type 'help'.")
        except Exception as e:
            print(f"[fallback] error: {type(e).__name__}: {e}")

    print("[gpt_code_agent] bye.")
    return 0


def _resolve_model_path() -> str:
    model_path = MODEL_PATH
    if os.path.islink("model.gguf") or os.path.isfile("model.gguf"):
        model_path = os.path.abspath("model.gguf")
    return model_path


def _direct_chat(_llm_ref, text: str) -> str:
    # Prefer native llama_cpp for stable one-shot chat
    global _NATIVE_LLAMA
    try:
        from llama_cpp import Llama  # type: ignore
        if _NATIVE_LLAMA is None:
            mp = _resolve_model_path()
            _NATIVE_LLAMA = Llama(model_path=mp, n_ctx=4096, verbose=False)
        prompt = f"USER: {text}\nASSISTANT:"
        out = _NATIVE_LLAMA(prompt, max_tokens=256, temperature=0.2, stop=["\nUSER:", "</s>"])
        txt = out.get("choices", [{}])[0].get("text") or str(out)
        return txt.strip()
    except Exception:
        # Fallback to langchain LLM invoke if native unavailable
        try:
            return str(_llm_ref.invoke(text)).strip()
        except Exception as e:
            return f"[chat] error: {type(e).__name__}: {e}"


def _norm(s: str) -> str:
    return (s or "").lower().replace(" ", "")


def _fs_list_all(base: str = ".", max_files: int = 2000) -> str:
    base = (base or ".").strip() or "."
    listing = list_dir(base, recursive=True)
    if not listing:
        return listing
    exclude_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build'}
    files = []
    for ln in listing.splitlines():
        parts = ln.split(" ", 2)
        if not parts or parts[0] != 'f':
            continue
        rel = parts[1]
        # exclude noisy directories
        if any(f"/{d}/" in f"/{rel}" for d in exclude_dirs):
            continue
        files.append(rel)
    truncated = False
    if len(files) > max_files:
        files = files[:max_files]
        truncated = True
    header = "[FS.ListAll] files={}{}".format(len(files), " (truncated)" if truncated else "")
    return header + "\n" + "\n".join(files)


def _is_list_files_query(text: str) -> bool:
    t = _norm(text)
    keys = [
        "listcurrentprojectfiles",
        "listfiles",
        "projectstructure",
        "repostructure",
        "directorystructure",
        "directorytree",
        "treelist",
        "tree",
        "ファイル一覧",
        "ファイルを一覧",
        "ファイル構成",
        "ファイル構造",
        "ディレクトリ構成",
        "ディレクトリツリー",
        "プロジェクト構成",
        "レポジトリ構成",
        "フォルダ構成",
        "ls-r",
        "ls-la",
    ]
    if any(k in t for k in keys):
        return True
    # heuristic combos like "ファイル 構成", "ディレクトリ 一覧"
    jp_file_words = ["ファイル", "ディレクトリ", "フォルダ"]
    jp_list_words = ["構成", "構造", "一覧", "ツリー"]
    if any(w in t for w in jp_file_words) and any(w in t for w in jp_list_words):
        return True
    eng_file_words = ["file", "files", "directory", "folders", "repo", "project"]
    eng_list_words = ["structure", "tree", "list"]
    if any(w in t for w in eng_file_words) and any(w in t for w in eng_list_words):
        return True
    return False


def _is_news_query(text: str) -> bool:
    t = _norm(text)
    keys = [
        "今日のニュース",
        "今日ニュース",
        "最新ニュース",
        "ニュース",
        "news",
        "latestnews",
        "todaynews",
    ]
    return any(k in t for k in keys)


def _is_mcp_query(text: str) -> bool:
    t = _norm(text)
    return "mcp" in t or "mcp経由" in t


def main() -> int:
    parser = argparse.ArgumentParser(description="gpt-code CLI agent")
    parser.add_argument("-p", "--prompt", help="Run once with the provided prompt and exit")
    parser.add_argument("--chat-only", action="store_true", help="Force pure chat (no tools)")
    sub = parser.add_subparsers(dest="cmd")

    # Direct impact_scan subcommand (no LLM)
    p_impact = sub.add_parser("impact", help="Run impact_scan directly (no LLM)")
    p_impact.add_argument("query")
    p_impact.add_argument("--limit", type=int, default=100)
    p_impact.add_argument("--mode", choices=["literal", "regex", "word"], default="literal")
    p_impact.add_argument("--context", type=int, default=2)
    p_impact.add_argument("--pythonVersion")
    p_impact.add_argument("--venvPath")
    p_impact.add_argument("--venv")
    p_impact.add_argument("--json", action="store_true", help="machine-readable output")

    args = parser.parse_args()

    # Handle impact alias before initializing agent/LLM
    if args.cmd == "impact":
        import json as _json
        pry = {k: getattr(args, k) for k in ("pythonVersion", "venvPath", "venv") if getattr(args, k, None)}
        payload = {
            "query": args.query,
            "limit": args.limit,
            "mode": args.mode,
            "context": args.context,
            "pyright": pry or None,
        }
        res_text = impact_scan_run(_json.dumps(payload))
        try:
            data = _json.loads(res_text)
        except Exception:
            print(res_text)
            return 0
        if args.json:
            print(_json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        ranked = data.get("files_ranked") or []
        sugg = data.get("suggestions") or []
        print("Top files:")
        for it in ranked[:10]:
            print(f"  - {it.get('path')}  (score={it.get('score')})")
        if sugg:
            print("\nSuggestions:")
            for s in sugg[:5]:
                print(f"  - {s}")
        return 0

    agent = _try_build_langchain_agent()
    if agent is None:
        return _fallback_cli()

    # one-shot prompt mode
    if args.prompt:
        llm = getattr(agent, "_llm_ref", None)
        text = args.prompt.strip()
        # pre-routing for one-shot
        if _is_list_files_query(text):
            print(_fs_list_all("."))
            return 0
        if _is_news_query(text):
            print(gemini_run("今日のニュースを要約して、出典も併記してください。", timeout=40))
            return 0
        if _is_mcp_query(text):
            out = ask_via_mcp(text)
            print(out if out else "[mcp] server/cli not found or returned no response. Set MCP_SERVER_CMD or install an MCP server.")
            return 0

        if args.chat_only and llm is not None:
            print(_direct_chat(llm, text))
            return 0
        try:
            resp: Any = agent.invoke({"input": text})
            if isinstance(resp, dict) and "output" in resp:
                print(resp["output"]) 
            else:
                print(str(resp))
        except Exception as e:
            msg = str(e)
            if llm is not None and ("Missing some input keys" in msg or "validation" in msg.lower()):
                print(_direct_chat(llm, text))
            else:
                print(f"[gpt_code_agent] error: {type(e).__name__}: {e}")
        return 0

    print("[gpt_code_agent] Type 'help' for tips, 'exit' to quit.")
    # Optional better CLI with history
    _session = None
    try:
        from prompt_toolkit import PromptSession  # type: ignore
        from prompt_toolkit.history import FileHistory  # type: ignore
        _session = PromptSession(history=FileHistory(".gpt_code_history"))
    except Exception:
        _session = None
    try:
        while True:
            try:
                if _session:
                    text = _session.prompt(">>> ").strip()
                else:
                    text = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not text:
                continue
            if text.lower() in {"exit", "quit", ":q"}:
                break
            if text.lower() in {"help", ":help", "/help"}:
                print("Usage examples:\n"
                      "- Create a file: 'Create src/foo.py with a hello() and write tests, run them.'\n"
                      "- List files: 'List current project files' (uses FS.List).\n"
                      "- Run a command: 'Run tests' or 'Shell: python3 -m unittest -v'.\n"
                      "- Edit file: 'Open src/foo.py, change X to Y, and rerun tests.'\n"
                      "Tools: WebSearch, PyExec, FS.Read/Write/Append/Delete/List/Mkdir, Shell.")
                continue

            # Pre-routing: intent-based early exits (checked before chat heuristics)
            lower = text.lower()
            if _is_list_files_query(text):
                print(_fs_list_all("."))
                continue
            if _is_news_query(text):
                print(gemini_run("今日のニュースを要約して、出典も併記してください。", timeout=40))
                continue
            if _is_mcp_query(text):
                out = ask_via_mcp(text)
                print(out if out else "[mcp] server/cli not found or returned no response. Set MCP_SERVER_CMD or install an MCP server.")
                continue

            # Heuristic: plain chat if explicitly asked or looks like small talk
            try:
                llm = getattr(agent, "_llm_ref", None)
                chat_triggers = (lower.startswith("chat:"), lower.startswith("/chat"))
                looks_like_chat = (
                    len(text) <= 24 or
                    any(k in lower for k in ["こんにちは", "hello", "hi", "hey", "今日", "help me", "explain", "why", "what", "how"]) and
                    not any(k in lower for k in ["fs.", "shell:", "run ", "python3", "unittest", "pytest", "create ", "write ", "append ", "delete ", "list ", "mkdir "])
                )
                if llm is not None and (chat_triggers or looks_like_chat):
                    # strip optional Chat: prefix
                    chat_text = text.split(":", 1)[1].strip() if lower.startswith("chat:") else text
                    result = _direct_chat(llm, chat_text)
                    print(result)
                    continue
            except Exception:
                pass

            try:
                resp: Any = agent.invoke({"input": text})
                if isinstance(resp, dict) and "output" in resp:
                    result = resp["output"]
                else:
                    result = str(resp)
            except Exception as e:
                msg = str(e)
                # If the agent complains about structured tool inputs, fall back to direct chat
                if "Missing some input keys" in msg or "validation" in msg.lower():
                    try:
                        llm = getattr(agent, "_llm_ref", None)
                        if llm is not None:
                            result = llm.invoke(text)
                        else:
                            result = f"[gpt_code_agent] error: {type(e).__name__}: {e}"
                    except Exception as e2:
                        result = f"[gpt_code_agent] error: {type(e2).__name__}: {e2}"
                else:
                    result = f"[gpt_code_agent] error: {type(e).__name__}: {e}"
            print(result)
    finally:
        print("[gpt_code_agent] bye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
