# synthesizer.py

**Location:** `clarity/agents/synthesizer.py`

## Purpose

Mental Model Synthesizer - the sole LLM-powered component in the Clarity pipeline. Takes structured inputs from readers and produces a grounded analysis of how the task fits into the existing system. Makes exactly ONE LLM call.

## Inputs

| Input | Source | Contains |
|-------|--------|----------|
| `task_ctx` | `read_task_context()` | Developer's task description, unknowns, constraints, assumptions |
| `docs` | `read_docs()` | Parsed documentation with sections and line ranges |
| `code` | `read_code()` | Parsed code with functions, classes, signatures |

## Output

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

## Responsibilities

1. Load the prompt template from `prompts/synthesizer.txt`
2. Format inputs into a structured prompt
3. Make a single LLM call
4. Parse the JSON response
5. Validate all required keys are present
6. Return the structured analysis

## Functions

### `synthesize(task_ctx: dict, docs: dict, code: dict) -> dict`

Synthesize inputs into a grounded mental model.

**Parameters:**
- `task_ctx`: Parsed task context from `read_task_context()`
- `docs`: Parsed documentation from `read_docs()`
- `code`: Parsed code observations from `read_code()`

**Returns:**
- Dictionary containing the mental model analysis

**Raises:**
- `SynthesisError`: If LLM client not configured, call fails, or response invalid

### `set_llm_client(client: LLMClient) -> None`

Configure the LLM client for synthesis.

### `get_llm_client() -> LLMClient`

Get the configured LLM client. Raises `SynthesisError` if not configured.

## LLMClient Interface

```python
class LLMClient:
    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Send a completion request to the LLM.

        Args:
            system_prompt: The system prompt
            user_content: The user message content

        Returns:
            The LLM response text
        """
        raise NotImplementedError("LLM client must be configured")
```

## Evidence Hierarchy

When evidence conflicts, the synthesizer prefers:

1. **Documentation** - Declared system intent
2. **Code** - Observed reality
3. **Task context assumptions** - May be wrong

## Confidence Levels

| Level | Meaning |
|-------|---------|
| `high` | Strong evidence from docs and code; few unknowns |
| `medium` | Partial evidence; some gaps but core understanding solid |
| `low` | Significant gaps; conclusions tentative |

## What It Does NOT Do

- Does not propose solutions - analysis only
- Does not design architecture - no recommendations
- Does not write code - pure analysis
- Does not resolve conflicts - reports for human decision
- Does not invent information - reasons from inputs only
- Does not make multiple LLM calls - one pass only

## Error Handling

| Error | Cause |
|-------|-------|
| `SynthesisError` | LLM client not configured, LLM call failed, response not valid JSON, or missing required keys |

## Usage

```python
from clarity.readers import read_task_context, read_docs, read_code
from clarity.agents import synthesize, set_llm_client, SynthesisError

# Configure LLM client
set_llm_client(my_llm_client)

# Read inputs
task_ctx = read_task_context("task_context.md")
docs = read_docs(["docs/api.md", "README.md"])
code = read_code(["src/"])

# Synthesize
try:
    mental_model = synthesize(task_ctx, docs, code)
    print(f"Confidence: {mental_model['confidence_assessment']['overall']}")
except SynthesisError as e:
    print(f"Synthesis failed: {e}")
```

## Notes

- Single LLM call ensures determinism and bounded cost
- Prompt template loaded from `prompts/synthesizer.txt`
- Response must be valid JSON with all required keys
- Supports markdown code blocks in LLM response (```json)
- Explicit uncertainty is preferred over false confidence
