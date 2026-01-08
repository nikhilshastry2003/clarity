# pyproject.toml

**Location:** `pyproject.toml` (project root)

## Purpose

Python project configuration file using the modern PEP 621 standard. Defines project metadata, dependencies, and build configuration.

## Contents

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "clarity"
version = "0.1.0"
description = "CLI tool for generating structured design analysis before implementation"
requires-python = ">=3.10"

[project.scripts]
clarity = "clarity.cli:main"
```

## Sections

### `[build-system]`

| Field | Value | Description |
|-------|-------|-------------|
| `requires` | `["setuptools>=61.0"]` | Build dependencies |
| `build-backend` | `setuptools.build_meta` | PEP 517 build backend |

### `[project]`

| Field | Value | Description |
|-------|-------|-------------|
| `name` | `clarity` | Package name on PyPI |
| `version` | `0.1.0` | Current version (semver) |
| `description` | CLI tool for... | Short description |
| `requires-python` | `>=3.10` | Minimum Python version |

### `[project.scripts]`

| Command | Entry Point | Description |
|---------|-------------|-------------|
| `clarity` | `clarity.cli:main` | CLI executable |

## Installation

```bash
# Development install
pip install -e .

# Build distribution
python -m build
```

## Adding Dependencies

To add runtime dependencies:

```toml
[project]
dependencies = [
    "requests>=2.28.0",
    "openai>=1.0.0",
]
```

To add development dependencies:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
```

## Notes

- Python 3.10+ is required for `list[str]` type hint syntax used in the codebase
- The `clarity` command is installed globally when the package is installed
- No external dependencies are currently declared
