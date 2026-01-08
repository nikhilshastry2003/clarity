# Task Context Reader

## What It Does

The Task Context Reader is a deterministic markdown parser that extracts structured data from `task_context.md` files. It converts human-written task descriptions into a Python dictionary with well-defined keys.

### Input Format

The reader expects a markdown file with `##` headers for each section:

```markdown
## Task
Implement user authentication

## Owned by
backend-team

## What I think I need to do
- Add login endpoint
- Create session management
- Implement password hashing

## What I'm unsure about
- Which OAuth provider to use
- Session storage strategy

## Constraints I know
- Must integrate with existing user table
- Cannot use external auth services

## Things I'm assuming (might be wrong)
- Users already have email addresses in the system
- We can add columns to the users table
```

### Output Format

```python
{
    "task": "Implement user authentication",
    "owned_by": "backend-team",
    "planned_approach": [
        "Add login endpoint",
        "Create session management",
        "Implement password hashing"
    ],
    "unknowns": [
        "Which OAuth provider to use",
        "Session storage strategy"
    ],
    "constraints": [
        "Must integrate with existing user table",
        "Cannot use external auth services"
    ],
    "assumptions": [
        "Users already have email addresses in the system",
        "We can add columns to the users table"
    ]
}
```

## Why It Exists

Before analyzing how a task fits into a codebase, we need structured input. Developers write task descriptions in markdown because it's natural and flexible. But downstream processing requires predictable data structures.

This reader bridges that gap: it accepts freeform markdown and produces validated, structured output.

Key design goals:
1. **Fail fast on bad input.** Missing required sections raise clear exceptions.
2. **Preserve original text.** No rewriting, summarizing, or "improving" the content.
3. **Deterministic behavior.** Same input always produces same output.

## Required Sections

These sections must be present or parsing fails:

| Section Header | Output Key |
|---------------|------------|
| `Task` | `task` |
| `Owned by` | `owned_by` |
| `What I think I need to do` | `planned_approach` |
| `What I'm unsure about` | `unknowns` |
| `Constraints I know` | `constraints` |
| `Things I'm assuming (might be wrong)` | `assumptions` |

## Optional Sections

These sections are parsed if present, ignored if absent:

| Section Header | Output Key |
|---------------|------------|
| `Documentation hints` | `documentation_hints` |
| `Suspected code areas` | `suspected_code_areas` |

## What It Does NOT Do

- **Does not use LLMs.** This is pure string parsing. No AI, no inference.
- **Does not invent content.** If a section is empty, the output is empty.
- **Does not rewrite or improve text.** Bullet points are extracted verbatim.
- **Does not guess missing sections.** Missing required sections cause an exception.
- **Does not validate semantics.** It checks structure, not meaning.
- **Does not handle nested bullets.** Only top-level bullets are extracted.

## Usage

```python
from clarity.readers import read_task_context, TaskContextParseError

try:
    context = read_task_context("task_context.md")
    print(context["task"])
    print(context["unknowns"])
except FileNotFoundError:
    print("File not found")
except TaskContextParseError as e:
    print(f"Parse error: {e}")
```

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | File does not exist |
| `TaskContextParseError` | File is not readable, has no sections, or is missing required sections |
