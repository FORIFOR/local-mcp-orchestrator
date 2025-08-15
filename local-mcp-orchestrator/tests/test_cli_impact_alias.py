import subprocess
import sys


def test_cli_impact_alias():
    # Run the direct impact subcommand; ensure it prints the header
    proc = subprocess.run([sys.executable, "gpt_code_agent.py", "impact", "def"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Top files:" in (proc.stdout or "")

