# Clarity - Architecture

## High-Level Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│     READERS     │────▶│   SYNTHESIZER   │────▶│     WRITER      │
│                 │     │                 │     │                 │
│  (Deterministic)│     │    (LLM-based)  │     │  (Deterministic)│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   Parse inputs            Reason over            Render output
   into structured         parsed data            to markdown
   dictionaries
```

## The Three-Layer Separation

Clarity's architecture enforces a clean separation between:

1. **Readers** - Parse raw inputs into structured data
2. **Agents** - Reason over structured data (LLM-powered)
3. **Writers** - Render structured output to files

### Why This Separation Exists

#### Testability

- **Readers** can be tested with deterministic inputs/outputs
- **Writers** can be tested with mock data
- **Only the synthesizer** requires LLM mocking

#### Predictability

Readers and writers are pure functions with no LLM involvement:
- Same input file → same parsed structure (readers)
- Same analysis dict → same markdown output (writers)

The LLM is isolated to a single, controlled point.

#### Replaceability

Each layer can be swapped independently:
- Different documentation format? Replace `docs_reader`
- Different LLM provider? Implement new `LLMClient`
- Different output format? Replace `design_analysis_writer`

#### Debuggability

When something goes wrong:
- Parsing issue? Check reader output
- Bad analysis? Check LLM prompt/response
- Formatting issue? Check writer logic

## Component Details

### Readers (`clarity/readers/`)

| Reader | Input | Output |
|--------|-------|--------|
| `task_context_reader` | `task_context.md` | `dict` with task, owner, planned_approach, unknowns, constraints, assumptions |
| `docs_reader` | Markdown files | `dict` with documents, each containing sections with headings and content |
| `code_reader` | Python files/dirs | `dict` with files, each containing functions, classes, and imports |

All readers:
- Are purely deterministic (no randomness, no LLM)
- Raise specific exceptions on failure
- Return structured dictionaries

### Agents (`clarity/agents/`)

| Agent | Input | Output |
|-------|-------|--------|
| `synthesizer` | task_ctx, docs, code dicts | Mental model dict |

The synthesizer:
- Makes exactly one LLM call
- Uses a strict prompt template (`prompts/synthesizer.txt`)
- Validates output structure before returning
- Requires an `LLMClient` to be configured

### Writers (`clarity/writers/`)

| Writer | Input | Output |
|--------|-------|--------|
| `design_analysis_writer` | Analysis dict | `design_analysis.md` file |

The writer:
- Transforms structured data to markdown
- Creates parent directories as needed
- Is purely deterministic

## Entry Point

The CLI (`clarity/cli.py`) orchestrates the full pipeline:

1. Parse command-line arguments
2. Validate all input paths exist
3. Call each reader in sequence
4. Invoke the synthesizer with collected data
5. Write output via the writer

Error handling is centralized in the CLI, with each layer raising specific exceptions that are caught and reported.

## Extension Points

### Adding a New Reader

1. Create module in `clarity/readers/`
2. Export from `clarity/readers/__init__.py`
3. Add CLI argument in `clarity/cli.py`
4. Call in the main pipeline

### Adding a New Agent

1. Create module in `clarity/agents/`
2. Export from `clarity/agents/__init__.py`
3. Define prompt template in `clarity/prompts/`
4. Integrate into pipeline (may require new synthesizer step)

### Implementing an LLM Client

```python
from clarity.agents import LLMClient, set_llm_client

class MyLLMClient(LLMClient):
    def complete(self, system_prompt: str, user_content: str) -> str:
        # Call your LLM provider
        return response_text

set_llm_client(MyLLMClient())
```
