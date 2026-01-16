# Design Analysis Writer

**Location**: `clarity/writers/design_analysis_writer.py`

## Purpose

Renders the synthesizer's output dictionary into a human-readable Markdown file. This is the final step in the Clarity pipeline.

The writer is **purely deterministic** - the same input dictionary always produces the exact same markdown output.

## Inputs & Outputs

### Inputs

| Input | Type | Description |
|-------|------|-------------|
| `analysis` | `dict` | The 7-key analysis dictionary from `synthesize()` |
| `output_path` | `str` | Path to write the output file |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| Markdown file | File | Human-readable analysis at `output_path` |

### Expected Input Keys

```python
{
    "system_intent": {...},
    "observed_reality": {...},
    "feature_fit": {...},
    "assumptions_and_risks": [...],
    "open_decisions": [...],
    "documentation_gaps": [...],
    "confidence_assessment": {...}
}
```

## Responsibilities

The writer is responsible for:

1. **Markdown rendering** - Convert analysis dict to formatted markdown
2. **Directory creation** - Create parent directories if needed
3. **File writing** - Write UTF-8 encoded content to output path
4. **Section formatting** - Apply consistent formatting to each section

## What This Module Must NOT Do

The writer must NOT:

1. **Perform reasoning** - Only format, never interpret
2. **Call external services** - No network calls, no LLM
3. **Read input files** - That's what readers do
4. **Modify the analysis dict** - Input is read-only
5. **Add non-deterministic content** - Same input = same output

## Dependencies

### Internal Dependencies

None - this is a leaf module.

### External Dependencies

- `pathlib.Path` - Path operations (stdlib)

## Key Functions

### `write_design_analysis(analysis: dict, output_path: str) -> None`

Main entry point. Renders and writes the file.

**Parameters**:
- `analysis`: The synthesis output dictionary
- `output_path`: Path to write the markdown file

**Behavior**:
- Creates parent directories if needed
- Writes UTF-8 encoded content
- Raises `WriteError` on failure

### `_render_markdown(analysis: dict) -> str`

Combines all sections into the final markdown string.

**Returns**: Complete markdown document as string

### Render Functions

Each section has a dedicated render function:

| Function | Section |
|----------|---------|
| `_render_header()` | Title, confidence, status |
| `_render_system_intent()` | Section 1 |
| `_render_observed_reality()` | Section 2 |
| `_render_feature_fit()` | Section 3 |
| `_render_assumptions_and_risks()` | Section 4 |
| `_render_open_decisions()` | Section 5 |
| `_render_documentation_gaps()` | Section 6 |

## Output Format

```markdown
# Design Analysis

**Confidence:** medium | **Status:** Ready to proceed

**Limiting Factors:**
- Limited documentation
- Complex codebase

## 1. System Intent

What the system is designed to do based on documentation.

**Key Points:**
- Point 1
- Point 2

**Sources:**
- `README.md:10-15`
- `docs/api.md:5-8`

## 2. Observed Code Reality

What the code actually shows.

**Relevant Code:**

- **`src/auth.py`**
  - Element: `TokenManager`
  - Lines: 10-25
  - Relevance: Handles authentication

**Patterns Found:**
- Repository pattern
- Dependency injection

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

## Section Details

### Header

Displays:
- Overall confidence level (`high`, `medium`, or `low`)
- Status (`Ready to proceed` if `sufficient_to_proceed` is true, else `Needs review`)
- Limiting factors as bullet list

### System Intent (Section 1)

Shows what documentation says the system should do:
- Summary text
- Key points as bullets
- Source citations with line numbers

### Observed Reality (Section 2)

Shows what the code actually contains:
- Summary text
- Relevant code locations with elements and line ranges
- Patterns identified in the codebase

### Feature Fit (Section 3)

Shows alignment/conflict analysis:
- **Alignments**: Where docs and code agree (with confidence level)
- **Conflicts**: Where they disagree (with severity level)

### Assumptions & Risks (Section 4)

Lists developer assumptions with:
- Source (`task_context` or `inferred`)
- Risk if the assumption is wrong
- How to validate

### Open Decisions (Section 5)

Lists decisions that need resolution:
- Status (`BLOCKING` or `Non-blocking`)
- Context explaining why it matters
- Available options

### Documentation Gaps (Section 6)

Lists missing documentation:
- What's missing
- How it impacts the task
- Where to find the information

## Empty Section Handling

When a section has no data, the writer displays a placeholder:

```markdown
## 4. Assumptions & Risks

*No assumptions or risks identified.*
```

This ensures consistent structure even when some sections are empty.

## Failure Modes

| Exception | Cause |
|-----------|-------|
| `WriteError("Failed to write design analysis: ...")` | Permission denied |
| `WriteError("Failed to write design analysis: ...")` | Disk full |
| `WriteError("Failed to write design analysis: ...")` | Invalid path |

The `WriteError` wraps the underlying exception message for context.

## Known Limitations

1. **Markdown only** - Does not support other output formats (HTML, PDF, etc.)
2. **Fixed structure** - Cannot customize section order or content
3. **No templating** - Layout is hardcoded in render functions
4. **English only** - Labels and formatting assume English
5. **No syntax highlighting** - Code references are plain backticks

## Design Philosophy: Scannability

The output format prioritizes quick scanning:

- **Confidence at top** - Most important info first
- **Numbered sections** - Easy navigation and reference
- **Bullet lists** - Faster to scan than prose
- **Bold labels** - Visual hierarchy
- **Code in backticks** - Clear file/code references
- **Severity/status visible** - Key metadata not buried

## Determinism Guarantee

The writer is strictly deterministic:

```python
# These will produce identical output:
write_design_analysis(analysis1, "out1.md")
write_design_analysis(analysis1, "out2.md")

# out1.md and out2.md will be byte-for-byte identical
```

This property enables:
- Reliable testing with expected output comparison
- Reproducible documentation generation
- Cache-friendly output (same input = same hash)
