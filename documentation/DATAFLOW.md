# Clarity - Data Flow

This document traces the complete lifecycle of a `clarity` CLI invocation, showing exactly how data transforms at each stage.

## Example Command

```bash
clarity task_context.md --docs README.md docs/api.md --code src/
```

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLARITY PIPELINE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUT FILES              READERS               SYNTHESIZER      WRITER    │
│   ───────────              ───────               ───────────      ──────    │
│                                                                             │
│   task_context.md ──┐                                                       │
│                     │      ┌────────────────┐                               │
│                     ├─────▶│ task_context   │──┐                            │
│                     │      │ _reader        │  │                            │
│                     │      └────────────────┘  │                            │
│                     │                          │    ┌────────────┐          │
│   README.md ────────┤      ┌────────────────┐  ├───▶│            │          │
│   docs/api.md ──────┼─────▶│ docs_reader    │──┤    │ synthesize │          │
│                     │      └────────────────┘  │    │    ()      │          │
│                     │                          │    │            │          │
│   src/*.py ─────────┤      ┌────────────────┐  │    │  1 LLM     │          │
│                     └─────▶│ code_reader    │──┘    │  call      │          │
│                            └────────────────┘       │            │          │
│                                                     └─────┬──────┘          │
│                                                           │                 │
│                                                           ▼                 │
│                                                     ┌────────────┐          │
│                                                     │  write_    │          │
│                                                     │  design_   │──▶ .md   │
│                                                     │  analysis  │          │
│                                                     └────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Flow

### Step 1: CLI Argument Parsing

**Location**: `clarity/cli.py:_create_parser()` (lines 29-84)

The CLI parses command-line arguments using `argparse`:

| Argument | Required | Type | Default |
|----------|----------|------|---------|
| `task_context` | Yes | Positional | - |
| `--docs` | No | List of paths | `[]` |
| `--code` | No | List of paths | `[]` |
| `--output` | No | Path | `.clarity/scratch/design_analysis.md` |
| `--dry-run` | No | Flag | `False` |

**Output**: Parsed `argparse.Namespace` object

### Step 2: Path Validation

**Location**: `clarity/cli.py:_validate_paths()` (lines 87-109)

Before any processing, all paths are validated:

```python
# Validation checks (in order):
1. Task context file exists?
2. All doc paths exist?
3. All code paths exist?
```

**If any path is missing**: Error messages printed to stderr, exit with code 1.

**Output**: Validated paths (no data transformation)

### Step 3: Read Task Context

**Location**: `clarity/readers/task_context_reader.py:read_task_context()` (lines 263-334)

**Input**: Path to `task_context.md`

**Process**:
1. Verify file exists and is a file (not directory)
2. Read file content as UTF-8
3. Split into lines
4. Parse line-by-line using state machine:
   - Detect section headers (case-insensitive, markdown-aware)
   - Extract inline values (Task, Owned by)
   - Collect list items (planned approach, unknowns, etc.)
5. Validate required fields are present and non-empty

**Output Dictionary**:
```python
{
    "task": "Build user authentication",        # REQUIRED: never empty
    "owned_by": "Backend Team",                 # REQUIRED: never empty
    "planned_approach": [                       # REQUIRED: at least 1 item
        "Implement login endpoint",
        "Add JWT tokens"
    ],
    "unknowns": ["OAuth details"],              # Optional: may be []
    "constraints": ["Use existing DB schema"],  # Optional: may be []
    "assumptions": ["Users have email"]         # Optional: may be []
}
```

**Failure modes**:
- `FileNotFoundError`: File does not exist
- `TaskContextValidationError`: Required sections missing or empty

### Step 4: Read Documentation

**Location**: `clarity/readers/docs_reader.py:read_docs()` (lines 56-79)

**Input**: List of markdown file paths (may be empty)

**Process**:
1. For each file path:
   - Verify file exists and is a file
   - Read content as UTF-8
   - Parse into sections based on headings (`#`, `##`, `###`)
   - Track line numbers for each section

**Output Dictionary**:
```python
{
    "documents": [
        {
            "path": "/absolute/path/to/README.md",
            "sections": [
                {
                    "heading": "Overview",
                    "level": 1,
                    "content": "This system provides...",
                    "line_start": 1,
                    "line_end": 15
                },
                {
                    "heading": "API Reference",
                    "level": 2,
                    "content": "The API exposes...",
                    "line_start": 17,
                    "line_end": 45
                }
            ]
        }
    ]
}
```

**Note on heading levels**: Only `#`, `##`, and `###` are treated as section delimiters. Deeper headings (`####` etc.) become part of section content.

**Failure modes**:
- `FileNotFoundError`: File does not exist
- `DocsReadError`: Path is not a file or cannot be read

### Step 5: Read Code

**Location**: `clarity/readers/code_reader.py:read_code()` (lines 84-120)

**Input**: List of file or directory paths (may be empty)

**Process**:
1. For each path:
   - If file: Parse if `.py` extension
   - If directory: Recursively find all `.py` files
2. For each Python file:
   - Parse with `ast.parse()` (NO code execution)
   - Extract functions (name, signature, docstring, lines, async flag)
   - Extract classes (name, signature, bases, methods)
   - Extract import statements

**Output Dictionary**:
```python
{
    "files": [
        {
            "path": "/absolute/path/to/src/auth.py",
            "functions": [
                {
                    "name": "login",
                    "signature": "def login(username: str, password: str) -> Token",
                    "docstring": "Authenticate user and return token.",
                    "line_start": 10,
                    "line_end": 25,
                    "is_async": False
                }
            ],
            "classes": [
                {
                    "name": "TokenManager",
                    "signature": "class TokenManager(BaseManager)",
                    "docstring": "Manages JWT tokens.",
                    "line_start": 30,
                    "line_end": 80,
                    "methods": [...],
                    "bases": ["BaseManager"]
                }
            ],
            "imports": [
                "from jwt import encode",
                "import hashlib"
            ]
        }
    ]
}
```

**Security note**: Code is parsed using Python's `ast` module. **No code is ever executed**. This is safe for analyzing untrusted code.

**Failure modes**:
- `FileNotFoundError`: Path does not exist
- `CodeReadError`: Syntax error or cannot read file

### Step 6: Dry Run Check

**Location**: `clarity/cli.py:main()` (lines 213-218)

If `--dry-run` flag is set:
- Print summary of parsed inputs
- Exit with code 0
- **Skip synthesis and writing**

This is useful for testing input parsing without LLM costs.

### Step 7: LLM Client Setup

**Location**: `clarity/cli.py:main()` (lines 223-228)

Check if an LLM client is configured:
- If not: Install `StubLLMClient` that returns placeholder response
- If yes: Use configured client

The `StubLLMClient` allows the pipeline to run end-to-end without a real LLM, useful for testing.

### Step 8: Synthesize (LLM Call)

**Location**: `clarity/agents/synthesizer.py:synthesize()` (lines 310-348)

**Input**: Three dictionaries from previous steps

**Process**:
1. Get configured LLM client
2. Load system prompt from `prompts/synthesizer.txt`
3. Format user content by combining:
   - Task context (formatted as markdown)
   - Documentation (sections with line references)
   - Code observations (functions, classes, with token management)
4. Call `LLMClient.complete(system_prompt, user_content)`
5. Parse JSON response (strips markdown code block wrappers)
6. Validate required keys present

**Token Management** (applied in `_format_code()`):
- Imports: Show first 10 (prevents token bloat)
- Docstrings: Truncate to 200 characters
- Methods: Show first 5 per class

**LLM Prompt Structure**:
```
System: You are a technical analyst synthesizing information...
        [Evidence hierarchy, output format, rules]

User:   ## Task Context
        Task: Build user authentication
        Owner: Backend Team
        ...

        ## Documentation
        ### File: README.md
        #### Overview (lines 1-15)
        This system provides...

        ## Code Observations
        ### File: src/auth.py
        **Functions:**
        `def login(username: str) -> Token` (lines 10-25)
        ...

        ---
        Analyze these inputs and produce the mental model JSON.
```

**Output Dictionary** (7 required keys):
```python
{
    "system_intent": {
        "summary": "The system is designed to...",
        "key_points": ["point 1", "point 2"],
        "citations": ["README.md:10-15", "docs/api.md:5-8"]
    },
    "observed_reality": {
        "summary": "The code shows...",
        "relevant_code": [
            {
                "path": "src/auth.py",
                "element": "TokenManager",
                "lines": "30-80",
                "relevance": "Handles token lifecycle"
            }
        ],
        "patterns_found": ["Repository pattern", "DI"]
    },
    "feature_fit": {
        "alignments": [
            {
                "aspect": "Authentication approach",
                "evidence": "Docs specify JWT, code uses jwt library",
                "confidence": "high"
            }
        ],
        "conflicts": [
            {
                "aspect": "Session handling",
                "docs_say": "Stateless JWT",
                "code_shows": "Session table in DB",
                "severity": "medium"
            }
        ]
    },
    "assumptions_and_risks": [
        {
            "assumption": "Users will have email addresses",
            "source": "task_context",
            "risk_if_wrong": "Registration flow breaks",
            "validation_needed": "Check user model"
        }
    ],
    "open_decisions": [
        {
            "decision": "Which OAuth provider to use",
            "options": ["Google", "GitHub", "Both"],
            "blocking": True,
            "context": "Affects callback URL configuration"
        }
    ],
    "documentation_gaps": [
        {
            "gap": "Error handling strategy",
            "impact": "Unknown how to handle auth failures",
            "suggested_source": "Ask team lead"
        }
    ],
    "confidence_assessment": {
        "overall": "medium",
        "limiting_factors": ["Limited documentation", "Complex codebase"],
        "sufficient_to_proceed": True
    }
}
```

**Failure modes**:
- `SynthesisError("LLM client not configured")`: `set_llm_client()` not called
- `SynthesisError("Prompt template not found")`: Missing synthesizer.txt
- `SynthesisError("LLM call failed: ...")`: Provider error
- `SynthesisError("Failed to parse LLM response as JSON")`: Invalid JSON
- `SynthesisError("Synthesis output missing required keys")`: Incomplete response

### Step 9: Write Output

**Location**: `clarity/writers/design_analysis_writer.py:write_design_analysis()` (lines 23-40)

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
- Limited documentation
- Complex codebase

## 1. System Intent

The system is designed to...

**Key Points:**
- point 1
- point 2

**Sources:**
- `README.md:10-15`
- `docs/api.md:5-8`

## 2. Observed Code Reality

The code shows...

**Relevant Code:**

- **`src/auth.py`**
  - Element: `TokenManager`
  - Lines: 30-80
  - Relevance: Handles token lifecycle

**Patterns Found:**
- Repository pattern
- DI

## 3. Feature Fit Analysis

### Alignments

**Authentication approach**
- Evidence: Docs specify JWT, code uses jwt library
- Confidence: high

### Conflicts

**Session handling** (Severity: medium)
- Documentation says: Stateless JWT
- Code shows: Session table in DB

## 4. Assumptions & Risks

### 1. Users will have email addresses

- **Source:** task_context
- **Risk if wrong:** Registration flow breaks
- **Validation needed:** Check user model

## 5. Open Decisions

### 1. Which OAuth provider to use

**Status:** BLOCKING

Affects callback URL configuration

**Options:**
- Google
- GitHub
- Both

## 6. Documentation Gaps

### Error handling strategy

**Impact:** Unknown how to handle auth failures

**Suggested source:** Ask team lead
```

**Failure modes**:
- `WriteError`: Permission denied, disk full, invalid path

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

All exceptions are caught in `cli.py:main()` (lines 240-257) and converted to user-friendly error messages with exit code 1.

## Data Transformation Summary

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  RAW FILES      │     │  STRUCTURED     │     │  ANALYSIS       │
│                 │     │  DICTIONARIES   │     │  DICTIONARY     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ task_context.md │ ──▶ │ task_ctx dict   │     │                 │
│ README.md       │ ──▶ │ docs dict       │ ──▶ │ 7-key mental    │
│ src/*.py        │ ──▶ │ code dict       │     │ model dict      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │    DETERMINISTIC      │    PROBABILISTIC      │    DETERMINISTIC
         │    (Readers)          │    (Synthesizer)      │    (Writer)
         │                       │                       │
         ▼                       ▼                       ▼
    Parse & Extract        Reason & Analyze        Render & Format
```

## Debugging Tips

### Inspecting Intermediate Data

To see what the readers produce without running synthesis:

```bash
clarity task_context.md --docs README.md --code src/ --dry-run
```

This validates inputs and shows summary counts.

### Checking LLM Prompt

The synthesizer builds the prompt in `_build_user_content()`. To inspect:

1. Add logging in `synthesize()` before the LLM call
2. Or use a stub client that prints the prompt

### Verifying Reader Output

Each reader can be called directly in Python:

```python
from clarity.readers import read_task_context, read_docs, read_code

task_ctx = read_task_context("task_context.md")
print(task_ctx)

docs = read_docs(["README.md"])
print(docs)

code = read_code(["src/"])
print(code)
```

### Tracing Errors

| Error Message | Check |
|---------------|-------|
| "Task context validation failed" | Is task_context.md well-formed? Required sections present? |
| "Failed to read documentation" | Does the file exist? Is it readable? |
| "Failed to read code" | Syntax error in Python file? |
| "Synthesis failed" | LLM client configured? Response valid JSON? |
| "Failed to write output" | Permission to write to output directory? |
