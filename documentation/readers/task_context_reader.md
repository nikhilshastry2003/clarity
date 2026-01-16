# Task Context Reader

**Location**: `clarity/readers/task_context_reader.py`

## Purpose

Parses a `task_context.md` file into a structured dictionary. This reader extracts the developer's intent, planned approach, unknowns, constraints, and assumptions from a human-written markdown document.

The parsed data feeds into LLM prompt generation to provide context-aware assistance.

## Inputs & Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `path` | `str` | File path to task_context.md |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| Task context | `dict` | Structured dictionary with 6 keys (see schema below) |

### Output Schema

```python
{
    "task": str,              # REQUIRED: never empty
    "owned_by": str,          # REQUIRED: never empty
    "planned_approach": list, # REQUIRED: at least 1 item
    "unknowns": list,         # Optional: may be []
    "constraints": list,      # Optional: may be []
    "assumptions": list,      # Optional: may be []
}
```

## Responsibilities

The task_context_reader is responsible for:

1. **File reading** - Read UTF-8 content from specified path
2. **Section detection** - Identify section headers (case-insensitive, markdown-aware)
3. **Value extraction** - Extract inline values and list items
4. **Unicode normalization** - Handle apostrophe variants (smart quotes, etc.)
5. **Validation** - Ensure required fields are present and non-empty
6. **Error reporting** - Report ALL validation errors at once, not just the first

## What This Module Must NOT Do

The task_context_reader must NOT:

1. **Perform reasoning** - Only parse, never interpret meaning
2. **Make assumptions about content** - Extract exactly what's written
3. **Call external services** - No network calls, no LLM
4. **Modify files** - Read-only operation
5. **Return partial results** - Either succeed completely or raise exception

## Dependencies

### Internal Dependencies

None - this is a leaf module.

### External Dependencies

- `re` - Regular expressions (stdlib)
- `pathlib.Path` - Path operations (stdlib)
- `typing.Optional` - Type hints (stdlib)

## Key Functions

### `read_task_context(path: str) -> dict`

Main entry point. Reads and parses the file.

**Parameters**:
- `path`: Path to task_context.md file

**Returns**: Dictionary with parsed sections

**Raises**:
- `FileNotFoundError`: File does not exist
- `TaskContextValidationError`: Required sections missing or invalid

### Internal Functions

| Function | Purpose |
|----------|---------|
| `_parse_lines(lines)` | Core parsing state machine |
| `_normalize_apostrophes(text)` | Handle Unicode apostrophe variants |
| `_strip_markdown_header(line)` | Remove `#` markers from headers |
| `_is_document_title(line)` | Detect document titles to skip |
| `_detect_section_header(line)` | Identify known section headers |
| `_extract_inline_value(line)` | Extract value after colon |
| `_extract_list_item(line)` | Extract bullet/numbered items |
| `_validate(result)` | Validate required fields present |

## Expected File Format

### Required Sections

| Section | Type | Description |
|---------|------|-------------|
| Task | Inline value | What the developer wants to accomplish |
| Owned by | Inline value | Team or person responsible |
| What I think I need to do | List | Planned approach (at least 1 item) |

### Optional Sections

| Section | Type | Description |
|---------|------|-------------|
| What I'm unsure about | List | Unknowns and questions |
| Constraints I know | List | Known limitations |
| Things I'm assuming | List | Assumptions that might be wrong |

### Format Flexibility

**Section headers** can be:
- Plain text: `Task:` or `Task`
- Markdown headers: `# Task` or `## Task`
- Case-insensitive: `TASK:`, `task:`, `Task:` all work

**List items** can use:
- Dash bullets: `- item`
- Asterisk bullets: `* item`
- Numbered lists: `1. item`
- Plain paragraphs under a section

**Unicode handling**: Various apostrophe characters (', ', `) are normalized to ASCII.

## Example Input

```markdown
# Task Context

Task: Build a user authentication system

Owned by: Backend Team

What I think I need to do:
- Implement login endpoint
- Add JWT token generation
- Create user session management

What I'm unsure about:
- OAuth integration details
- Session timeout requirements

Constraints I know:
- Must use existing database schema
- No third-party auth services

Things I'm assuming (might be wrong):
- Users will have email addresses
- Single sign-on is not needed
```

## Example Output

```python
{
    "task": "Build a user authentication system",
    "owned_by": "Backend Team",
    "planned_approach": [
        "Implement login endpoint",
        "Add JWT token generation",
        "Create user session management"
    ],
    "unknowns": [
        "OAuth integration details",
        "Session timeout requirements"
    ],
    "constraints": [
        "Must use existing database schema",
        "No third-party auth services"
    ],
    "assumptions": [
        "Users will have email addresses",
        "Single sign-on is not needed"
    ]
}
```

## Failure Modes

| Exception | Cause |
|-----------|-------|
| `FileNotFoundError` | File does not exist |
| `TaskContextValidationError("Path is not a file: ...")` | Path is a directory |
| `TaskContextValidationError("'Task' section is required...")` | Missing or empty task |
| `TaskContextValidationError("'Owned by' section is required...")` | Missing owner |
| `TaskContextValidationError("'What I think I need to do' must contain at least 1 item(s)")` | Empty planned approach |

**Multi-error reporting**: Validation collects ALL errors before raising, so users see all problems at once.

## Known Limitations

1. **Single file only** - Cannot read multiple task context files
2. **No include/import** - Cannot reference other files
3. **English section names** - Headers must match English patterns
4. **No nested structure** - Flat section model only
5. **Line-based parsing** - Multiline values within a list item not supported

## Design Philosophy: Strictness Is Intentional

This parser enforces strict validation for required fields. This is NOT arbitrary bureaucracy - it's essential for downstream reliability:

1. **Garbage In, Garbage Out**: The parsed data becomes part of LLM prompts. Missing required fields lead to useless or misleading AI output.

2. **Fail Fast, Fail Clearly**: When a file is malformed, raise immediately with a clear message. This is better than silently producing incomplete data.

3. **Human Accountability**: Requiring explicit task ownership and planned approach forces developers to think through their work before asking for AI help.

## Parsing Algorithm

The parser uses a **single-pass, line-by-line state machine**:

```
State variables:
- current_section: Which section we're in (or None)
- waiting_for_inline_value: For deferred inline values

For each line:
  1. Skip blank lines
  2. Skip document titles (e.g., "# Task Context")
  3. If section header detected:
     - Update current_section
     - For inline sections: extract value or wait for next line
     - For list sections: reset to empty list
  4. If waiting for inline value:
     - Capture this line as the value
  5. If under a list section:
     - Extract and append list item

After parsing:
  - Validate all required fields
  - Raise with ALL errors if any
```

**Performance**: O(n) where n = number of lines. Each line is processed exactly once.

## SECTION_CONFIG Structure

The parser is configuration-driven. Each section is defined in `SECTION_CONFIG`:

```python
'task': {
    'display_name': 'Task',
    'patterns': ['task'],
    'output_key': 'task',
    'type': 'inline',
}
```

- `display_name`: Used in error messages
- `patterns`: Lowercase patterns to match (with startswith)
- `output_key`: Key in output dictionary
- `type`: 'inline' (single value) or 'list' (multiple items)
- `required_items`: (optional) Minimum items for list sections
