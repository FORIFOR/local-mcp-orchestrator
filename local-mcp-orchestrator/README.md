Claude Code ライクなローカルオーケストレーションエージェント（テンプレート）

このテンプレートは、ローカルの `llama_cpp` モデルを共通参照しつつ、
- MCP サーバ設定（`mcp-server.yaml`）
- CLI チャット REPL（`cli_chat.py`）
- LangChain エージェントモード（`agent.py`）
- シンボリックリンク作成スクリプト（`symlinks.sh`）
- 依存関係（`requirements.txt`）
をひとまとめにしたプロジェクト構成です。

注意: 現在の作業ディレクトリは `/Users/saiteku/workspace/gpt-local-code` 配下です。モデル本体は別ユーザーの絶対パスにあります（後述）。

1) モデル共有パス
- 既存モデル本体（単一ファイル）:
  - `/Users/saiteku/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf`
- すべてのツール／スクリプトからこのパスを共有参照します。
- 併せて、ローカルプロジェクト内にシンボリックリンクを作成する例を `symlinks.sh` に用意しています。
  - 例: `./models/gpt-oss-20b-MXFP4.gguf` → 上記絶対パス

2) MCP サーバ設定
- `mcp-server.yaml` は provider に `llama_cpp` を使用し、`path` を上記モデルに設定しています。
- tools セクションに `web_search` と `code_exec` を登録しています（例示的なエントリポイントを記載）。

注意: MCP サーバやクライアントは実装によって設定仕様が異なる可能性があります。本テンプレートの YAML は「概念実装例」です。ご利用の MCP 実装に合わせて適宜修正してください。

3) CLI チャット REPL
- `cli_chat.py` はシンプルな REPL です。
  - 上下キーで履歴参照（`prompt_toolkit`）。
  - `exit` / `quit` / `:q` で終了。
  - まず Python MCP クライアント（`mcp` パッケージ想定）で `mcp-server` を stdio 経由で起動・接続を試みます。
  - もし MCP クライアントが利用できない／接続失敗した場合は、`llama_cpp` 直接呼び出しにフォールバックします（モデルは同一パス）。

4) エージェントモード（LangChain 版）
- `agent.py` は LangChain の `LlamaCpp` ラッパーで上記モデルをロードします。
- Tool として `WebSearch`（DuckDuckGo API ラッパの簡易例）と `CodeExec`（Python subprocess 実行）を登録。
- `AgentType.ZERO_SHOT_REACT_DESCRIPTION` を使って自然言語でワークフロー（検索→要約、コード生成→実行など）を自動実行します。
  - ネットワーク制限環境では検索ツールが空振りになる場合があります。README の環境変数設定やオフライン動作の注意を参照してください。

5) セットアップ
- 必要パッケージをインストール:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- モデル共有リンクを作成（任意）:

```
bash symlinks.sh
```

- MCP サーバ起動（例）:

```
mcp-server --config mcp-server.yaml
```

- CLI チャット起動（MCP 経由／フォールバック内蔵）:

```
python3 cli_chat.py
```

- エージェントモード起動（LangChain）:

```
python3 agent.py
```

5.1) UI（CLI）
- 端末で動作する CLI UI を強化した `gpt_code_agent.py` を追加しました。
- チャット経由で「ファイル作成・編集・削除」「コマンド実行」「エラー修正の反復」を一気通貫で実行します。
- LangChain + llama_cpp が未インストールの場合は自動的にフォールバック CLI モードで起動し、ツールを直接実行できます（後述ログ参照）。

起動（CLI UI）:
```
python3 gpt_code_agent.py
# またはランチャーで起動（推奨）
chmod +x gpt-code
./gpt-code
```

ワンショット実行（非対話、1回だけ実行して終了）:
```
./gpt-code -p "こんにちは"              # チャットのみで回答
./gpt-code -p "こんにちは" --chat-only  # 明示的にツールを使わない
./gpt-code -p "List current project files"   # 必要に応じてツールを利用
```

注意:
- コマンド実行およびファイル操作は全て `local-mcp-orchestrator/` 配下に制限されます。
- 実行タイムアウト（既定 20s）と出力量の上限があります。

6) 実行例
- REPL:
  - 入力: `PythonでFizzBuzzのコードを書いて` → LLM 応答を表示
  - 入力: `exit` → 終了
- エージェント:
  - 例: `2024年のAIトレンドを調べて3点に要約`（ネットワークが利用可の場合、検索→要約）
  - 例: `配列をソートするPythonコードを書いて実行`（コード生成→実行→出力）
  - 例: `src/calc.py に divide(a,b) を実装し、ゼロ割は ValueError。テストを書いて実行し、失敗したら直して再実行`（作成→実行→修正）

7) テストログと修正（この環境での実行結果）
- 最初の起動テスト（LangChain 未インストール）:

```
$ python3 local-mcp-orchestrator/gpt_code_agent.py
[gpt_code_agent] LangChain/LLM unavailable: ModuleNotFoundError: No module named 'langchain'
[gpt_code_agent:fallback] Starting minimal CLI. Type 'help' for commands. 'exit' to quit.
[fallback] llama_cpp unavailable: ModuleNotFoundError: No module named 'llama_cpp'
Commands:
  chat <text>            - echo chat (LLM unavailable in fallback)
  ls [path]              - list directory
  read <path>            - read file
  write <path>           - write file (then enter lines, end with a single '.' line)
  append <path>          - append to file (end with '.')
  rm <path>              - delete file or empty dir
  mkdir <path>           - make directories
  sh <command>           - run shell command in project root
  help                   - show this help
>>> exit
[gpt_code_agent] bye.
```

