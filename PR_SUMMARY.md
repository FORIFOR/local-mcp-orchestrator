### What
- Introduces `impact_scan` tool: ripgrep hits → N-line context → ranked files
- Optional focused pyright on matched `.py` files
- CLI demo: `impact <query>` prints ranked summary and suggestions
- README docs and new tests

### Why
- Fast “blast radius” discovery before edits; enables safer cross-file changes

### Inputs / Outputs
- Input: {"query", "limit"=100, "mode"="literal|regex|word", "context"=2, "pyright"?{pythonVersion?, venvPath?, venv?}}
- Output: {hits[], files_ranked[], suggestions[], used:{ripgrep{mode,context,installed?}, pyright?{installed?, pythonVersion?, venvPath?, venv?, error?}}}

### Demo
- agent impact_scan foo (fallback CLI: `impact <query>`) shows top ranked files and suggestions
- Example Edit.ApplyPatch footer previously added shows `strategy:"unified_diff"` and `hunks`

### Skip behavior samples
- pyright missing (sample):
```
"used": {"pyright": {"installed": false, "pythonVersion": "3.11", "venvPath": "/tmp/x", "venv": "venv", "error": "pyright not installed"}}
```
- ripgrep missing (sample):
```
{"hits":[],"files_ranked":[],"suggestions":[],"used":{"ripgrep":{"error":"ripgrep (rg) not installed","installed":false}},"error":"ripgrep (rg) not installed"}
```

### Tests
- All green locally; new tests cover mode switching, context flag, env opts

### Acceptance
- ≥5 hits & ≥1 suggestion on a repo with known matches
- Clean, structured skip if ripgrep/pyright missing

### Risks / Mitigations
- Large repos → bound by `limit` (default 100); context read is batched
- Read-only scan; no code changes applied

### Notes
- files_ranked.score = number of hits per file (simple frequency)
- Agent tool catalog includes `impact_scan` via fallback CLI command `impact <query>`

