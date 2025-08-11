#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Any

from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain_community.llms import LlamaCpp

from tools import web_search_run, code_exec_run


MODEL_PATH = \
    "/Users/saiteku/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf"


def build_llm() -> LlamaCpp:
    model_path = MODEL_PATH
    # Prefer local symlink if present
    if os.path.islink("model.gguf") or os.path.isfile("model.gguf"):
        model_path = os.path.abspath("model.gguf")

    llm = LlamaCpp(
        model_path=model_path,
        n_ctx=4096,
        temperature=0.2,
        max_tokens=512,
        verbose=False,
    )
    return llm


def build_tools() -> list[Tool]:
    web_search_tool = Tool(
        name="WebSearch",
        func=lambda q: web_search_run(q, max_results=5),
        description=(
            "Use this to search the web for up-to-date information."
            " Input should be a natural language query."
        ),
    )
    code_exec_tool = Tool(
        name="CodeExec",
        func=lambda code: code_exec_run(code, timeout=10),
        description=(
            "Execute short Python snippets and return stdout/stderr."
            " Use for running generated code or quick calculations."
        ),
    )
    return [web_search_tool, code_exec_tool]


def main() -> int:
    print("[agent] starting LangChain agent. Type 'exit' to quit.")
    tools = build_tools()
    llm = build_llm()

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        memory=memory,
    )

    try:
        while True:
            try:
                text = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not text:
                continue
            if text.lower() in {"exit", "quit", ":q"}:
                break

            try:
                # agent.run is simpler for string input
                result: Any = agent.run(text)
            except Exception as e:
                result = f"[agent] error: {type(e).__name__}: {e}"

            print(result)
    finally:
        print("[agent] bye.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
