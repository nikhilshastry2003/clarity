"""Command-line interface for clarity."""

import json
import sys
from pathlib import Path

from clarity.agents.task_context_reader import TaskContextReader
from clarity.models.task_model import TaskContextValidationError


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI."""
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Usage: clarity <task_context.md>", file=sys.stderr)
        return 1

    task_context_path = Path(argv[0])

    if not task_context_path.exists():
        print(f"Error: File not found: {task_context_path}", file=sys.stderr)
        return 1

    if not task_context_path.is_file():
        print(f"Error: Not a file: {task_context_path}", file=sys.stderr)
        return 1

    scratch_dir = Path(".clarity") / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)

    try:
        reader = TaskContextReader()
        task_context = reader.parse(task_context_path)

        output_path = scratch_dir / "task_model.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(task_context.to_dict(), f, indent=2)

        print(f"✓ Parsed {task_context_path.name} → .clarity/scratch/task_model.json")
        return 0

    except TaskContextValidationError as e:
        print(f"Error: Validation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
