# Docs Reader

**Location**: `clarity/readers/docs_reader.py`

## Purpose

Parses Markdown documentation files into structured output. Each file is split into sections based on headings, with line number tracking for citations.

Documentation is treated as **authoritative system intent** - the highest priority evidence source in Clarity's evidence hierarchy.

## Inputs & Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `paths` | `list[str]` | List of paths to Markdown files |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| Documents dict | `dict` | Dictionary with `documents` key containing parsed files |

### Output Schema

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

## Responsibilities

The docs_reader is responsible for:

1. **File reading** - Read UTF-8 content from specified paths
2. **Section detection** - Identify headings at levels 1-3
3. **Content extraction** - Capture content between headings
4. **Line tracking** - Record start/end line numbers for citations
5. **Path resolution** - Convert relative paths to absolute

## What This Module Must NOT Do

The docs_reader must NOT:

1. **Interpret content** - Only parse structure, not meaning
2. **Perform reasoning** - That's the synthesizer's job
3. **Call external services** - No network calls, no LLM
4. **Modify files** - Read-only operation
5. **Parse non-Markdown** - Only `.md` files supported

## Dependencies

### Internal Dependencies

None - this is a leaf module.

### External Dependencies

- `re` - Regular expressions for heading detection (stdlib)
- `pathlib.Path` - Path operations (stdlib)
- `dataclasses` - Data class definitions (stdlib)

## Key Functions

### `read_docs(paths: list[str]) -> dict`

Main entry point. Parses all provided documentation files.

**Parameters**:
- `paths`: List of file paths to Markdown files

**Returns**: Dictionary with `documents` key containing list of parsed documents.

**Raises**:
- `FileNotFoundError`: File does not exist
- `DocsReadError`: Path is not a file or cannot be read

### `_read_single_doc(path: str) -> Document`

Reads and parses a single Markdown file.

**Parameters**:
- `path`: Path to a single Markdown file

**Returns**: `Document` dataclass instance

### `_parse_sections(content: str) -> list[Section]`

Splits content into sections based on Markdown headings (`#`, `##`, `###`).

**Parameters**:
- `content`: Raw file content as string

**Returns**: List of `Section` dataclass instances

## Data Classes

### `Section`

```python
@dataclass
class Section:
    heading: str      # The heading text (without # markers)
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

Both classes implement `to_dict()` methods for serialization.

## Heading Level Behavior

The parser recognizes headings up to level 3:

| Pattern | Level | Behavior |
|---------|-------|----------|
| `# Heading` | 1 | Creates new section |
| `## Heading` | 2 | Creates new section |
| `### Heading` | 3 | Creates new section |
| `#### Heading` | 4+ | Becomes part of current section content |

**Rationale**: Deeper headings (`####` etc.) are treated as content to prevent over-fragmentation. Most documents use levels 1-3 for major structure.

## Line Number Tracking

Each section includes:
- `line_start`: Line number where the heading appears (1-indexed)
- `line_end`: Last line of the section content

This enables the synthesizer to cite specific locations like `README.md:10-25`.

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

## Failure Modes

| Exception | Cause |
|-----------|-------|
| `FileNotFoundError` | File does not exist at specified path |
| `DocsReadError("Path is not a file: ...")` | Path points to a directory |
| `DocsReadError("Failed to read file X: ...")` | File exists but cannot be read (permissions, encoding) |

## Known Limitations

1. **Markdown only** - Does not support RST, HTML, or other formats
2. **No frontmatter parsing** - YAML frontmatter is treated as content
3. **No link resolution** - Does not follow or validate links
4. **No code block detection** - Headings inside code blocks may be incorrectly parsed
5. **UTF-8 only** - Other encodings will fail
6. **Empty path list** - Returns `{"documents": []}` (not an error)

## Parsing Algorithm

```python
heading_pattern = r"^(#{1,3})\s+(.+?)\s*$"

for line_num, line in enumerate(lines, start=1):
    if matches heading_pattern:
        # Save previous section
        # Start new section with heading, level, line_num
    else:
        # Append to current section content

# Save final section
```

The algorithm is single-pass, O(n) where n = number of lines.
