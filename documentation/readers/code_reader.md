# Code Reader

**Location**: `clarity/readers/code_reader.py`

## Purpose

Reads Python source code files and extracts structural information using AST (Abstract Syntax Tree) parsing. This provides the synthesizer with code observations without executing any code.

Code observations represent **observed reality** - what the codebase actually contains, regardless of what documentation claims.

## Inputs & Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `paths` | `list[str]` | List of paths to Python files or directories |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| Code dict | `dict` | Dictionary with `files` key containing parsed file info |

### Output Schema

```python
{
    "files": [
        {
            "path": "/absolute/path/to/file.py",
            "functions": [
                {
                    "name": "function_name",
                    "signature": "def function_name(arg1: str, arg2: int = 0) -> bool",
                    "docstring": "Function documentation...",
                    "line_start": 10,
                    "line_end": 25,
                    "is_async": False
                }
            ],
            "classes": [
                {
                    "name": "ClassName",
                    "signature": "class ClassName(BaseClass)",
                    "docstring": "Class documentation...",
                    "line_start": 30,
                    "line_end": 80,
                    "methods": [...],  # Same structure as functions
                    "bases": ["BaseClass"]
                }
            ],
            "imports": [
                "import os",
                "from pathlib import Path"
            ]
        }
    ]
}
```

## Responsibilities

The code_reader is responsible for:

1. **File discovery** - Find all `.py` files in directories (recursive)
2. **AST parsing** - Parse Python source without execution
3. **Function extraction** - Extract name, signature, docstring, lines
4. **Class extraction** - Extract name, signature, bases, methods
5. **Import extraction** - Record import statements
6. **Line tracking** - Record start/end line numbers for citations

## What This Module Must NOT Do

The code_reader must NOT:

1. **Execute code** - CRITICAL: No `exec()`, `eval()`, or imports of target code
2. **Interpret semantics** - Only structure, not meaning
3. **Perform reasoning** - That's the synthesizer's job
4. **Modify files** - Read-only operation
5. **Parse non-Python** - Only `.py` files supported
6. **Follow imports** - Does not resolve or analyze imported modules

## Dependencies

### Internal Dependencies

None - this is a leaf module.

### External Dependencies

- `ast` - Python AST parsing (stdlib)
- `pathlib.Path` - Path operations (stdlib)
- `dataclasses` - Data class definitions (stdlib)

## Key Functions

### `read_code(paths: list[str]) -> dict`

Main entry point. Processes all provided paths.

**Parameters**:
- `paths`: List of file or directory paths

**Behavior**:
- For files: Parses if `.py` extension
- For directories: Recursively finds all `.py` files

**Returns**: Dictionary with `files` key containing parsed file info

**Raises**:
- `FileNotFoundError`: Path does not exist
- `CodeReadError`: Syntax error or unreadable file

### `_read_single_file(path: Path) -> FileInfo`

Parses a single Python file using `ast.parse()`.

### `_extract_function(node, source_lines, is_async) -> FunctionInfo`

Extracts function information from an AST node.

### `_extract_class(node, source_lines) -> ClassInfo`

Extracts class information including all methods.

### `_build_function_signature(node, is_async) -> str`

Reconstructs the function signature as a string.

### `_build_arguments(args) -> str`

Formats function arguments including:
- Positional-only args (before `/`)
- Regular args with defaults
- `*args` and `**kwargs`
- Keyword-only args

### `_extract_import(node) -> list[str]`

Extracts import statements as human-readable strings.

## Data Classes

### `FunctionInfo`

```python
@dataclass
class FunctionInfo:
    name: str           # Function name
    signature: str      # Full signature string
    docstring: str | None
    line_start: int
    line_end: int
    is_async: bool      # True for async def
```

### `ClassInfo`

```python
@dataclass
class ClassInfo:
    name: str
    signature: str      # e.g., "class Foo(Bar, Baz)"
    docstring: str | None
    line_start: int
    line_end: int
    methods: list[FunctionInfo]
    bases: list[str]    # Parent class names
```

### `FileInfo`

```python
@dataclass
class FileInfo:
    path: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
```

All classes implement `to_dict()` methods for serialization.

## Security: No Code Execution

This is a critical safety feature. The reader uses Python's `ast` module:

```python
tree = ast.parse(source, filename=str(path))
```

This means:
- **No code execution** - Safe to parse untrusted/malicious code
- **Syntax errors are caught** - Reported as `CodeReadError`
- **Type annotations preserved** - Using `ast.unparse()`

You can safely run Clarity against any Python codebase without risk of executing malicious code.

## Example

**Input file** (`auth.py`):
```python
"""Authentication module."""

from typing import Optional
import jwt

class TokenManager:
    """Manages JWT tokens."""

    def __init__(self, secret: str):
        self.secret = secret

    def create_token(self, user_id: int) -> str:
        """Create a new JWT token."""
        return jwt.encode({"user_id": user_id}, self.secret)

async def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a token."""
    pass
```

**Output**:
```python
{
    "files": [
        {
            "path": "/path/to/auth.py",
            "functions": [
                {
                    "name": "verify_token",
                    "signature": "async def verify_token(token: str) -> Optional[dict]",
                    "docstring": "Verify and decode a token.",
                    "line_start": 16,
                    "line_end": 18,
                    "is_async": True
                }
            ],
            "classes": [
                {
                    "name": "TokenManager",
                    "signature": "class TokenManager",
                    "docstring": "Manages JWT tokens.",
                    "line_start": 6,
                    "line_end": 14,
                    "methods": [
                        {
                            "name": "__init__",
                            "signature": "def __init__(self, secret: str)",
                            "docstring": None,
                            "line_start": 9,
                            "line_end": 10,
                            "is_async": False
                        },
                        {
                            "name": "create_token",
                            "signature": "def create_token(self, user_id: int) -> str",
                            "docstring": "Create a new JWT token.",
                            "line_start": 12,
                            "line_end": 14,
                            "is_async": False
                        }
                    ],
                    "bases": []
                }
            ],
            "imports": [
                "from typing import Optional",
                "import jwt"
            ]
        }
    ]
}
```

## Failure Modes

| Exception | Cause |
|-----------|-------|
| `FileNotFoundError` | Path does not exist |
| `CodeReadError("Path is neither file nor directory: ...")` | Invalid path type |
| `CodeReadError("Failed to read file X: ...")` | Cannot read file (permissions) |
| `CodeReadError("Syntax error in X: ...")` | Python syntax error in source file |

## Known Limitations

1. **Python only** - Does not support other languages (JS, Go, etc.)
2. **Top-level only** - Nested functions/classes inside functions are not extracted
3. **No type resolution** - Type annotations are strings, not resolved types
4. **No control flow analysis** - Does not understand what code does, just structure
5. **No comment extraction** - Only docstrings, not inline comments
6. **UTF-8 only** - Other encodings will fail
7. **No .pyi stub files** - Does not merge type stubs

## Argument Handling

The `_build_arguments()` function reconstructs Python's complex argument syntax:

```
def foo(pos_only, /, regular, *args, kw_only, **kwargs)
```

- Positional-only args: Before `/` (Python 3.8+)
- Regular args: With optional defaults
- `*args`: Variable positional
- Keyword-only args: After `*` or `*args`
- `**kwargs`: Variable keyword

Defaults are right-aligned: if 3 args have 2 defaults, defaults apply to args 2 and 3.
