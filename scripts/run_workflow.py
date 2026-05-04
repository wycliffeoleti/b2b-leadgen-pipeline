"""CLI entry point for running automation workflows."""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from first_agentic_workflow.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
