# CLI Module

**Location**: `clarity/cli.py`

## Purpose

The CLI module is the main entry point for Clarity. It orchestrates the full pipeline: parsing arguments, reading inputs, invoking the synthesizer, and writing output.

## Usage

```bash
clarity <task_context.md> [--docs <files...>] [--code <paths...>] [--output <path>] [--dry-run]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `task_context` | Yes | Path to task_context.md file |
| `--docs` | No | Paths to markdown documentation files |
| `--code` | No | Paths to Python files or directories |
| `--output` | No | Output path (default: `.clarity/scratch/design_analysis.md`) |
| `--dry-run` | No | Parse inputs only, skip synthesis |

### Examples

```bash
# Minimal invocation
clarity task_context.md

# With documentation
clarity task_context.md --docs README.md docs/api.md

# With code
clarity task_context.md --code src/

# Full invocation
clarity task_context.md --docs README.md --code src/ lib/

# Dry run (test parsing)
clarity task_context.md --docs README.md --code src/ --dry-run
```

## Key Functions

### `main(argv: list[str] | None = None) -> int`

Entry point. Returns 0 on success, 1 on error.

**Pipeline steps**:
1. Parse arguments
2. Validate paths
3. Read task context
4. Read documentation (if provided)
5. Read code (if provided)
6. Synthesize (unless dry-run)
7. Write output

### `_create_parser() -> argparse.ArgumentParser`

Creates the argument parser with all CLI options.

### `_validate_paths(args) -> list[str]`

Validates all input paths exist before processing. Returns list of error messages (empty if valid).

## StubLLMClient

When no LLM client is configured, the CLI uses a `StubLLMClient` that returns a placeholder response indicating synthesis was skipped. This allows the pipeline to run without a real LLM for testing purposes.

In production, replace with a real LLM client:

```python
from clarity.agents import set_llm_client, LLMClient

class OpenAIClient(LLMClient):
    def complete(self, system_prompt: str, user_content: str) -> str:
        # Call OpenAI API
        return response

set_llm_client(OpenAIClient())
```

## Error Handling

The CLI catches all domain-specific exceptions and converts them to user-friendly error messages:

| Exception | User Message |
|-----------|--------------|
| `TaskContextValidationError` | "Task context validation failed: ..." |
| `DocsReadError` | "Failed to read documentation: ..." |
| `CodeReadError` | "Failed to read code: ..." |
| `SynthesisError` | "Synthesis failed: ..." |
| `WriteError` | "Failed to write output: ..." |

All errors are printed to stderr with exit code 1.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (invalid paths, validation failure, synthesis error, write error) |
