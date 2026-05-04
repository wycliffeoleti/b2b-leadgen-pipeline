"""Shared CLI for running named workflows."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="first_agentic_workflow",
        description="Run an automation workflow",
    )
    parser.add_argument("name", help="Workflow module name (e.g. lead_gen)")
    parser.add_argument("--dry-run", action="store_true", help="Run without side effects")
    parser.add_argument("--client", default="example", help="Client name (default: example)")
    args = parser.parse_args(argv)

    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        module = importlib.import_module(f"workflows.{args.name}")
    except ModuleNotFoundError:
        print(f"Error: workflow '{args.name}' not found", file=sys.stderr)
        return 1

    run_fn = getattr(module, "run", None)
    if run_fn is None:
        print(f"Error: workflow '{args.name}' has no run() function", file=sys.stderr)
        return 1

    run_fn(dry_run=args.dry_run, client=args.client)
    return 0
