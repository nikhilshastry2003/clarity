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

Clarity's architecture enforces a strict separation between three component types:

1. **Readers** (`clarity/readers/`) - Parse raw inputs into structured data
2. **Agents** (`clarity/agents/`) - Reason over structured data (LLM-powered)
3. **Writers** (`clarity/writers/`) - Render structured output to files

### Why This Separation Exists

This separation is not arbitrary - it serves critical purposes:

#### 1. Testability

The separation enables targeted testing strategies:

- **Readers** can be tested with deterministic inputs/outputs - no mocking needed
- **Writers** can be tested with mock data - no LLM involvement
- **Only the synthesizer** requires LLM mocking or integration tests

This means ~90% of the codebase can be tested without LLM infrastructure.

#### 2. Predictability

Readers and writers are pure functions with no LLM involvement:

- Same input file → same parsed structure (readers)
- Same analysis dict → same markdown output (writers)

The LLM is isolated to a single, well-defined point. This makes debugging tractable: if output is wrong, you can determine whether the issue is parsing, reasoning, or rendering by examining intermediate representations.

#### 3. Replaceability

Each layer can be swapped independently:

- Different documentation format? → Implement new reader
- Different LLM provider? → Implement new `LLMClient`
- Different output format? → Implement new writer

The interface contracts (dictionaries with defined schemas) enable this flexibility.

#### 4. Debuggability

When something goes wrong, the three-layer structure enables precise diagnosis:

| Symptom | Investigation |
|---------|---------------|
| Missing data in output | Check reader output - is the data being parsed? |
| Wrong analysis | Check LLM prompt/response - is the reasoning correct? |
| Formatting issues | Check writer logic - is rendering correct? |

#### 5. Separation of Concerns

Each layer has a single responsibility:

- **Readers**: Transform raw bytes into structured dictionaries
- **Agents**: Perform LLM inference on structured data
- **Writers**: Transform structured data into formatted output

This prevents "leaky abstractions" where parsing logic bleeds into reasoning or rendering logic bleeds into parsing.

## Component Responsibilities

### Readers (`clarity/readers/`)

**Responsibility**: Parse input files into structured dictionaries.

**What readers MUST do**:
- Read files and extract structure
- Return consistent dictionary schemas
- Raise specific exceptions on failure
- Track line numbers for citation support

**What readers MUST NOT do**:
- Perform any reasoning or inference
- Call external services (including LLM)
- Modify any files
- Make assumptions about content meaning

| Reader | Input | Output Schema |
|--------|-------|---------------|
| `task_context_reader` | `task_context.md` | `{task, owned_by, planned_approach, unknowns, constraints, assumptions}` |
| `docs_reader` | Markdown files | `{documents: [{path, sections: [{heading, level, content, line_start, line_end}]}]}` |
| `code_reader` | Python files/dirs | `{files: [{path, functions, classes, imports}]}` |

### Agents (`clarity/agents/`)

**Responsibility**: Perform LLM-based reasoning over structured data.

**What agents MUST do**:
- Accept structured dictionaries from readers
- Make LLM calls to perform reasoning
- Return structured dictionaries for writers
- Validate LLM output structure

