# design_analysis_writer.py

**Location:** `clarity/writers/design_analysis_writer.py`

## Purpose

Design Analysis Writer - renders the synthesis output to a markdown file. Performs no reasoning, inference, or transformation. Pure formatting only. Deterministic output.

## Inputs

The synthesis output dictionary from `synthesize()`:

- `system_intent`
- `observed_reality`
- `feature_fit`
- `assumptions_and_risks`
- `open_decisions`
- `documentation_gaps`
- `confidence_assessment`

## Output

A markdown file with these exact sections in fixed order:

1. Header with confidence assessment
2. System Intent
3. Observed Code Reality
4. Feature Fit Analysis
5. Assumptions & Risks
6. Open Decisions
7. Documentation Gaps

## Responsibilities

1. Accept synthesis dictionary
2. Render each section to markdown
3. Maintain fixed section ordering
4. Handle missing/empty data gracefully
5. Write to specified output path

## Functions

### `write_design_analysis(analysis: dict, output_path: str) -> None`

Write synthesis analysis to a markdown file.

**Parameters:**
- `analysis`: The synthesis output dictionary
- `output_path`: Path to write the markdown file

**Raises:**
- `WriteError`: If writing fails (permissions, invalid path, disk full)

## Output Format

```markdown
# Design Analysis

**Confidence:** medium | **Status:** Ready to proceed

**Limiting Factors:**
- Missing authentication documentation
- No tests found for user service

## 1. System Intent

What the system is designed to do based on documentation.

**Key Points:**
- Point from documentation

**Sources:**
- `docs/api.md:10-15`

## 2. Observed Code Reality

What the code actually shows.

**Relevant Code:**

- **`src/services/user.py`**
  - Element: `UserService`
  - Lines: 10-85
  - Relevance: Handles user operations

**Patterns Found:**
- Repository pattern used for data access

## 3. Feature Fit Analysis

### Alignments

**API structure matches task requirements**
- Evidence: Existing endpoints follow RESTful patterns
- Confidence: high

### Conflicts

**Cache implementation differs from docs** (Severity: medium)
- Documentation says: Redis-based caching
- Code shows: In-memory cache only

## 4. Assumptions & Risks

### 1. Database schema is stable

- **Source:** task_context
- **Risk if wrong:** Migrations required mid-implementation
- **Validation needed:** Check with DBA team

## 5. Open Decisions

### 1. Which authentication provider to use?

**Status:** BLOCKING

Context explaining why this matters.

**Options:**
- OAuth2 with existing provider
- New JWT implementation

## 6. Documentation Gaps

### No API versioning documentation

**Impact:** Cannot determine backward compatibility requirements

**Suggested source:** Check with API team or look at headers
```

## What It Does NOT Do

- Does not reason - pure formatting
- Does not infer - missing data stays missing
- Does not summarize - all content rendered
- Does not reorder - sections always 1-6
- Does not call LLMs - deterministic string operations
- Does not validate content - renders whatever it receives

## Error Handling

| Error | Cause |
|-------|-------|
| `WriteError` | File cannot be written (permissions, invalid path, disk full) |

## Why Strict Ordering Matters

1. **Predictability** - Engineers develop muscle memory
2. **Comparability** - Side-by-side diffs work across analyses
3. **Auditability** - Structure itself is not a variable
4. **Explicit empty sections** - Confirms section was considered, not skipped

## Usage

```python
from clarity.agents import synthesize
from clarity.writers import write_design_analysis, WriteError

# After synthesis
analysis = synthesize(task_ctx, docs, code)

# Write to file
try:
    write_design_analysis(analysis, ".clarity/scratch/design_analysis.md")
    print("Analysis written successfully")
except WriteError as e:
    print(f"Write failed: {e}")
```

## Notes

- Creates parent directories automatically
- Empty sections display placeholder text (e.g., "*No assumptions or risks identified.*")
- The synthesis dict is the source of truth; markdown is a view
- Writer cannot add or modify content from synthesis
