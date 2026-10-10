# dependency-map

[解析トップへ戻る](../README.md)

内容確認したソースの静的依存関係。PythonはAST、JavaScript／TypeScriptはimport文の字句抽出です。型だけのimport、再export、コメントや動的importの扱いには制限があり、ランタイム依存の完全なグラフではありません。


```mermaid
graph TD
    n-local-mcp-orchestrator-tools-gemini-cli-py-b37374["gemini_cli.py\nlocal-mcp-orchestrator/tools/gemini_cli.py"]
    n-local-mcp-orchestrator-utils-mcp-client-py-254919["mcp_client.py\nlocal-mcp-orchestrator/utils/mcp_client.py"]
```

## 要素の説明

### n-local-mcp-orchestrator-tools-gemini-cli-py-b37374

確認済みファイル: `local-mcp-orchestrator/tools/gemini_cli.py`

解析: Python AST。静的なimport／export参照です。関数の実行順序やHTTP通信は表していません。

宣言: `run`

- `__future__` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `shlex` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `subprocess` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定

[詳細な図と説明を見る](n-local-mcp-orchestrator-tools-gemini-cli-py-b37374/README.md)

### n-local-mcp-orchestrator-utils-mcp-client-py-254919

確認済みファイル: `local-mcp-orchestrator/utils/mcp_client.py`

解析: Python AST。静的なimport／export参照です。関数の実行順序やHTTP通信は表していません。

宣言: `MCPUnavailable`, `_try_mcp_once`, `ask_via_mcp`

- `__future__` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `asyncio` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `typing` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `os` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `shlex` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `mcp.client.stdio` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `mcp.client.session` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定
- `mcp.types` → 外部・標準ライブラリ・別名など。ローカル対応先は未確定

[詳細な図と説明を見る](n-local-mcp-orchestrator-utils-mcp-client-py-254919/README.md)

