# code_reader.py

**Location:** `clarity/readers/code_reader.py`

## Purpose

Deterministic reader for Python source code files. Uses AST parsing to extract structural information (functions, classes, methods, imports) without execution or interpretation. Represents observed code reality.

## Inputs

A list of file or directory paths. Directories are scanned recursively for `.py` files.

## Output

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

## Responsibilities

1. Read Python files from specified paths
2. Recursively scan directories for `.py` files
3. Parse files using Python's AST module
4. Extract function and class signatures
5. Extract docstrings and line ranges
6. Extract import statements
7. Return structured representation of all code

## Functions

### `read_code(paths: list[str]) -> dict`

Read Python source files from specified paths.

**Parameters:**
- `paths`: List of file or directory paths to read

**Returns:**
- Dictionary with `files` key containing list of parsed file info

**Raises:**
- `CodeReadError`: If a path is invalid or cannot be read
- `FileNotFoundError`: If a path does not exist

## Data Structures

### FunctionInfo

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Function name |
| `signature` | str | Full signature with parameters and return type |
| `docstring` | str or null | Docstring if present |
| `line_start` | int | Line where function definition begins |
| `line_end` | int | Line where function body ends |
| `is_async` | bool | Whether function is async |

### ClassInfo

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Class name |
| `signature` | str | Class definition with base classes |
| `docstring` | str or null | Class docstring if present |
| `line_start` | int | Line where class definition begins |
| `line_end` | int | Line where class body ends |
| `bases` | list[str] | List of base class names |
| `methods` | list[FunctionInfo] | List of method info |

### FileInfo

| Field | Type | Description |
|-------|------|-------------|
| `path` | str | Absolute path to the file |
| `functions` | list[FunctionInfo] | Top-level functions |
| `classes` | list[ClassInfo] | Top-level classes |
| `imports` | list[str] | Import statements as strings |

## What It Does NOT Do

- Does not execute code - static analysis only
- Does not interpret behavior - extracts structure, not meaning
- Does not judge quality - no linting or style checks
- Does not infer relationships - no call graphs or dependency analysis
- Does not summarize - all functions and classes included
- Does not use LLMs - pure AST parsing
- Does not read non-Python files - only `.py` files processed
- Does not follow imports - only explicitly provided paths read

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | A specified path does not exist |
| `CodeReadError` | Path is invalid, file is unreadable, or contains syntax errors |

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

## Notes

- Code represents observed reality (what actually exists)
- Line numbers enable precise citations in analysis output
- Only processes explicitly provided paths (no implicit discovery)
- Syntax errors in any file cause the entire operation to fail
- Empty path list returns `{"files": []}`
