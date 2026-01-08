# Code Reader

## What It Does

The Code Reader extracts structural information from Python source files. It parses the AST (Abstract Syntax Tree) to identify functions, classes, methods, and imports, preserving signatures, docstrings, and line locations.

### Input

A list of file or directory paths. Directories are scanned recursively for `.py` files.

### Output

```python
{
    "files": [
        {
            "path": "/absolute/path/to/module.py",
            "functions": [
                {
                    "name": "process_data",
                    "signature": "def process_data(items: list[str], limit: int = 10) -> dict",
                    "docstring": "Process a list of items and return results.",
                    "line_start": 15,
                    "line_end": 42,
                    "is_async": false
                }
            ],
            "classes": [
                {
                    "name": "DataProcessor",
                    "signature": "class DataProcessor(BaseProcessor)",
                    "docstring": "Handles data processing operations.",
                    "line_start": 50,
                    "line_end": 120,
                    "bases": ["BaseProcessor"],
                    "methods": [
                        {
                            "name": "__init__",
                            "signature": "def __init__(self, config: Config)",
                            "docstring": null,
                            "line_start": 54,
                            "line_end": 58,
                            "is_async": false
                        }
                    ]
                }
            ],
            "imports": [
                "from pathlib import Path",
                "import json"
            ]
        }
    ]
}
```

## Why Code Is Treated as Observed Reality

Code is **what exists**. Not what was intended. Not what the documentation claims. What actually runs.

In the Clarity pipeline, there are three sources of truth:

| Source | Represents |
|--------|------------|
| Task Context | What the developer wants to do |
| Documentation | What the system is supposed to be |
| Code | What the system actually is |

The Code Reader captures observed reality because:

1. **Code doesn't lie.** A function either exists or it doesn't. It either accepts certain parameters or it doesn't. There's no ambiguity.

2. **Documentation can drift.** Docs may describe a function that was renamed, parameters that changed, or behavior that was modified. Code shows current state.

3. **Intent vs. implementation.** The task says "add caching." The code shows whether caching already exists, what patterns are used, where related logic lives.

The reader extracts facts: names, signatures, locations, docstrings. It makes no claims about quality, correctness, or design.

## Why Interpretation Is Forbidden

Interpretation at read time would corrupt the data.

### No Quality Judgments

The reader does not flag "bad code" or "good patterns." A function with 500 lines and no docstring is recorded the same as a well-documented 10-line function. Quality judgment happens later, with full context.

### No Behavior Inference

The reader extracts `def calculate_tax(amount: float) -> float`. It does not infer "this calculates sales tax" or "this handles tax brackets." The name and signature are facts. The behavior is interpretation.

### No Relationship Mapping

The reader notes that `class OrderService` has methods `create_order` and `cancel_order`. It does not infer that `OrderService` "manages the order lifecycle" or "coordinates with InventoryService." Relationships require analysis, not reading.

### No Summarization

If a class has 20 methods, all 20 are recorded. The reader doesn't decide which are "important." Importance depends on the task, which is unknown at read time.

### Determinism

AST parsing is deterministic. Same code produces same output. Interpretation could vary, especially if LLM-based. The reader must be reproducible.

## How This Output Is Used Later

The structured code output enables precise downstream operations:

### Citation in Recommendations

When Clarity suggests modifying code, it can cite exactly where:

```
Add caching decorator to `fetch_user` (see src/services/user.py:45-67)
```

The `line_start` and `line_end` fields make this possible.

### Signature Matching

Later stages can match task requirements against existing signatures:

- Task mentions "handle authentication"
- Reader found `def authenticate(user: User, password: str) -> Token`
- Analysis can connect these facts

### Scope Filtering

The reader only processes paths explicitly provided. This ensures:

- Analysis is bounded to relevant code
- Unrelated code doesn't pollute context
- Processing time is predictable

### Docstring Extraction

Docstrings, when present, provide author-declared intent. They're extracted verbatim for later comparison against observed behavior.

### Import Analysis

Captured imports reveal dependencies:

- What external libraries are used
- What internal modules are connected
- Where integration points exist

## Usage

```python
from clarity.readers import read_code, CodeReadError

try:
    result = read_code([
        "src/",
        "lib/utils.py"
    ])

    for file in result["files"]:
        print(f"File: {file['path']}")

        for func in file["functions"]:
            print(f"  Function: {func['signature']}")
            print(f"    Lines: {func['line_start']}-{func['line_end']}")

        for cls in file["classes"]:
            print(f"  Class: {cls['signature']}")
            print(f"    Methods: {len(cls['methods'])}")

except FileNotFoundError as e:
    print(f"Path not found: {e}")
except CodeReadError as e:
    print(f"Read error: {e}")
```

## What It Does NOT Do

- **Does not execute code.** Static analysis only.
- **Does not interpret behavior.** Extracts structure, not meaning.
- **Does not judge quality.** No linting, no style checks.
- **Does not infer relationships.** No call graphs, no dependency analysis.
- **Does not summarize.** All functions and classes are included.
- **Does not use LLMs.** Pure AST parsing.
- **Does not read non-Python files.** Only `.py` files are processed.
- **Does not follow imports.** Only explicitly provided paths are read.

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | A specified path does not exist |
| `CodeReadError` | Path is invalid, file is unreadable, or contains syntax errors |

## Extracted Information

### For Functions

| Field | Description |
|-------|-------------|
| `name` | Function name |
| `signature` | Full signature with parameters and return type |
| `docstring` | Docstring if present, `null` otherwise |
| `line_start` | Line where function definition begins |
| `line_end` | Line where function body ends |
| `is_async` | Whether function is async |

### For Classes

| Field | Description |
|-------|-------------|
| `name` | Class name |
| `signature` | Class definition with base classes |
| `docstring` | Class docstring if present |
| `line_start` | Line where class definition begins |
| `line_end` | Line where class body ends |
| `bases` | List of base class names |
| `methods` | List of method info (same structure as functions) |

### For Files

| Field | Description |
|-------|-------------|
| `path` | Absolute path to the file |
| `functions` | Top-level functions |
| `classes` | Top-level classes |
| `imports` | Import statements as strings |
