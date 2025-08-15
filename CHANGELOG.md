# Changelog

## [Unreleased]
### Added
- `impact_scan` ツール（ripgrep + N行コンテキスト + 任意のpyright）。CLIデモ `impact <query>` を追加。
- ApplyPatch のフッターに `strategy` / `hunks` を追加。

### Fixed
- CRLF/BOM を保持するようパッチ適用を修正。ハッシュをraw bytesで統一。
- modify時の実行ビット維持、create/deleteの競合ガード。

### Notes
- `files_ranked.score = ヒット件数`（今後重み付けを追加予定）
