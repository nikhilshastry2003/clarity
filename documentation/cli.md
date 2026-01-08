# cli.py

**Location:** `clarity/cli.py`

## Purpose

The command-line interface entry point for the clarity tool. Handles argument parsing, file validation, and orchestrates the task context parsing pipeline.

## Usage

```
clarity <task_context.md>
```

## Functions

### `main(argv: list[str] | None = None) -> int`

Entry point for the CLI application.

**Parameters:**
- `argv`: Optional list of command-line arguments. If `None`, uses `sys.argv[1:]`.

**Returns:**
- `0` on success
- `1` on any error

**Behavior:**
1. Validates exactly one argument is provided
2. Checks the input file exists and is a regular file
3. Creates `.clarity/scratch/` directory if missing
4. Invokes `TaskContextReader` to parse the markdown file
5. Writes validated output to `.clarity/scratch/task_model.json`
6. Prints success message or error details

## Dependencies

- `clarity.agents.task_context_reader.TaskContextReader`
- `clarity.models.task_model.TaskContextValidationError`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - task context parsed and saved |
| 1 | Error - invalid arguments, missing file, or validation failure |

## Output

**On success:**
```
✓ Parsed task_context.md → .clarity/scratch/task_model.json
```

**On error:**
```
Error: <description>
```

## Notes

- All errors are written to stderr
- The scratch directory is created with `parents=True` to handle missing parent directories
- Catches both `TaskContextValidationError` for schema issues and generic exceptions for other failures
