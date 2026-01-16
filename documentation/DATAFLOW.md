# Clarity - Data Flow

This document traces the complete lifecycle of a `clarity` CLI invocation.

## Example Command

```bash
clarity task_context.md --docs README.md docs/api.md --code src/
```

## Step-by-Step Flow

### Step 1: CLI Argument Parsing

**Location**: `clarity/cli.py:_create_parser()`

The CLI parses:
- `task_context`: Required positional argument (path to task_context.md)
- `--docs`: Optional list of documentation file paths
- `--code`: Optional list of code file/directory paths
- `--output`: Output path (default: `.clarity/scratch/design_analysis.md`)
- `--dry-run`: Skip synthesis, only parse inputs

### Step 2: Path Validation

**Location**: `clarity/cli.py:_validate_paths()`

Before any processing, all paths are validated:
- Task context file must exist
- All doc paths must exist
- All code paths must exist

If any path is missing, the CLI exits with error messages.

### Step 3: Read Task Context

**Location**: `clarity/readers/task_context_reader.py:read_task_context()`

**Input**: Path to `task_context.md`

**Process**:
1. Read file content as UTF-8
2. Parse line by line, detecting section headers
3. Extract inline values (task, owner) and list items (goals, unknowns, etc.)
4. Validate required sections are present

**Output**:
```python
{
    "task": "Build user authentication",
    "owned_by": "Backend Team",
    "planned_approach": ["Implement login", "Add JWT tokens"],
    "unknowns": ["OAuth details"],
    "constraints": ["Use existing DB schema"],
    "assumptions": ["Users have email"]
}
```

### Step 4: Read Documentation

**Location**: `clarity/readers/docs_reader.py:read_docs()`

**Input**: List of markdown file paths

**Process**:
1. For each file:
   - Read content as UTF-8
   - Parse into sections based on `#`, `##`, `###` headings
   - Track line numbers for each section

**Output**:
```python
{
    "documents": [
        {
            "path": "/abs/path/to/README.md",
            "sections": [
                {
                    "heading": "Overview",
                    "level": 1,
                    "content": "This system...",
                    "line_start": 1,
                    "line_end": 15
                }
            ]
        }
    ]
}
```

### Step 5: Read Code

**Location**: `clarity/readers/code_reader.py:read_code()`

**Input**: List of file or directory paths

**Process**:
1. For directories: recursively find all `.py` files
2. For each Python file:
   - Parse with Python's `ast` module
   - Extract functions (name, signature, docstring, lines)
   - Extract classes (name, signature, bases, methods)
   - Extract imports

**Output**:
```python
{
    "files": [
        {
            "path": "/abs/path/to/src/auth.py",
            "functions": [
                {
                    "name": "login",
                    "signature": "def login(username: str, password: str) -> Token",
                    "docstring": "Authenticate user...",
                    "line_start": 10,
                    "line_end": 25,
                    "is_async": False
                }
            ],
            "classes": [...],
            "imports": ["from jwt import encode"]
        }
    ]
}
```

### Step 6: Synthesize (LLM Call)

**Location**: `clarity/agents/synthesizer.py:synthesize()`

**Input**: Three dictionaries from previous steps

**Process**:
1. Load system prompt from `prompts/synthesizer.txt`
2. Format user content by combining:
   - Task context (formatted as markdown)
   - Documentation (sections with line references)
   - Code observations (functions, classes, truncated for token limits)
3. Call configured `LLMClient.complete()`
4. Parse JSON response
5. Validate required keys present

**LLM Prompt Structure**:
```
System: You are a technical analyst...
        [Rules for evidence hierarchy, output format]

User:   ## Task Context
        Task: Build user authentication
        ...

        ## Documentation
        ### File: README.md
        ...

        ## Code Observations
        ### File: src/auth.py
        ...

        ---
        Analyze these inputs and produce the mental model JSON.
```

**Output**:
```python
{
    "system_intent": {
        "summary": "...",
        "key_points": [...],
        "citations": [...]
    },
    "observed_reality": {
        "summary": "...",
        "relevant_code": [...],
        "patterns_found": [...]
    },
    "feature_fit": {
        "alignments": [...],
        "conflicts": [...]
    },
    "assumptions_and_risks": [...],
    "open_decisions": [...],
    "documentation_gaps": [...],
    "confidence_assessment": {
        "overall": "medium",
        "limiting_factors": [...],
        "sufficient_to_proceed": True
    }
}
```

### Step 7: Write Output

**Location**: `clarity/writers/design_analysis_writer.py:write_design_analysis()`

**Input**: Analysis dictionary from synthesizer

**Process**:
1. Render each section to markdown:
   - Header with confidence and status
   - System Intent section
   - Observed Reality section
   - Feature Fit Analysis section
   - Assumptions & Risks section
   - Open Decisions section
   - Documentation Gaps section
2. Create parent directories if needed
3. Write UTF-8 encoded file

**Output**: `.clarity/scratch/design_analysis.md`

```markdown
# Design Analysis

**Confidence:** medium | **Status:** Ready to proceed

**Limiting Factors:**
- Limited documentation coverage

## 1. System Intent

The system is designed to...

## 2. Observed Code Reality

The code shows...

[... remaining sections ...]
```

## Data Flow Diagram

```
task_context.md ──┐
                  │
README.md ────────┼──▶ CLI ──▶ Readers ──┐
docs/api.md ──────┤                      │
                  │                      ▼
src/ ─────────────┘              ┌───────────────┐
                                 │ task_ctx dict │
                                 │ docs dict     │──▶ Synthesizer
                                 │ code dict     │        │
                                 └───────────────┘        │
                                                          ▼
                                                    LLM Client
                                                          │
                                                          ▼
                                                  analysis dict
                                                          │
                                                          ▼
                                                      Writer
                                                          │
                                                          ▼
                                           .clarity/scratch/design_analysis.md
```

## Error Handling Flow

Each step can fail with specific exceptions:

| Step | Exception | Cause |
|------|-----------|-------|
| Path validation | `SystemExit(1)` | File not found |
| Task context | `TaskContextValidationError` | Missing required sections |
| Docs | `DocsReadError` | Unreadable file |
| Code | `CodeReadError` | Syntax error or unreadable |
| Synthesize | `SynthesisError` | No LLM client, invalid response |
| Write | `WriteError` | Permission denied, disk full |

All exceptions are caught in `cli.py:main()` and converted to user-friendly error messages with exit code 1.
