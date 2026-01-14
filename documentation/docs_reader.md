# docs_reader.py

**Location:** `clarity/readers/docs_reader.py`

## Purpose

Deterministic parser for Markdown documentation files. Extracts document structure (headings, content, line ranges) without any LLM calls or summarization. Preserves content verbatim for precise citation.

## Inputs

A list of paths to Markdown files.

## Output

```python
{
    "documents": [
        {
            "path": "/absolute/path/to/api.md",
            "sections": [
                {
                    "heading": "API Reference",
                    "level": 1,
                    "content": "This document describes the REST API.",
                    "line_start": 1,
                    "line_end": 3
                },
                {
                    "heading": "Authentication",
                    "level": 2,
                    "content": "All requests require a Bearer token.\n\nExample:\n```\nAuthorization: Bearer <token>\n```",
                    "line_start": 5,
                    "line_end": 12
                }
            ]
        }
    ]
}
```

## Responsibilities

1. Read markdown files from disk
2. Parse headings at levels 1-3 (# to ###)
3. Extract content between headings
4. Track line numbers for each section
5. Return structured representation of all documents

## Functions

### `read_docs(paths: list[str]) -> dict`

Parse multiple Markdown documentation files into structured output.

**Parameters:**
- `paths`: List of paths to Markdown files

**Returns:**
- Dictionary with `documents` key containing list of parsed documents

**Raises:**
- `DocsReadError`: If any file cannot be read
- `FileNotFoundError`: If any file does not exist

## Data Structures

### Section

| Field | Type | Description |
|-------|------|-------------|
| `heading` | str | The heading text (without `#` markers) |
| `level` | int | Heading depth: 1 for `#`, 2 for `##`, 3 for `###` |
| `content` | str | All text between this heading and the next |
| `line_start` | int | Line number where heading appears (1-indexed) |
| `line_end` | int | Line number where section ends |

### Document

| Field | Type | Description |
|-------|------|-------------|
| `path` | str | Absolute path to the file |
| `sections` | list[Section] | List of parsed sections |

## What It Does NOT Do

- Does not summarize - content preserved verbatim
- Does not interpret - no judgment about importance
- Does not merge sections - each file's sections stay separate
- Does not use LLMs - pure deterministic parsing
- Does not validate content - empty sections are valid
- Does not parse beyond `###` - deeper headings treated as content
- Does not handle YAML front matter - treated as content before first heading

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | A specified file does not exist |
| `DocsReadError` | A path is not a file, or file cannot be read |

## Usage

```python
from clarity.readers import read_docs, DocsReadError

try:
    result = read_docs([
        "docs/api.md",
        "docs/architecture.md",
        "README.md"
    ])

    for doc in result["documents"]:
        print(f"File: {doc['path']}")
        for section in doc["sections"]:
            print(f"  [{section['level']}] {section['heading']}")
            print(f"      Lines {section['line_start']}-{section['line_end']}")

except FileNotFoundError as e:
    print(f"Missing file: {e}")
except DocsReadError as e:
    print(f"Read error: {e}")
```

## Notes

- Documentation is treated as authoritative system intent
- Line numbers enable precise citations in analysis output
- Content is preserved exactly for downstream filtering by relevance
- Empty path list returns `{"documents": []}`