**What agents MUST NOT do**:
- Parse raw files (that's what readers do)
- Format output (that's what writers do)
- Invent information not in inputs
- Propose solutions or next steps

| Agent | Input | Output |
|-------|-------|--------|
| `synthesizer` | task_ctx, docs, code dicts | Mental model dict with 7 required keys |

### Writers (`clarity/writers/`)

**Responsibility**: Render structured dictionaries to output files.

**What writers MUST do**:
- Accept structured dictionaries from agents
- Produce deterministic output (same input → same output)
- Create output files with proper formatting

**What writers MUST NOT do**:
- Perform any reasoning or inference
- Call external services (including LLM)
- Read input files (that's what readers do)
- Modify input dictionaries

| Writer | Input | Output |
|--------|-------|--------|
| `design_analysis_writer` | Analysis dict | `design_analysis.md` file |

## Determinism Boundary

The **synthesizer is the only probabilistic component** in Clarity. This is a deliberate architectural decision:

```
┌──────────────────────────────────────────────────────────────────┐
│                    DETERMINISTIC ZONE                            │
│  ┌──────────────┐                           ┌──────────────┐    │
│  │   Readers    │                           │   Writers    │    │
│  │              │    ┌───────────────┐      │              │    │
│  │ • task_ctx   │───▶│  PROBABILISTIC│─────▶│ • design_    │    │
│  │ • docs       │    │               │      │   analysis   │    │
│  │ • code       │    │  Synthesizer  │      │              │    │
│  │              │    │   (LLM call)  │      │              │    │
│  └──────────────┘    └───────────────┘      └──────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Implications**:
- Readers can be tested with simple input/output assertions
- Writers can be tested with mock analysis dictionaries
- Only the synthesizer requires LLM mocking or live calls
- Parsing bugs are isolated from reasoning bugs

## LLM Client Interface

The synthesizer uses dependency injection for the LLM client:

```python
from clarity.agents import LLMClient, set_llm_client

class LLMClient:
    def complete(self, system_prompt: str, user_content: str) -> str:
        """Send a completion request and return the response text."""
        raise NotImplementedError

set_llm_client(my_client_instance)
```

This pattern enables:
- Testing with stub/mock clients
- Swapping LLM providers without code changes
- Centralized client configuration

## Entry Point (CLI)

The CLI (`clarity/cli.py`) orchestrates the full pipeline:

```
1. Parse command-line arguments
         │
         ▼
2. Validate all input paths exist
         │
         ▼
3. Call each reader in sequence
         │
         ▼
4. Invoke the synthesizer with collected data
         │
         ▼
5. Write output via the writer
```

Error handling is centralized in the CLI. Each layer raises specific exceptions that the CLI catches and converts to user-friendly messages.

## Exception Hierarchy

Each layer defines its own exception types:

| Layer | Exception | Purpose |
|-------|-----------|---------|
| Readers | `TaskContextValidationError` | Invalid task_context.md structure |
| Readers | `DocsReadError` | Cannot read documentation file |
| Readers | `CodeReadError` | Cannot read code or syntax error |
| Agents | `SynthesisError` | LLM call failed or invalid response |
| Writers | `WriteError` | Cannot write output file |

The CLI catches all of these and produces consistent error output.

## Extension Points

### Adding a New Reader

1. Create module in `clarity/readers/`
2. Define exception class for failures
3. Implement public function that returns a dictionary
4. Export from `clarity/readers/__init__.py`
5. Add CLI argument in `clarity/cli.py`
6. Call in the main pipeline

### Adding a New Agent

1. Create module in `clarity/agents/`
2. Define exception class for failures
3. Define prompt template in `clarity/prompts/`
4. Implement synthesis function
5. Export from `clarity/agents/__init__.py`
6. Integrate into pipeline

### Implementing an LLM Client

```python
from clarity.agents import LLMClient, set_llm_client

class MyLLMClient(LLMClient):
    def complete(self, system_prompt: str, user_content: str) -> str:
        # Call your LLM provider
        return response_text

set_llm_client(MyLLMClient())
```

### Adding a New Writer

1. Create module in `clarity/writers/`
2. Define exception class for failures
3. Implement public function that writes output
4. Export from `clarity/writers/__init__.py`
5. Update CLI if needed (different output format)

## Design Decisions

### Why Dictionaries Instead of Classes?

The intermediate representations between layers use plain dictionaries rather than dataclasses. This was a deliberate choice:

1. **JSON compatibility** - Dictionaries serialize naturally to JSON for debugging
2. **Flexibility** - No need to update class definitions for schema changes
3. **LLM compatibility** - LLM output is JSON, avoiding unnecessary conversion

However, the readers do use dataclasses internally (e.g., `Section`, `Document`, `FunctionInfo`) for clarity, converting to dicts at the API boundary.

### Why Single LLM Call?

The synthesizer makes exactly one LLM call per invocation. This ensures:

1. **Predictable costs** - One call = one billing event
2. **Bounded latency** - No multi-turn conversation delays
3. **Simple debugging** - One prompt, one response to examine
4. **Atomic operation** - Synthesis either succeeds or fails, no partial state

### Why Strict Prompt Constraints?

The synthesizer prompt explicitly forbids the LLM from:
- Inventing information not in inputs
- Proposing solutions or architectures
- Suggesting next steps

This keeps Clarity focused on analysis, not action - preserving its role as a human-in-the-loop tool.
