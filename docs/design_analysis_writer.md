# Design Analysis Writer

## What It Does

The Design Analysis Writer takes the structured output from the Mental Model Synthesizer and renders it as a single markdown file. It performs no reasoning, inference, or transformation—only formatting.

### Input

The synthesis output dictionary containing:
- `system_intent`
- `observed_reality`
- `feature_fit`
- `assumptions_and_risks`
- `open_decisions`
- `documentation_gaps`
- `confidence_assessment`

### Output

A markdown file (`design_analysis.md`) with these exact sections in order:

1. System Intent
2. Observed Code Reality
3. Feature Fit Analysis
4. Assumptions & Risks
5. Open Decisions
6. Documentation Gaps

## Why Writing Is Separated from Reasoning

The Clarity pipeline maintains a strict separation:

```
Read → Synthesize → Write
         ↑            ↑
      reasoning    formatting
```

### Single Responsibility

The synthesizer reasons. The writer formats. Neither does both.

If the writer could "improve" the analysis—rephrase for clarity, add context, fill gaps—it would:
- Introduce a second reasoning step
- Make output unpredictable
- Obscure what came from synthesis vs. what was added

### Debuggability

When the final output looks wrong, where's the bug?

With separation:
- Wrong content → synthesizer bug
- Wrong formatting → writer bug

Without separation:
- Wrong output → could be anywhere

### Testability

The writer can be tested with fixed inputs:
```python
test_analysis = {"system_intent": {...}, ...}
output = write_design_analysis(test_analysis, "test.md")
assert "## 1. System Intent" in output
```

No LLM required. No variance. Pure function.

### Auditability

The synthesis dict is the source of truth. The markdown is a view. If you need to verify what was analyzed, check the dict. The writer cannot have added anything.

## Why This Step Is Deterministic

The writer makes exactly zero decisions.

### No Interpretation

```python
# Synthesis says:
{"aspect": "Cache TTL", "confidence": "low"}

# Writer outputs:
"- Confidence: low"
```

The writer doesn't interpret "low" as "concerning" or "needs attention." It writes "low."

### No Inference

If `assumptions_and_risks` is empty, the writer outputs:

```markdown
## 4. Assumptions & Risks

*No assumptions or risks identified.*
```

It does not infer "the system is safe" or "review needed." Empty means empty.

### No Summarization

Every item in every list is rendered. The writer doesn't decide which assumptions are "most important" or which conflicts to highlight. All data flows through.

### No LLM Calls

The writer is pure string manipulation. Given the same input, it produces the same output every time.

## Why Strict Ordering Matters for Trust

The six sections always appear in the same order:

1. System Intent
2. Observed Code Reality
3. Feature Fit Analysis
4. Assumptions & Risks
5. Open Decisions
6. Documentation Gaps

### Predictability Builds Trust

Engineers reviewing many analyses develop muscle memory. They know:
- Section 1 tells them what the system is supposed to do
- Section 2 tells them what the code actually does
- Section 3 compares them

If ordering varied, reviewers would waste time orienting themselves.

### Comparability Across Analyses

When comparing analyses for different tasks:
- Side-by-side diffs work
- Same questions appear in same places
- Patterns emerge ("we always have documentation gaps about auth")

Variable ordering would make comparison difficult.

### Auditability Over Time

If analysis ordering changed based on "importance" or "severity," you'd need to remember what logic determined order. Fixed order means the structure itself is not a variable.

### Explicit Empty Sections

When a section has no content, it still appears:

```markdown
## 6. Documentation Gaps

*No documentation gaps identified.*
```

This is intentional. It confirms the section was considered, not skipped. An absent section would be ambiguous—was it empty or missing?

## Usage

```python
from clarity.agents import synthesize
from clarity.writers import write_design_analysis, WriteError

# After synthesis
analysis = synthesize(task_ctx, docs, code)

# Write to file
try:
    write_design_analysis(analysis, ".clarity/design_analysis.md")
    print("Analysis written successfully")
except WriteError as e:
    print(f"Write failed: {e}")
```

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
- Another point

**Sources:**
- `docs/api.md:10-15`
- `README.md:5-8`

## 2. Observed Code Reality

What the code actually shows.

**Relevant Code:**

- **`src/services/user.py`**
  - Element: `UserService`
  - Lines: 10-85
  - Relevance: Handles user operations

**Patterns Found:**
- Repository pattern used for data access
- Dependency injection throughout

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

## Error Handling

| Error | Cause |
|-------|-------|
| `WriteError` | File cannot be written (permissions, invalid path, disk full) |

The writer validates nothing about the analysis content. If synthesis produced empty or malformed data, the writer renders what it received.

## What It Does NOT Do

- **Does not reason.** Pure formatting.
- **Does not infer.** Missing data stays missing.
- **Does not summarize.** All content is rendered.
- **Does not reorder.** Sections are always 1-6.
- **Does not call LLMs.** Deterministic string operations.
- **Does not validate content.** Renders whatever it receives.
