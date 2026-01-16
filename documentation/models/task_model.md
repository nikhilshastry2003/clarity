# TaskModel Module

**Location**: `clarity/models/task_model.py`

## Purpose

The TaskModel module defines the `TaskContext` data class, which represents a structured task context that could be produced by an LLM. It provides validation and serialization for task context data.

**Note**: This module is currently **not used** in the main Clarity pipeline. The `task_context_reader.py` returns a plain dictionary rather than a `TaskContext` instance. This module appears to be designed for a future or alternative workflow where an LLM might generate structured task contexts.

## Inputs & Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| Task context data | `dict` | Dictionary with task, owner, goals, unknowns, etc. |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| `TaskContext` | Object | Validated task context instance |
| `dict` | Dictionary | Serialized task context via `to_dict()` |

## Responsibilities

The TaskModel module is responsible for:

1. **Defining the TaskContext schema** - Required keys and their types
2. **Validating input data** - Ensure all required keys present, correct types
3. **Providing type-safe access** - Instance attributes instead of dict access
4. **Serialization** - Convert to/from dictionary representation

## What This Module Must NOT Do

The TaskModel module must NOT:

1. **Parse files** - That's the reader's responsibility
2. **Perform any reasoning** - Just data structure and validation
3. **Make assumptions about content** - Only validate structure, not semantics
4. **Modify input data** - Validation only, no transformation

## Dependencies

### Internal Dependencies

None.

### External Dependencies

None beyond Python stdlib.

## Key Classes and Functions

### `class TaskContextValidationError(Exception)`

Raised when task context validation fails.

**Note**: This exception is **also defined** in `readers/task_context_reader.py`. This is a duplication that could cause confusion.

### `class TaskContext`

Structured task context model.

**Class Attributes**:

```python
REQUIRED_KEYS = {"task", "owner", "explicit_goals", "unknowns", "constraints", "assumptions"}

SCHEMA = {
    "task": str,
    "owner": str,
    "explicit_goals": list,
    "unknowns": list,
    "constraints": list,
    "assumptions": list,
}
```

**Instance Attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `task` | `str` | The task description |
| `owner` | `str` | Team or person responsible |
| `explicit_goals` | `list[str]` | Goals the developer wants to achieve |
| `unknowns` | `list[str]` | Things the developer is unsure about |
| `constraints` | `list[str]` | Known limitations |
| `assumptions` | `list[str]` | Assumptions that may be wrong |

**Methods**:

| Method | Description |
|--------|-------------|
| `from_dict(data: dict) -> TaskContext` | Class method to create instance from dict |
| `to_dict() -> dict` | Convert instance to dictionary |
| `_validate(data: dict) -> None` | Class method to validate input data |
| `__repr__() -> str` | String representation |

### Validation Rules

The `_validate()` method checks:

1. **Input is a dictionary** - Not a list, string, or other type
2. **All required keys present** - `REQUIRED_KEYS` must all exist
3. **No unexpected keys** - Only defined keys allowed
4. **Correct types** - Each key's value matches `SCHEMA` type
5. **List items are strings** - All items in list fields must be `str`

## Usage Example

```python
from clarity.models import TaskContext, TaskContextValidationError

# Valid data
data = {
    "task": "Build authentication",
    "owner": "Backend Team",
    "explicit_goals": ["Implement login", "Add JWT"],
    "unknowns": ["OAuth details"],
    "constraints": ["Use existing DB"],
    "assumptions": ["Users have email"],
}

context = TaskContext.from_dict(data)
print(context.task)  # "Build authentication"
print(context.to_dict())  # Returns original dict

# Invalid data - missing key
try:
    TaskContext.from_dict({"task": "Test"})
except TaskContextValidationError as e:
    print(e)  # "Missing required keys: ..."
```

## Failure Modes

| Failure | Cause |
|---------|-------|
| `TaskContextValidationError("Expected a dictionary, got X")` | Input is not a dict |
| `TaskContextValidationError("Missing required keys: ...")` | Required keys absent |
| `TaskContextValidationError("Unexpected keys: ...")` | Unknown keys present |
| `TaskContextValidationError("Invalid type for 'X': ...")` | Wrong type for field |
| `TaskContextValidationError("Invalid type for 'X[N]': ...")` | List contains non-string |

## Known Limitations

1. **Not used in main pipeline** - `task_context_reader.py` returns plain dict
2. **Schema mismatch** - Uses `owner` and `explicit_goals` but reader uses `owned_by` and `planned_approach`
3. **Duplicate exception** - `TaskContextValidationError` defined in two places
4. **No optional fields** - All fields are required (unlike reader which has optional sections)
5. **Strict key validation** - Rejects any keys not in REQUIRED_KEYS

## Schema Comparison

The TaskContext schema differs from the reader's output:

| TaskContext | Reader Output | Notes |
|-------------|---------------|-------|
| `owner` | `owned_by` | Different key name |
| `explicit_goals` | `planned_approach` | Different key name |
| `unknowns` | `unknowns` | Same |
| `constraints` | `constraints` | Same |
| `assumptions` | `assumptions` | Same |

This mismatch means `TaskContext.from_dict()` cannot directly accept output from `read_task_context()`.

## Relationship to Other Modules

- **Not imported by CLI** - CLI uses reader output directly
- **Not imported by synthesizer** - Synthesizer takes plain dicts
- **Exported from `clarity.models`** - Available for external use
- **Parallel to reader** - Alternative data structure, not integrated

## Future Considerations

If this module is to be used:

1. **Align schema with reader** - Use same key names
2. **Remove duplicate exception** - Define in one place
3. **Consider optional fields** - Match reader's optional/required distinction
4. **Integrate with pipeline** - Have reader return TaskContext instances
