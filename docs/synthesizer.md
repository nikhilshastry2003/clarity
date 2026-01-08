# Mental Model Synthesizer

## What It Does

The Synthesizer is the first reasoning step in the Clarity pipeline. It takes three structured inputs—task context, documentation, and code observations—and produces a grounded mental model of how the task fits into the existing system.

### Inputs

| Input | Source | Contains |
|-------|--------|----------|
| `task_ctx` | `read_task_context()` | Developer's task description, unknowns, constraints, assumptions |
| `docs` | `read_docs()` | Parsed documentation with sections and line ranges |
| `code` | `read_code()` | Parsed code with functions, classes, signatures |

### Output

```python
{
    "system_intent": {
        "summary": "What the system is designed to do",
        "key_points": [...],
        "citations": ["docs/api.md:10-15", ...]
    },
    "observed_reality": {
        "summary": "What the code actually shows",
        "relevant_code": [...],
        "patterns_found": [...]
    },
    "feature_fit": {
        "alignments": [...],
        "conflicts": [...]
    },
    "assumptions_and_risks": [...],
    "open_decisions": [...],
    "documentation_gaps": [...],
    "confidence_assessment": {
        "overall": "high|medium|low",
        "limiting_factors": [...],
        "sufficient_to_proceed": true|false
    }
}
```

## Why Synthesis Is Separate from Writing

The pipeline deliberately separates understanding from doing:

```
Read → Synthesize → (future: Write)
```

### Analysis and Implementation Are Different Skills

Understanding a system requires:
- Identifying patterns
- Detecting conflicts
- Surfacing risks
- Citing evidence

Implementing changes requires:
- Designing solutions
- Writing code
- Making trade-offs
- Handling edge cases

Combining these creates muddled output. The synthesizer focuses purely on understanding.

### Separation Enables Review

When synthesis is separate, engineers can review the mental model before any changes are proposed:

- "Does the system intent match my understanding?"
- "Did it find the right code areas?"
- "Are these the real risks?"

If analysis is bundled with recommendations, reviewers must untangle "what was understood" from "what was decided."

### Garbage In, Garbage Out

If synthesis is wrong, any downstream recommendations will be wrong. By isolating synthesis:

1. Errors are caught early
2. The source of errors is clear
3. Fixes don't require re-running the entire pipeline

### Different Confidence Thresholds

Synthesis can operate with incomplete information. It explicitly reports:
- What it knows with confidence
- What it's uncertain about
- What's missing

Implementation proposals require higher confidence. Keeping them separate means the synthesizer can say "I don't have enough information" without blocking the entire workflow.

## Why Reasoning Is Limited to One Pass

The synthesizer makes exactly ONE LLM call. This is intentional.

### Determinism and Reproducibility

Multiple LLM calls create compounding variance. Each call can produce different output. With one call:
- Output is more predictable
- Debugging is easier
- Cost is bounded

### Forcing Completeness of Input

If the synthesizer could "ask for more information" via additional calls, it would mask input quality issues. One pass forces:
- Readers to provide complete data
- Prompts to be well-designed
- Inputs to be sufficient

### Preventing Hallucination Loops

Multiple passes allow the LLM to build on its own outputs. If pass 1 hallucinates a fact, pass 2 might elaborate on it. One pass limits this risk.

### Bounded Cost and Latency

One call = predictable cost. With multiple calls, costs vary unpredictably based on how the LLM decides to explore.

### Encouraging Explicit Uncertainty

With one pass, the synthesizer must express uncertainty in its output rather than trying to resolve it. This surfaces gaps to the human reviewer.

## How Confidence Is Assessed

The synthesizer outputs a `confidence_assessment`:

```python
{
    "overall": "medium",
    "limiting_factors": [
        "No documentation found for authentication flow",
        "Task mentions 'caching' but no cache code found"
    ],
    "sufficient_to_proceed": true
}
```

### Confidence Levels

| Level | Meaning |
|-------|---------|
| `high` | Strong evidence from docs and code; few unknowns |
| `medium` | Partial evidence; some gaps but core understanding is solid |
| `low` | Significant gaps; conclusions are tentative |

### Limiting Factors

Explicit list of what's reducing confidence:
- Missing documentation
- Code that doesn't match docs
- Unverified assumptions from task context
- Ambiguous requirements

### Sufficient to Proceed

Boolean indicating whether downstream steps should continue. Even `low` confidence might be sufficient if the task is exploratory.

## Evidence Hierarchy

When evidence conflicts, the synthesizer prefers:

1. **Documentation** — Declared system intent
2. **Code** — Observed reality
3. **Task context assumptions** — May be wrong

### Example Conflict

Task context says: "We use Redis for caching"
Documentation says: "Caching layer uses Memcached"
Code shows: No caching implementation exists

The synthesizer reports:
- Documentation claims Memcached (citation)
- Code shows no caching (citation)
- Task assumption of Redis conflicts with docs
- This is flagged as a conflict + documentation gap

## What It Does NOT Do

- **Does not propose solutions.** No "you should add a cache here."
- **Does not design architecture.** No "consider using the Strategy pattern."
- **Does not write code.** Pure analysis.
- **Does not resolve conflicts.** Reports them for human decision.
- **Does not invent information.** Only reasons from inputs.
- **Does not make multiple LLM calls.** One pass only.

## Usage

```python
from clarity.readers import read_task_context, read_docs, read_code
from clarity.agents import synthesize, set_llm_client, SynthesisError

# Configure LLM client (implementation-specific)
set_llm_client(my_llm_client)

# Read inputs
task_ctx = read_task_context("task_context.md")
docs = read_docs(["docs/api.md", "README.md"])
code = read_code(["src/"])

# Synthesize
try:
    mental_model = synthesize(task_ctx, docs, code)

    print(f"Confidence: {mental_model['confidence_assessment']['overall']}")

    if mental_model['feature_fit']['conflicts']:
        print("Conflicts found:")
        for conflict in mental_model['feature_fit']['conflicts']:
            print(f"  - {conflict['aspect']}")

except SynthesisError as e:
    print(f"Synthesis failed: {e}")
```

## LLM Client Configuration

The synthesizer requires an LLM client to be configured:

```python
from clarity.agents import LLMClient, set_llm_client

class MyLLMClient(LLMClient):
    def complete(self, system_prompt: str, user_content: str) -> str:
        # Your LLM implementation here
        return response

set_llm_client(MyLLMClient())
```

The `LLMClient` interface has a single method:
- `complete(system_prompt, user_content) -> str`

This abstraction allows any LLM provider to be used.

## Error Handling

| Error | Cause |
|-------|-------|
| `SynthesisError` | LLM client not configured, LLM call failed, or response parsing failed |

The synthesizer validates that all required output keys are present. If the LLM produces malformed output, a `SynthesisError` is raised.
