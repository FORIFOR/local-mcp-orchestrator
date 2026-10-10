# overall-architecture/n-local-mcp-orchestrator-dd539a/group-1

[解析トップへ戻る](../../../README.md)

このグループは表示用の区切りです。独立した実行モジュールではありません。


```mermaid
graph TD
    n-local-mcp-orchestrator-models-f6bc23["models\nlocal-mcp-orchestrator/models"]
    n-local-mcp-orchestrator-scripts-e21918["scripts\nlocal-mcp-orchestrator/scripts"]
    n-local-mcp-orchestrator-src-752c78["src\nlocal-mcp-orchestrator/src"]
    n-local-mcp-orchestrator-tests-c68225["tests\nlocal-mcp-orchestrator/tests"]
    n-local-mcp-orchestrator-tmp-34154b["tmp\nlocal-mcp-orchestrator/tmp"]
    n-local-mcp-orchestrator-tools-a05b76["tools\nlocal-mcp-orchestrator/tools"]
    n-local-mcp-orchestrator-utils-a61d31["utils\nlocal-mcp-orchestrator/utils"]
    n-local-mcp-orchestrator-agent-py-53d4c7["agent.py\nlocal-mcp-orchestrator/agent.py"]
```

## 要素の説明

### n-local-mcp-orchestrator-agent-py-53d4c7

実在パス: `local-mcp-orchestrator/agent.py`。1ファイル。

- `local-mcp-orchestrator/agent.py`

### n-local-mcp-orchestrator-models-f6bc23

実在パス: `local-mcp-orchestrator/models`。1ファイル。

- `local-mcp-orchestrator/models/gpt-oss-20b-MXFP4.gguf`

### n-local-mcp-orchestrator-scripts-e21918

実在パス: `local-mcp-orchestrator/scripts`。1ファイル。

- `local-mcp-orchestrator/scripts/setup-codex-websearch.sh`

### n-local-mcp-orchestrator-src-752c78

実在パス: `local-mcp-orchestrator/src`。3ファイル。

- `local-mcp-orchestrator/src/adder.py`
- `local-mcp-orchestrator/src/calc.py`
- `local-mcp-orchestrator/src/cli_tool.py`

### n-local-mcp-orchestrator-tests-c68225

実在パス: `local-mcp-orchestrator/tests`。6ファイル。

- `local-mcp-orchestrator/tests/test_adder.py`
- `local-mcp-orchestrator/tests/test_calc.py`
- `local-mcp-orchestrator/tests/test_cli_impact_alias.py`
- `local-mcp-orchestrator/tests/test_cli_tool.py`
- `local-mcp-orchestrator/tests/test_impact_scan.py`
- `local-mcp-orchestrator/tests/test_patch_flow.py`

### n-local-mcp-orchestrator-tmp-34154b

実在パス: `local-mcp-orchestrator/tmp`。15ファイル。

- `local-mcp-orchestrator/tmp/demo_patch.txt`
- `local-mcp-orchestrator/tmp/e2e_apply.txt`
- `local-mcp-orchestrator/tmp/e2e_apply_run.txt`
- `local-mcp-orchestrator/tmp/e2e_conflict.txt`
- `local-mcp-orchestrator/tmp/e2e_crlf.txt`
- `local-mcp-orchestrator/tmp/e2e_repr.txt`
- `local-mcp-orchestrator/tmp/e2e_repr_run.txt`
- `local-mcp-orchestrator/tmp/e2e_repr_run2.txt`
- `local-mcp-orchestrator/tmp/e2e_smoke_crlf.txt`
- `local-mcp-orchestrator/tmp/e2e_smoke_exec.sh`
- `local-mcp-orchestrator/tmp/e2e_tool.sh`
- `local-mcp-orchestrator/tmp/lock.txt`
- `local-mcp-orchestrator/tmp/smoke.txt`
- `local-mcp-orchestrator/tmp/smoke_crlf.txt`
- `local-mcp-orchestrator/tmp/smoke_crlf2.txt`

### n-local-mcp-orchestrator-tools-a05b76

実在パス: `local-mcp-orchestrator/tools`。24ファイル。

- `local-mcp-orchestrator/tools/__init__.py`
- `local-mcp-orchestrator/tools/__pycache__/__init__.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/code_exec.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/fs_ops.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/gemini_cli.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/impact_scan.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/shell_exec.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/tests.cpython-313.pyc`
- `local-mcp-orchestrator/tools/__pycache__/web_search.cpython-313.pyc`
- `local-mcp-orchestrator/tools/code_exec.py`
- `local-mcp-orchestrator/tools/edit/__pycache__/apply_patch.cpython-313.pyc`
- `local-mcp-orchestrator/tools/edit/__pycache__/plan_patch.cpython-313.pyc`
- `local-mcp-orchestrator/tools/edit/apply_patch.py`
- `local-mcp-orchestrator/tools/edit/plan_patch.py`
- `local-mcp-orchestrator/tools/fs_ops.py`
- `local-mcp-orchestrator/tools/gemini_cli.py`
- `local-mcp-orchestrator/tools/impact_scan.py`
- `local-mcp-orchestrator/tools/index/__pycache__/ripgrep.cpython-313.pyc`
- `local-mcp-orchestrator/tools/index/ripgrep.py`
- `local-mcp-orchestrator/tools/lsp/__pycache__/diagnostics.cpython-313.pyc`
- `local-mcp-orchestrator/tools/lsp/diagnostics.py`
- `local-mcp-orchestrator/tools/shell_exec.py`
- `local-mcp-orchestrator/tools/tests.py`
- `local-mcp-orchestrator/tools/web_search.py`

### n-local-mcp-orchestrator-utils-a61d31

実在パス: `local-mcp-orchestrator/utils`。2ファイル。

- `local-mcp-orchestrator/utils/__pycache__/mcp_client.cpython-313.pyc`
- `local-mcp-orchestrator/utils/mcp_client.py`

