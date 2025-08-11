#!/usr/bin/env bash
set -euo pipefail

# モデル共有のためのシンボリックリンク作成スクリプト
# 既存モデル: /Users/horioshuuhei/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf
# このプロジェクト内: ./models/gpt-oss-20b-MXFP4.gguf にリンクを作成

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
MODELS_DIR="$SCRIPT_DIR/models"
TARGET="/Users/saiteku/.lmstudio/models/lmstudio-community/gpt-oss-20b-GGUF/gpt-oss-20b-MXFP4.gguf"
LINK="$MODELS_DIR/gpt-oss-20b-MXFP4.gguf"

mkdir -p "$MODELS_DIR"

if [ ! -f "$TARGET" ]; then
  echo "[WARN] モデル本体が見つかりません: $TARGET" >&2
  echo "       パスが正しいか、アクセス権があるか確認してください。" >&2
fi

ln -sfn "$TARGET" "$LINK"
echo "[OK] Symlink created: $LINK -> $TARGET"

# 便利用の短縮リンク
ln -sfn "$LINK" "$SCRIPT_DIR/model.gguf"
echo "[OK] Shortcut symlink: $SCRIPT_DIR/model.gguf -> $LINK"