- フォールバック CLI 機能テスト（ファイル・コマンド一式）:

```
$ python3 local-mcp-orchestrator/gpt_code_agent.py << 'EOF'
help
ls .
write tmp/demo.txt
hello
world
.
read tmp/demo.txt
append tmp/demo.txt
+1
.
read tmp/demo.txt
sh echo OK
rm tmp/demo.txt
ls tmp
exit
EOF

[gpt_code_agent] LangChain/LLM unavailable: ModuleNotFoundError: No module named 'langchain'
[gpt_code_agent:fallback] Starting minimal CLI. Type 'help' for commands. 'exit' to quit.
[fallback] llama_cpp unavailable: ModuleNotFoundError: No module named 'llama_cpp'
Commands:
  chat <text>            - echo chat (LLM unavailable in fallback)
  ls [path]              - list directory
  read <path>            - read file
  write <path>           - write file (then enter lines, end with a single '.' line)
  append <path>          - append to file (end with '.')
  rm <path>              - delete file or empty dir
  mkdir <path>           - make directories
  sh <command>           - run shell command in project root
  help                   - show this help
>>> ...（中略）
[fs.write] ok: tmp/demo.txt (11 bytes)
...
[sh] returncode=0
[stdout]
OK
...
[fs.delete] removed file: tmp/demo.txt
...
[gpt_code_agent] bye.
```

- 問題点の特定と修正:
  - 問題: `langchain` と `llama_cpp` が未インストールで起動に失敗。
  - 対応: `gpt_code_agent.py` を改修し、依存が無い場合でもフォールバック CLI UI が起動し、
    - ファイル作成・編集・削除
    - ディレクトリ一覧
    - シェル実行（プロジェクト配下）
    を実行できるようにしました。`prompt_toolkit` があれば履歴（↑↓）も有効。
  - 追加対応: `llama_cpp` のみが利用可能な環境では、フォールバック CLI の `chat` がローカルモデルによる応答を返します。
  - 本番運用: 依存をインストールすれば（`pip install -r requirements.txt`）、LangChain エージェントが自然言語から自動的に「検索→要約」「コード生成→実行」「エラー修正」を行います。

8) 重要な注意点
- ネットワークが制限されている環境では `WebSearch` が失敗する可能性があります。その場合は結果が空、もしくはフォールバックメッセージになります。
- `CodeExec` は安全確保のために実行時間・出力量・実行コマンドを制限しています。任意コード実行のリスクをご理解の上でお使いください。
- MCP の設定仕様は実装差があります。本テンプレートはあくまでひな形です。実際の MCP 実装に合わせて `mcp-server.yaml` と `cli_chat.py` の接続部分を調整してください。

9) プロジェクト構成
```
local-mcp-orchestrator/
├─ README.md
├─ requirements.txt
├─ symlinks.sh
├─ mcp-server.yaml
├─ cli_chat.py
├─ agent.py
├─ gpt_code_agent.py
├─ tools/
│  ├─ __init__.py
│  ├─ web_search.py
│  ├─ code_exec.py
│  ├─ fs_ops.py
│  └─ shell_exec.py
└─ utils/
   └─ mcp_client.py
 （CLI専用のため、ブラウザUIのソースは含めていません）

10) 付属CLIツール（サンプル）
- モジュール: `src/cli_tool.py`
- サブコマンド:
  - `greet [--name NAME]` → `Hello, NAME!`
  - `add A B` → `A+B` を表示
  - `divide A B` → `A/B` を表示（ゼロ割はエラー終了）
- 実行例:
```
python3 -m src.cli_tool greet --name Taro
python3 -m src.cli_tool add 1 2
python3 -m src.cli_tool divide 4 2
python3 -m src.cli_tool divide 1 0   # エラー終了
```

11) 外部連携
- Gemini CLI 連携（ウェブリサーチ）
  - `tools/gemini_cli.py` から `gemini -p "..."` を呼び出すツール `Gemini` を登録
  - 例: `./gpt-code -p "今日のニュースを要約して"` または REPL で `今日のニュースを教えて`
  - 注意: ローカルに `gemini` コマンドが必要です（PATH, APIキー設定など）
- MCP 連携
  - `utils/mcp_client.py` を使った `MCP.Query` ツールを登録
  - サーバ起動例: `mcp-server --config mcp-server.yaml`（PATH に `mcp-server` が無い場合は `MCP_SERVER_CMD` でコマンド名/パスを指定）
  - 例: `./gpt-code -p "MCP経由で'Hello'を送って"`（サーバ実装・tool 名に依存）
  - うまくいかない場合: `[mcp] server/cli not found...` が出力されます。`MCP_SERVER_CMD` / `MCP_CONFIG` を設定し、サーバを導入・起動してください。
```

ライセンス: テンプレートは学習用途のサンプルです。各依存ライブラリのライセンスに従ってください。
