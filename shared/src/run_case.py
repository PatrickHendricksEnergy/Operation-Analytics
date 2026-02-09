"""CLI runner to execute a case pipeline."""
from __future__ import annotations

import argparse
import importlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a case pipeline")
    parser.add_argument("--case", required=True, help="case name (folder under cases)")
    args = parser.parse_args()

    module_path = f"cases.{args.case}.src.pipeline"
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:
        print(f"Failed to import {module_path}: {exc}")
        sys.exit(1)

    if not hasattr(module, "run"):
        print(f"Pipeline module {module_path} has no run()")
        sys.exit(1)

    module.run()


if __name__ == "__main__":
    main()
