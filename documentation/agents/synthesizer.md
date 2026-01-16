# Synthesizer Agent

**Location**: `clarity/agents/synthesizer.py`

## Purpose

The synthesizer is the **reasoning core** of Clarity and the **only probabilistic component** in the system. It takes structured inputs from the readers and produces a grounded mental model by making exactly one LLM call.

All LLM inference is isolated to this module. All other modules are purely deterministic.

## Inputs & Outputs

### Inputs

| Input | Type | Source |
|-------|------|--------|
| `task_ctx` | `dict` | From `read_task_context()` |
| `docs` | `dict` | From `read_docs()` |
| `code` | `dict` | From `read_code()` |

### Outputs

| Output | Type | Description |
|--------|------|-------------|
| Analysis dict | `dict` | Mental model with 7 required keys (see schema below) |

### Output Schema

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
                "confidence": "high|medium|low"
            }
        ],
        "conflicts": [
            {
                "aspect": "Session handling",
                "docs_say": "Stateless JWT",
                "code_shows": "Session table in DB",
                "severity": "high|medium|low"
            }
        ]
    },
    "assumptions_and_risks": [
        {
            "assumption": "Users will have email addresses",
            "source": "task_context|inferred",
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
        "overall": "high|medium|low",
        "limiting_factors": ["Limited documentation", "Complex codebase"],
        "sufficient_to_proceed": True
    }
}
```

## Responsibilities

The synthesizer is responsible for:

1. **LLM client management** - Store and retrieve configured client
2. **Prompt loading** - Load system prompt from template file
3. **Content formatting** - Format inputs for LLM consumption
4. **LLM invocation** - Make exactly one LLM call
5. **Response parsing** - Parse JSON from LLM response
6. **Output validation** - Verify all required keys present

## What This Module Must NOT Do

The synthesizer must NOT:

1. **Parse files** - That's what readers do; inputs are already structured
2. **Format output files** - That's what writers do
3. **Invent information** - All analysis must be grounded in inputs
4. **Propose solutions** - Only analyze, never suggest actions
5. **Make multiple LLM calls** - Exactly one call per invocation
6. **Modify input data** - Inputs are read-only

## Dependencies

### Internal Dependencies

- `clarity/prompts/synthesizer.txt` - Prompt template file

### External Dependencies

- `json` - JSON parsing (stdlib)
- `pathlib.Path` - Path operations (stdlib)

## Key Functions

### `synthesize(task_ctx: dict, docs: dict, code: dict) -> dict`

Main entry point. Orchestrates the LLM call and validates output.

**Parameters**:
- `task_ctx`: Parsed task context from reader
- `docs`: Parsed documentation from reader
- `code`: Parsed code observations from reader

**Returns**: Analysis dictionary with 7 required keys

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

### Internal Functions

| Function | Purpose |
|----------|---------|
| `_load_prompt()` | Load system prompt from template file |
| `_format_task_context()` | Format task context for prompt |
| `_format_docs()` | Format documentation for prompt |
| `_format_code()` | Format code observations with token management |
| `_build_user_content()` | Combine all formatted inputs |
| `_parse_response()` | Parse JSON from LLM response |
| `_validate_output()` | Verify required keys present |

## LLMClient Interface

```python
class LLMClient:
    def complete(self, system_prompt: str, user_content: str) -> str:
        """Send a completion request and return the response text."""
        raise NotImplementedError
```

### Implementation Example

```python
import anthropic
from clarity.agents import LLMClient, set_llm_client

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
4. Lists strict rules:
   - Never invent information
   - Always cite sources
   - Mark low confidence appropriately
   - Do not propose solutions

## Evidence Hierarchy

When evidence conflicts, the LLM is instructed to prefer:

1. **Documentation** - Declared system intent (highest authority)
2. **Code** - Observed reality
3. **Task context assumptions** - May be wrong (lowest authority)

This ensures developer assumptions are checked against authoritative sources.

## Token Management

Large codebases can exceed LLM context limits. The synthesizer applies strategic truncation in `_format_code()`:

| Element | Limit | Rationale |
|---------|-------|-----------|
| Imports | First 10 | Usually enough to understand dependencies |
| Docstrings | 200 chars | Captures intent without noise |
| Methods | First 5 per class | Covers main functionality |

## Key Principle: Grounded Reasoning

The synthesizer does NOT:
- Invent information not present in inputs
- Propose solutions or architectures
- Suggest what to do next
- Make assumptions beyond what's stated

It ONLY:
- Synthesizes existing information
- Identifies alignments and conflicts
- Flags assumptions and risks
- Cites specific sources for all claims

## Failure Modes

| Exception | Cause |
|-----------|-------|
| `SynthesisError("LLM client not configured...")` | `set_llm_client()` not called |
| `SynthesisError("Prompt template not found: ...")` | Missing synthesizer.txt |
| `SynthesisError("LLM call failed: ...")` | LLM provider error |
| `SynthesisError("Failed to parse LLM response as JSON")` | Invalid JSON from LLM |
| `SynthesisError("Synthesis output missing required keys: ...")` | Incomplete response |

## Known Limitations

1. **Single LLM call** - No multi-turn reasoning or clarification
2. **Token limits** - Very large codebases may lose information
3. **LLM provider agnostic** - Must implement `LLMClient` for each provider
4. **No streaming** - Response is returned all at once
5. **No caching** - Each invocation makes a fresh LLM call
6. **English only** - Prompt and expected output are English

## JSON Response Handling

LLMs often wrap JSON in markdown code blocks despite instructions. The `_parse_response()` function handles this:

```python
# Strips these patterns before parsing:
# ```json ... ```
# ``` ... ```
```

This robustness prevents failures due to common LLM response formatting.

## Required Output Keys

The synthesizer validates that these 7 keys are present:

1. `system_intent`
2. `observed_reality`
3. `feature_fit`
4. `assumptions_and_risks`
5. `open_decisions`
6. `documentation_gaps`
7. `confidence_assessment`

Missing keys indicate the LLM deviated from the expected format, which would break downstream rendering.
