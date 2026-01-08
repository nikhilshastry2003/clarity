# Documentation Reader

## What It Does

The Documentation Reader parses Markdown files and extracts their structure: headings, content, and line ranges. It produces a deterministic representation of documentation that can be referenced precisely.

### Input

A list of paths to Markdown files.

### Output

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

## Why Documentation Is Authoritative

Documentation represents **declared system intent**. When a README says "this service handles user authentication," that statement carries weight regardless of what the code currently does.

In the Clarity pipeline, documentation serves as:

1. **Ground truth for design decisions.** If docs say "we use JWT for sessions," that's a constraint, not a suggestion.
2. **Context for code analysis.** Code without documentation is ambiguous. Code with documentation has stated purpose.
3. **Source for citations.** When Clarity explains why something matters, it can point to specific documentation lines.

The reader treats documentation as authoritative because:
- It was written by humans with system knowledge
- It represents intentional communication about the system
- It should be preserved exactly as written, not reinterpreted

## Why No Summarization

Summarization would destroy the reader's value. Here's why:

### Loss of Precision

Original: "The cache TTL must not exceed 300 seconds due to GDPR compliance requirements."

Summarized: "Cache has time limits."

The summary loses the specific value (300s) and the reason (GDPR). Both are critical for downstream analysis.

### Loss of Citation Ability

If we summarize, we can no longer say: "See api.md, lines 45-48." The original text is gone.

### Introduced Interpretation

Summarization requires deciding what's important. That's interpretation. This reader deliberately avoids interpretation because:
- Importance depends on the task (unknown at read time)
- Human authors chose their words deliberately
- Downstream stages can filter; this stage should not

### Determinism

Summarization (especially LLM-based) can produce different outputs for the same input. This reader produces identical output every time.

## How This Output Is Used Later

The structured documentation output enables several downstream operations:

### Citation Generation

When Clarity explains a recommendation, it can cite:
```
Based on authentication requirements (see docs/security.md:23-31)
```

The `line_start` and `line_end` fields make this possible.

### Relevance Filtering

Later stages can filter sections by heading or content to find documentation relevant to a specific task. The structure makes this filtering fast and precise.

### Hierarchy Understanding

The `level` field (1 for `#`, 2 for `##`, 3 for `###`) preserves document structure. A level-2 heading under a level-1 heading is contextually related.

### Multi-Document Analysis

Each document is kept separate (`documents` is a list). This prevents accidental mixing of unrelated documentation and enables per-file attribution.

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

## What It Does NOT Do

- **Does not summarize.** Content is preserved verbatim.
- **Does not interpret.** No judgment about importance or relevance.
- **Does not merge sections.** Each file's sections stay with that file.
- **Does not use LLMs.** Pure deterministic parsing.
- **Does not validate content.** Empty sections are valid.
- **Does not parse beyond `###`.** Deeper headings (####, #####) are treated as content.
- **Does not handle front matter.** YAML front matter is treated as content before the first heading.

## Error Handling

| Error | Cause |
|-------|-------|
| `FileNotFoundError` | A specified file does not exist |
| `DocsReadError` | A path is not a file, or file cannot be read |

## Section Structure

| Field | Type | Description |
|-------|------|-------------|
| `heading` | `str` | The heading text (without `#` markers) |
| `level` | `int` | Heading depth: 1 for `#`, 2 for `##`, 3 for `###` |
| `content` | `str` | All text between this heading and the next |
| `line_start` | `int` | Line number where heading appears (1-indexed) |
| `line_end` | `int` | Line number where section ends |
