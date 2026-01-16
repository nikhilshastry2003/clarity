# Code Reader

**Location**: `clarity/readers/code_reader.py`

## Purpose

Reads Python source code files and extracts structural information using AST (Abstract Syntax Tree) parsing. This provides the synthesizer with code observations without executing any code.

## Input

A list of paths to:
- Individual Python files (`.py`)
- Directories (recursively searches for `.py` files)

## Output Structure

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

## Key Functions

### `read_code(paths: list[str]) -> dict`

Main entry point. Processes all provided paths.

**Behavior**:
- For files: Parses if `.py` extension
- For directories: Recursively finds all `.py` files

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

## AST Parsing Details

The reader uses Python's `ast` module for static analysis:

```python
tree = ast.parse(source, filename=str(path))
```

This means:
- **No code execution** - safe to parse untrusted code
- **Syntax errors are caught** - reported as `CodeReadError`
- **Type annotations preserved** - using `ast.unparse()`

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
                            ...
                        },
                        {
                            "name": "create_token",
                            "signature": "def create_token(self, user_id: int) -> str",
                            ...
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
