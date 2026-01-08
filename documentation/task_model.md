# task_model.py

**Location:** `clarity/models/task_model.py`

## Purpose

Defines the structured data model for task context and provides strict validation of LLM-generated output. This module has no external dependencies.

## Classes

### `TaskContextValidationError`

Custom exception raised when task context validation fails.

```python
class TaskContextValidationError(Exception):
    """Raised when task context validation fails."""
    pass
```

### `TaskContext`

Structured representation of a parsed task context.

#### Schema

| Field | Type | Description |
|-------|------|-------------|
| `task` | `str` | The task description |
| `owner` | `str` | The task owner/author |
| `explicit_goals` | `list[str]` | List of explicit goals |
| `unknowns` | `list[str]` | List of unknowns/open questions |
| `constraints` | `list[str]` | List of constraints |
| `assumptions` | `list[str]` | List of assumptions |

#### Class Attributes

- `REQUIRED_KEYS`: Set of all required field names
- `SCHEMA`: Dictionary mapping field names to expected types

#### Methods

**`__init__(self, task, owner, explicit_goals, unknowns, constraints, assumptions)`**

Direct constructor. Prefer `from_dict()` for validated creation.

**`from_dict(cls, data: dict) -> TaskContext`** (classmethod)

Creates a `TaskContext` from a dictionary with full validation.

- Raises `TaskContextValidationError` if validation fails
- Returns validated `TaskContext` instance

**`to_dict(self) -> dict`**

Converts the `TaskContext` back to a dictionary.

**`__repr__(self) -> str`**

Returns a debug-friendly string representation.

## Validation Rules

The `_validate()` method enforces:

1. Input must be a dictionary
2. All required keys must be present
3. No unexpected keys are permitted
4. `task` and `owner` must be strings
5. `explicit_goals`, `unknowns`, `constraints`, `assumptions` must be lists
6. All items within the lists must be strings

## Error Messages

Each validation failure produces a specific error message:

- `"Expected a dictionary, got <type>"`
- `"Missing required keys: <keys>"`
- `"Unexpected keys: <keys>"`
- `"Invalid type for '<field>': expected <expected>, got <actual>"`
- `"Invalid type for '<field>[<index>]': expected str, got <actual>"`

## Example Usage

```python
from clarity.models.task_model import TaskContext, TaskContextValidationError

data = {
    "task": "Implement user authentication",
    "owner": "backend-team",
    "explicit_goals": ["Support OAuth2", "Add session management"],
    "unknowns": ["Which OAuth provider?"],
    "constraints": ["Must use existing database"],
    "assumptions": ["Users have email addresses"]
}

try:
    context = TaskContext.from_dict(data)
    print(context.to_dict())
except TaskContextValidationError as e:
    print(f"Validation failed: {e}")
```
