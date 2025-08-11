#!/usr/bin/env bash
set -euo pipefail

# This script scaffolds a web-search MCP server and prints config steps for Codex.

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
TARGET_DIR="$ROOT_DIR/integrations/web-search"
REPO_URL="https://github.com/pskill9/web-search"

echo "[i] Cloning web-search MCP to $TARGET_DIR"
mkdir -p "$TARGET_DIR"
if [ ! -d "$TARGET_DIR/.git" ]; then
  git clone "$REPO_URL" "$TARGET_DIR"
else
  echo "[i] Repo exists. Pulling latest..."
  (cd "$TARGET_DIR" && git pull --rebase)
fi

echo "[i] Installing and building"
(cd "$TARGET_DIR" && npm i && npm run build)

BUILD_JS="$TARGET_DIR/build/index.js"
echo "[i] Built at: $BUILD_JS"

echo
echo "[next] Add to ~/.codex/config.toml (create file if missing):"
cat <<TOML

[mcp_servers.websearch]
command = "node"
args = ["$BUILD_JS"]
TOML

echo
echo "[next] Test with Inspector (optional):"
echo "npx @modelcontextprotocol/inspector node $BUILD_JS"

