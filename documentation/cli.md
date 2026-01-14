# cli.py

**Location:** `clarity/cli.py`

## Purpose

The command-line interface entry point for the clarity tool. Orchestrates the full pipeline: reading inputs, running synthesis, and writing the design analysis output.

## Usage

```bash
clarity <task_context.md> [--docs <path>...] [--code <path>...] [--output <path>] [--dry-run]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_context` | Yes | Path to the task_context.md file |
| `--docs` | No | Paths to documentation files (markdown) |
| `--code` | No | Paths to code files or directories |
| `--output` | No | Output path (default: `.clarity/scratch/design_analysis.md`) |
| `--dry-run` | No | Parse inputs only, skip synthesis |

### Examples

```bash
# Basic usage
clarity task_context.md

# With documentation
clarity task_context.md --docs README.md docs/api.md

# With code
clarity task_context.md --code src/

# Full pipeline
clarity task_context.md --docs README.md docs/arch.md --code src/ lib/

# Dry run to test parsing
clarity task_context.md --docs README.md --code src/ --dry-run
```

## Responsibilities

1. Parse command-line arguments using argparse
2. Validate all input paths exist before processing
3. Orchestrate the pipeline steps:
   - Read task context via `read_task_context()`
   - Read documentation via `read_docs()`
   - Read code via `read_code()`
   - Synthesize via `synthesize()`
   - Write output via `write_design_analysis()`
4. Handle errors from each pipeline stage gracefully
5. Print progress messages to stdout, errors to stderr

## Dependencies

- `clarity.readers.read_task_context`
- `clarity.readers.read_docs`
- `clarity.readers.read_code`
- `clarity.agents.synthesize`
- `clarity.agents.set_llm_client`
- `clarity.writers.write_design_analysis`

## Functions

### `main(argv: list[str] | None = None) -> int`

Entry point for the CLI application.

**Parameters:**
- `argv`: Optional list of command-line arguments. If `None`, uses `sys.argv[1:]`.

**Returns:**
- `0` on success
- `1` on any error

### `_create_parser() -> argparse.ArgumentParser`

Creates the argument parser with all supported options.

### `_validate_paths(args: argparse.Namespace) -> list[str]`

Validates all input paths exist. Returns list of error messages.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - analysis generated |
| 1 | Error - invalid arguments, missing file, or pipeline failure |

## Output

**On success:**
```
Reading task context: task_context.md
Reading documentation: README.md, docs/api.md
Reading code: src/
Running synthesis...
Writing design analysis: .clarity/scratch/design_analysis.md
Done! Output: .clarity/scratch/design_analysis.md
```

**On dry run:**
```
Dry run complete - inputs parsed successfully
  Task: <task description>
  Docs: N files
  Code: N files
```

**On error:**
```
Error: <description>
```

## Notes

- All errors are written to stderr
- The output directory is created automatically if missing
- If no LLM client is configured, a stub client is used that produces placeholder output
- The `--dry-run` flag is useful for testing input parsing without requiring an LLM
