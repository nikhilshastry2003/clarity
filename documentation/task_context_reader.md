# task_context_reader.py

**Location:** `clarity/readers/task_context_reader.py`

## Purpose

Deterministic parser for task_context.md files. Extracts structured data from markdown sections without any LLM calls. Same input always produces same output.

## Inputs

A markdown file with `##` headers for each section:

```markdown
## Task
Implement user authentication

## Owned by
backend-team

## What I think I need to do
- Add login endpoint
- Create session management

## What I'm unsure about
- Which OAuth provider to use

## Constraints I know
- Must use existing database

## Things I'm assuming (might be wrong)
- Users have email addresses
```

## Output

```python
{
    "task": "Implement user authentication",
    "owned_by": "backend-team",
    "planned_approach": [
        "Add login endpoint",
        "Create session management"
    ],
    "unknowns": [
        "Which OAuth provider to use"
    ],
    "constraints": [
        "Must use existing database"
    ],
    "assumptions": [
        "Users have email addresses"
    ]
}
```

## Responsibilities

1. Read markdown file from disk
2. Extract sections based on `##` headers
3. Parse bullet points from list sections
4. Validate required sections are present
5. Return structured dictionary

## Functions

### `read_task_context(path: str) -> dict`

Parse a task_context.md file into a structured dictionary.

**Parameters:**
- `path`: Path to the task_context.md file

**Returns:**
- Dictionary with parsed sections

**Raises:**
- `TaskContextValidationError`: If required sections are missing
- `FileNotFoundError`: If the file does not exist

## Required Sections

| Section Header | Output Key | Type |
|---------------|------------|------|
| `Task` | `task` | str |
| `Owned by` | `owned_by` | str |
| `What I think I need to do` | `planned_approach` | list[str] |
| `What I'm unsure about` | `unknowns` | list[str] |
| `Constraints I know` | `constraints` | list[str] |
| `Things I'm assuming (might be wrong)` | `assumptions` | list[str] |

## Optional Sections

| Section Header | Output Key | Type |
|---------------|------------|------|
| `Documentation hints` | `documentation_hints` | list[str] |
| `Suspected code areas` | `suspected_code_areas` | list[str] |

## What It Does NOT Do

- Does not use LLMs - pure string parsing
- Does not invent content - missing sections raise errors
- Does not rewrite text - bullet points extracted verbatim
- Does not validate semantics - checks structure only
- Does not handle nested bullets - top-level only

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | File does not exist |
| `TaskContextValidationError` | Missing required sections or invalid structure |

## Usage

```python
from clarity.readers import read_task_context, TaskContextValidationError

try:
    context = read_task_context("task_context.md")
    print(context["task"])
    print(context["planned_approach"])
except FileNotFoundError:
    print("File not found")
except TaskContextValidationError as e:
    print(f"Validation error: {e}")
```

## Notes

- Section headers are case-sensitive
- Empty list sections are allowed (returned as empty lists)
- Text sections (task, owned_by) cannot be empty
- Supports both `-` and `*` bullet markers, plus numbered lists
