# Design Analysis Writer

**Location**: `clarity/writers/design_analysis_writer.py`

## Purpose

Renders the synthesizer's output dictionary into a human-readable Markdown file. This is the final step in the Clarity pipeline.

## Input

The analysis dictionary from `synthesize()`, containing:
- `system_intent`
- `observed_reality`
- `feature_fit`
- `assumptions_and_risks`
- `open_decisions`
- `documentation_gaps`
- `confidence_assessment`

## Output

A Markdown file at the specified path (default: `.clarity/scratch/design_analysis.md`).

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

## Key Functions

### `write_design_analysis(analysis: dict, output_path: str) -> None`

Main entry point. Renders and writes the file.

**Behavior**:
- Creates parent directories if needed
- Writes UTF-8 encoded content
- Raises `WriteError` on failure

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

### `_render_markdown(analysis: dict) -> str`

Combines all sections into the final markdown string.

## Section Details

### Header

Displays:
- Overall confidence level
- Status ("Ready to proceed" or "Needs review")
- Limiting factors as bullet list

### System Intent

Shows what documentation says the system should do:
- Summary text
- Key points as bullets
- Source citations with line numbers

### Observed Reality

Shows what the code actually contains:
- Summary text
- Relevant code locations with elements and line ranges
- Patterns identified in the codebase

### Feature Fit

Shows alignment/conflict analysis:
- **Alignments**: Where docs and code agree
- **Conflicts**: Where they disagree (with severity)

### Assumptions & Risks

Lists developer assumptions with:
- Source (task_context or inferred)
- Risk if the assumption is wrong
- How to validate

### Open Decisions

Lists decisions that need resolution:
- Status (BLOCKING or Non-blocking)
- Context explaining why it matters
- Available options

### Documentation Gaps

Lists missing documentation:
- What's missing
- How it impacts the task
- Where to find the information

## Error Handling

```python
class WriteError(Exception):
    """Raised when writing fails."""
    pass
```

Possible causes:
- Permission denied
- Disk full
- Invalid path
