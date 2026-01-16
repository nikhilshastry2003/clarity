# Synthesizer Agent

**Location**: `clarity/agents/synthesizer.py`

## Purpose

The synthesizer is the reasoning core of Clarity. It takes structured inputs from the readers and produces a grounded mental model by making exactly one LLM call.

## Key Principle: Grounded Reasoning

The synthesizer does NOT:
- Invent information not present in inputs
- Propose solutions or architectures
- Suggest what to do next

It ONLY:
- Synthesizes existing information
- Identifies alignments and conflicts
- Flags assumptions and risks
- Cites specific sources for all claims

## Input

Three dictionaries from the readers:

1. **task_ctx**: From `read_task_context()`
2. **docs**: From `read_docs()`
3. **code**: From `read_code()`

## Output Structure

```python
{
    "system_intent": {
        "summary": "What the system is designed to do",
        "key_points": ["point 1", "point 2"],
        "citations": ["README.md:10-15", "docs/api.md:5-8"]
    },
    "observed_reality": {
        "summary": "What the code actually shows",
        "relevant_code": [
            {
                "path": "src/auth.py",
                "element": "TokenManager",
                "lines": "10-25",
                "relevance": "Handles authentication"
            }
        ],
        "patterns_found": ["Repository pattern", "Dependency injection"]
    },
    "feature_fit": {
        "alignments": [
            {
                "aspect": "Authentication approach",
                "evidence": "Docs specify JWT, code uses jwt library",
                "confidence": "high"
            }
        ],
        "conflicts": [
            {
                "aspect": "Session handling",
                "docs_say": "Stateless JWT",
                "code_shows": "Session table in DB",
                "severity": "medium"
            }
        ]
    },
    "assumptions_and_risks": [
        {
            "assumption": "Users will have email addresses",
            "source": "task_context",
            "risk_if_wrong": "Registration flow breaks",
            "validation_needed": "Check user model"
        }
    ],
    "open_decisions": [
        {
            "decision": "Which OAuth provider to use",
            "options": ["Google", "GitHub", "Both"],
            "blocking": True,
            "context": "Affects callback URL configuration"
        }
    ],
    "documentation_gaps": [
        {
            "gap": "Error handling strategy",
            "impact": "Unknown how to handle auth failures",
            "suggested_source": "Ask team lead"
        }
    ],
    "confidence_assessment": {
        "overall": "medium",
        "limiting_factors": ["Limited documentation", "Complex codebase"],
        "sufficient_to_proceed": True
    }
}
```

## Key Functions

### `synthesize(task_ctx, docs, code) -> dict`

Main entry point. Orchestrates the LLM call and validates output.

**Process**:
1. Get configured LLM client
2. Load prompt template
3. Build user content from inputs
4. Call LLM
5. Parse JSON response
6. Validate required keys

### `set_llm_client(client: LLMClient) -> None`

Configure the LLM client. Must be called before `synthesize()`.

### `get_llm_client() -> LLMClient`

Get the configured client. Raises `SynthesisError` if not configured.

## LLMClient Interface

```python
class LLMClient:
    def complete(self, system_prompt: str, user_content: str) -> str:
        """Send a completion request and return the response text."""
        raise NotImplementedError
```

To use Clarity, implement this interface for your LLM provider:

```python
class AnthropicClient(LLMClient):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system_prompt: str, user_content: str) -> str:
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}]
        )
        return response.content[0].text

set_llm_client(AnthropicClient(os.environ["ANTHROPIC_API_KEY"]))
```

## Prompt Template

**Location**: `clarity/prompts/synthesizer.txt`

The prompt:
1. Establishes the analyst role
2. Defines the evidence hierarchy (docs > code > assumptions)
3. Specifies exact output JSON structure
4. Lists strict rules (no inventing, cite sources, etc.)

## Evidence Hierarchy

When evidence conflicts, the LLM is instructed to prefer:

1. **Documentation** - Declared system intent (highest authority)
2. **Code** - Observed reality
3. **Task context assumptions** - May be wrong (lowest authority)

## Token Management

The synthesizer limits content to prevent token overflow:
- Imports: First 10 shown, remainder counted
- Docstrings: Truncated to 200 characters
- Methods: First 5 shown per class

## Error Handling

| Exception | Cause |
|-----------|-------|
| `SynthesisError("LLM client not configured")` | `set_llm_client()` not called |
| `SynthesisError("Prompt template not found")` | Missing `prompts/synthesizer.txt` |
| `SynthesisError("LLM call failed: ...")` | LLM provider error |
| `SynthesisError("Failed to parse LLM response as JSON")` | Invalid JSON response |
| `SynthesisError("Synthesis output missing required keys")` | Incomplete response |
