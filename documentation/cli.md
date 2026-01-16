# CLI Module

**Location**: `clarity/cli.py`

## Purpose

The CLI module is the main entry point and orchestration layer for Clarity. It ties together all components (readers, synthesizer, writer) and provides the command-line interface for users.

The CLI itself contains **no business logic** beyond argument parsing and error handling. This keeps the core logic testable and reusable outside the CLI context.

## Inputs & Outputs

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `task_context` | Command-line positional arg | Path to task_context.md file |
| `--docs` | Command-line option | Paths to markdown documentation files |
| `--code` | Command-line option | Paths to Python files or directories |
| `--output` | Command-line option | Output file path |
| `--dry-run` | Command-line flag | Skip synthesis, parse only |

### Outputs

| Output | Destination | Description |
|--------|-------------|-------------|
| Design analysis | File (default: `.clarity/scratch/design_analysis.md`) | Markdown analysis document |
| Progress messages | stdout | Status updates during execution |
| Error messages | stderr | Error details on failure |
| Exit code | Process exit | 0 = success, 1 = error |

## Responsibilities

The CLI module is responsible for:

1. **Argument parsing** - Define and parse command-line options using `argparse`
2. **Path validation** - Verify all input paths exist before processing
3. **Pipeline orchestration** - Call readers, synthesizer, and writer in sequence
4. **Error handling** - Catch domain exceptions and convert to user-friendly messages
5. **LLM client fallback** - Install stub client if no real client is configured
6. **Output directory creation** - Ensure output directory exists

## What This Module Must NOT Do

The CLI module must NOT:

1. **Parse file contents** - That's the readers' responsibility
2. **Perform reasoning** - That's the synthesizer's responsibility
3. **Format output** - That's the writer's responsibility
4. **Make LLM calls** - That's the synthesizer's responsibility
5. **Define business logic** - Must remain a thin orchestration layer

## Dependencies

### Internal Dependencies

```python
from clarity.readers import read_task_context, read_docs, read_code
from clarity.readers import TaskContextValidationError, DocsReadError, CodeReadError
from clarity.agents import synthesize, set_llm_client, SynthesisError, LLMClient
from clarity.writers import write_design_analysis, WriteError
```

### External Dependencies

- `argparse` - Command-line argument parsing (stdlib)
- `sys` - System exit and argv (stdlib)
- `pathlib.Path` - Path operations (stdlib)

## Key Functions

### `main(argv: list[str] | None = None) -> int`

Entry point for the CLI. Parses arguments, runs the pipeline, and returns exit code.

**Parameters**:
- `argv`: Command-line arguments (defaults to `sys.argv[1:]`)

**Returns**: `0` on success, `1` on error

**Pipeline steps** (in order):
1. Parse arguments with `_create_parser()`
2. Validate paths with `_validate_paths()`
3. Read task context with `read_task_context()`
4. Read documentation with `read_docs()` (if `--docs` provided)
5. Read code with `read_code()` (if `--code` provided)
6. Check for dry-run (skip synthesis if set)
7. Synthesize with `synthesize()`
8. Write output with `write_design_analysis()`

### `_create_parser() -> argparse.ArgumentParser`

Creates the argument parser with all CLI options.

**Returns**: Configured `ArgumentParser` instance

### `_validate_paths(args: argparse.Namespace) -> list[str]`

Validates all input paths exist before processing.

**Parameters**:
- `args`: Parsed command-line arguments

**Returns**: List of error messages (empty if all paths valid)

### `class StubLLMClient(LLMClient)`

Stub LLM client for when no real LLM is configured.

This allows the pipeline to run end-to-end without a real LLM, useful for:
- Testing the full pipeline flow
- Demonstrating output format without API costs
- CI environments without LLM credentials

The stub response follows the exact schema expected by the writer but contains placeholder content.

## Usage Examples

```bash
# Minimal invocation
clarity task_context.md

# With documentation
clarity task_context.md --docs README.md docs/api.md

# With code
clarity task_context.md --code src/

# Full invocation
clarity task_context.md --docs README.md --code src/ lib/

# Dry run (test parsing without synthesis)
clarity task_context.md --docs README.md --code src/ --dry-run

# Custom output location
clarity task_context.md --output analysis.md
```

## Failure Modes

| Exception | User Message | Cause |
|-----------|--------------|-------|
| Path not found | `"Error: Task context file not found: ..."` | Input file missing |
| `TaskContextValidationError` | `"Error: Task context validation failed: ..."` | Malformed task_context.md |
| `DocsReadError` | `"Error: Failed to read documentation: ..."` | Cannot read doc file |
| `CodeReadError` | `"Error: Failed to read code: ..."` | Cannot read code file or syntax error |
| `SynthesisError` | `"Error: Synthesis failed: ..."` | LLM call failed or invalid response |
| `WriteError` | `"Error: Failed to write output: ..."` | Cannot write output file |
| Other `Exception` | `"Error: Unexpected error: ..."` | Catch-all for unexpected failures |

All errors are printed to stderr with exit code 1.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (any failure condition) |

## Known Limitations

1. **No configuration file support** - All options must be passed via command line
2. **No watch mode** - Must re-run for each analysis
3. **No parallel execution** - Readers run sequentially
4. **Single output format** - Only markdown output supported
5. **No progress indication** - Long synthesis has no progress bar

## Integrating an LLM Client

The CLI falls back to `StubLLMClient` if no real client is configured. To use a real LLM:

```python
from clarity.agents import set_llm_client, LLMClient

class OpenAIClient(LLMClient):
    def complete(self, system_prompt: str, user_content: str) -> str:
        # Call OpenAI API
        return response

# Configure before running clarity
set_llm_client(OpenAIClient())
```

This must be done before calling `main()` or invoking the CLI.
