# Docs Reader

**Location**: `clarity/readers/docs_reader.py`

## Purpose

Parses Markdown documentation files into structured output. Each file is split into sections based on headings, with line number tracking for citations.

## Input

A list of paths to Markdown files.

## Output Structure

```python
{
    "documents": [
        {
            "path": "/absolute/path/to/file.md",
            "sections": [
                {
                    "heading": "Section Title",
                    "level": 1,        # 1 for #, 2 for ##, 3 for ###
                    "content": "Section content...",
                    "line_start": 1,
                    "line_end": 15
                }
            ]
        }
    ]
}
```

## Key Functions

### `read_docs(paths: list[str]) -> dict`

Main entry point. Parses all provided documentation files.

**Returns**: Dictionary with `documents` key containing list of parsed documents.

**Raises**:
- `FileNotFoundError`: File does not exist
- `DocsReadError`: Path is not a file or cannot be read

### `_read_single_doc(path: str) -> Document`

Reads and parses a single Markdown file.

### `_parse_sections(content: str) -> list[Section]`

Splits content into sections based on Markdown headings (`#`, `##`, `###`).

## Section Detection

The parser recognizes headings up to level 3:

| Pattern | Level |
|---------|-------|
| `# Heading` | 1 |
| `## Heading` | 2 |
| `### Heading` | 3 |

Headings beyond level 3 are treated as content within the current section.

## Line Number Tracking

Each section includes:
- `line_start`: Line number where the heading appears
- `line_end`: Last line of the section content

This enables the synthesizer to cite specific locations in documentation.

## Data Classes

### `Section`

```python
@dataclass
class Section:
    heading: str      # The heading text
    level: int        # 1, 2, or 3
    content: str      # Content between this heading and the next
    line_start: int   # Line number of heading
    line_end: int     # Last line of section
```

### `Document`

```python
@dataclass
class Document:
    path: str                # Absolute path to file
    sections: list[Section]  # Parsed sections
```

## Example

**Input file** (`README.md`):
```markdown
# Overview

This is the overview.

## Getting Started

Installation instructions here.

### Prerequisites

You need Python 3.10+.
```

**Output**:
```python
{
    "documents": [
        {
            "path": "/path/to/README.md",
            "sections": [
                {
                    "heading": "Overview",
                    "level": 1,
                    "content": "This is the overview.",
                    "line_start": 1,
                    "line_end": 4
                },
                {
                    "heading": "Getting Started",
                    "level": 2,
                    "content": "Installation instructions here.",
                    "line_start": 5,
                    "line_end": 8
                },
                {
                    "heading": "Prerequisites",
                    "level": 3,
                    "content": "You need Python 3.10+.",
                    "line_start": 9,
                    "line_end": 11
                }
            ]
        }
    ]
}
```
