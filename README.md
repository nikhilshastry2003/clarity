# Clarity

A CLI tool for generating structured design analysis before implementation.

## What This Tool Does

Clarity reads task context, documentation, and code, then produces a design analysis document. It forces deliberate thinking about how a change fits into an existing codebase before writing code.

**Pipeline:**
```
Task Context → Readers → Synthesizer → Writer → design_analysis.md
```

## What This Tool Is Not

- Not a code generator
- Not an auto-pilot for implementation
- Not a replacement for understanding the codebase yourself

The output is a structured analysis to inform your decisions, not decisions made for you.

## Features

### Readers (Deterministic)

| Reader | Purpose |
|--------|---------|
| `read_task_context()` | Parse task requirements from markdown |
| `read_docs()` | Extract structured sections from documentation |
| `read_code()` | Analyze Python code structure via AST |

### Synthesizer (LLM-Powered)

- Single LLM call for analysis
- Evidence hierarchy: Docs > Code > Assumptions
- Produces structured mental model with citations

### Writer (Deterministic)

- Renders analysis to markdown
- Fixed section ordering for consistency
- No inference or interpretation

## Installation

```bash
pip install -e .
```

## Usage

```bash
clarity <task_context.md>
```

### Programmatic Usage

```python
from clarity.readers import read_task_context, read_docs, read_code
from clarity.agents import synthesize, set_llm_client
from clarity.writers import write_design_analysis

# Read inputs
task_ctx = read_task_context("task_context.md")
docs = read_docs(["docs/api.md", "README.md"])
code = read_code(["src/"])

# Configure LLM and synthesize
set_llm_client(your_llm_client)
analysis = synthesize(task_ctx, docs, code)

# Write output
write_design_analysis(analysis, "design_analysis.md")
```

## Project Structure

```
clarity/
├── clarity/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── config.py              # Configuration (placeholder)
│   ├── errors.py              # Error definitions (placeholder)
│   ├── readers/
│   │   ├── task_context_reader.py
│   │   ├── docs_reader.py
│   │   └── code_reader.py
│   ├── agents/
│   │   └── synthesizer.py     # LLM-powered analysis
│   ├── writers/
│   │   └── design_analysis_writer.py
│   └── prompts/
│       └── synthesizer.txt    # LLM prompt template
├── docs/                      # Internal documentation
├── documentation/             # Module documentation
├── pyproject.toml
└── README.md
```

## Task Context Format

```markdown
## Task
Implement user authentication

## Owned by
backend-team

## What I think I need to do
- Add login endpoint
- Create session management

## What I'm unsure about
- Which OAuth provider to use

## Constraints I know
- Must use existing database

## Things I'm assuming (might be wrong)
- Users have email addresses
```

## Output Format

The generated `design_analysis.md` contains:

1. **System Intent** - What docs say the system should do
2. **Observed Code Reality** - What code actually shows
3. **Feature Fit Analysis** - Alignments and conflicts
4. **Assumptions & Risks** - Flagged assumptions with validation needs
5. **Open Decisions** - Blocking and non-blocking decisions
6. **Documentation Gaps** - Missing information

## Design Principles

- **Separation of concerns**: Reading, reasoning, and writing are isolated
- **Determinism where possible**: Only synthesis uses LLM
- **Citations required**: All claims reference specific files and lines
- **No invention**: Analysis is grounded in provided inputs only

## Requirements

- Python 3.10+
- LLM client implementation (for synthesis)

## License

MIT
