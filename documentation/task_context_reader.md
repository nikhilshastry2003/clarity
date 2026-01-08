# task_context_reader.py

**Location:** `clarity/agents/task_context_reader.py`

## Purpose

Orchestrates the LLM-based parsing of markdown task context files into structured JSON. This module handles all LLM interaction for the task context parsing stage.

## Status

**Not yet implemented.** This file is a placeholder for the Task Context Reader agent.

## Intended Interface

```python
class TaskContextReader:
    def __init__(self):
        """Initialize the reader, loading the prompt template."""
        pass

    def parse(self, file_path: Path) -> TaskContext:
        """
        Parse a task context markdown file.

        Args:
            file_path: Path to the task_context.md file

        Returns:
            Validated TaskContext instance

        Raises:
            TaskContextValidationError: If LLM output fails validation
            Exception: For LLM communication errors
        """
        pass
```

## Responsibilities

1. Load the prompt template from `clarity/prompt/task_context_reader.txt`
2. Read the input markdown file
3. Construct the LLM request (system prompt + user content)
4. Send request to the LLM provider
5. Parse the JSON response
6. Validate and return a `TaskContext` object

## Design Constraints

- All LLM interaction for this pipeline stage is isolated here
- Uses the prompt template verbatim (no dynamic prompt modification)
- Returns validated `TaskContext` objects only
- Fails fast on any LLM or validation error

## Dependencies

- `clarity.models.task_model.TaskContext`
- `clarity.models.task_model.TaskContextValidationError`
- LLM provider SDK (to be determined)

## Notes

- If the LLM provider changes, only this file needs modification
- No retry logic is implemented; failures should be handled by the caller
- The prompt template enforces extraction-only behavior from the LLM
