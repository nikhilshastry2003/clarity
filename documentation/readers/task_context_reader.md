# Task Context Reader

**Location**: `clarity/readers/task_context_reader.py`

## Purpose

Parses a `task_context.md` file into a structured dictionary. This reader extracts the developer's intent, planned approach, unknowns, constraints, and assumptions.

## Expected File Format

The parser expects a Markdown file with specific sections:

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
- Plain text: `Task:` or `Task:`
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

## Output Structure

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

## Key Functions

### `read_task_context(path: str) -> dict`

Main entry point. Reads and parses the file.

**Raises**:
- `FileNotFoundError`: File does not exist
- `TaskContextValidationError`: Required sections missing or invalid

### `_parse_lines(lines: list[str]) -> dict`

Core parsing logic. Iterates through lines, detecting section headers and collecting content.

### `_detect_section_header(trimmed_line: str) -> Optional[str]`

Identifies if a line is a known section header. Handles markdown headers, plain text, and case variations.

### `_extract_list_item(trimmed_line: str) -> Optional[str]`

Extracts list items from dash, asterisk, or numbered formats.

### `_validate(result: dict) -> None`

Ensures required fields are present and non-empty.

## Configuration

The `SECTION_CONFIG` dictionary defines:
- Display names for error messages
- Pattern variations for matching
- Output key names
- Whether the section is inline or list
- Minimum required items for list sections

## Error Messages

| Error | Cause |
|-------|-------|
| "'Task' section is required and cannot be empty" | Missing or empty task |
| "'Owned by' section is required and cannot be empty" | Missing owner |
| "'What I think I need to do' must contain at least 1 item(s)" | Empty planned approach |
