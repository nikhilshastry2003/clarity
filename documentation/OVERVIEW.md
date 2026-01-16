# Clarity - Overview

## What Clarity Is

Clarity is a **task-scoped design analysis tool** that helps developers understand how their planned changes fit into an existing codebase before implementation begins.

Given a developer's task context (what they want to build, their assumptions, constraints), along with relevant documentation and code, Clarity produces a **grounded mental model** - a structured analysis that:

- Extracts system intent from documentation
- Observes actual code reality (functions, classes, patterns)
- Identifies alignments and conflicts between intent and reality
- Flags risky assumptions the developer may have made
- Surfaces open decisions that need resolution
- Highlights documentation gaps

## What Problem It Solves

**The Understanding Gap**: Developers often start implementation with incomplete or incorrect mental models of the codebase. This leads to:

- Building features that conflict with existing architecture
- Making assumptions that turn out to be wrong
- Missing important constraints buried in documentation
- Discovering integration issues late in development

**Clarity closes this gap** by forcing a structured analysis phase before code is written. It synthesizes scattered information (docs, code, developer intent) into a single, coherent assessment.

## What Clarity Does NOT Do

Clarity is intentionally limited in scope:

1. **Does NOT generate code** - It analyzes, it does not create.

2. **Does NOT propose solutions** - It surfaces problems and decisions, not answers.

3. **Does NOT modify files** - Read-only operations only; output goes to a scratch file.

4. **Does NOT replace human judgment** - It presents evidence; developers decide what to do.

5. **Does NOT analyze runtime behavior** - Static analysis of source code and documentation only.

6. **Does NOT invent information** - All analysis must be grounded in provided inputs.

7. **Does NOT execute code** - The code reader uses AST parsing only (safe for untrusted code).

## Scope Boundaries

### Read-Only Philosophy

Clarity is explicitly designed as a read-only, human-in-the-loop tool. It:

- Reads files but never modifies them
- Produces analysis but never acts on it
- Requires human review before any action is taken

This philosophy is fundamental to Clarity's design - it is NOT an autonomous coding agent.

### Input Boundaries

- **Task Context**: A markdown file describing what the developer wants to do
- **Documentation**: Markdown files treated as authoritative system intent
- **Code**: Python source files parsed for structure (never executed)

### Output Boundaries

- **Single output file**: `.clarity/scratch/design_analysis.md`
- **No side effects**: No file modifications, network calls (except LLM), or system changes
- **Deterministic readers**: Same inputs always produce same parsed structures

### LLM Boundaries

The synthesizer makes exactly **one LLM call** per invocation. The LLM is:

- **Constrained by a strict prompt** that forbids inventing information
- **Required to cite sources** for all claims
- **Prohibited from proposing solutions** or next steps

### Evidence Hierarchy

When evidence conflicts, the system uses this precedence:

1. **Documentation** - Declared system intent (highest authority)
2. **Code** - Observed reality
3. **Task context assumptions** - May be wrong (lowest authority)

This hierarchy ensures that developer assumptions are checked against authoritative sources, not treated as truth.

## Determinism vs. Probabilism

A core architectural principle of Clarity is the strict separation between deterministic and probabilistic components:

| Component | Behavior |
|-----------|----------|
| Readers | **Deterministic** - Same input always produces same output |
| Synthesizer | **Probabilistic** - LLM inference (the only non-deterministic component) |
| Writers | **Deterministic** - Same input always produces same output |

This separation means:
- 90% of the codebase can be tested without LLM mocking
- Parsing bugs can be isolated from reasoning bugs
- The probabilistic component is clearly bounded

## Limitations and Known Issues

### Current Limitations

1. **Python-only code reading** - The code reader only parses `.py` files. Other languages are not supported.

2. **Markdown-only documentation** - Only Markdown files are parsed. Other formats (RST, HTML, etc.) are not supported.

3. **No incremental analysis** - Each invocation starts fresh; there is no caching or incremental update mechanism.

4. **Token limits** - Large codebases may exceed LLM context limits. The synthesizer applies truncation strategies but very large inputs may lose information.

5. **Single LLM call** - Complex analyses that might benefit from multi-turn reasoning are not supported.

### Future Considerations

The following are NOT currently implemented but may be considered:

- Support for additional programming languages
- Support for additional documentation formats
- Incremental/cached analysis
- Multi-model or multi-turn synthesis
- IDE integration

## Relationship to Other Tools

Clarity is **not** a replacement for:

- **Static analysis tools** (like pylint, mypy) - Clarity analyzes structure, not correctness
- **Documentation generators** (like Sphinx) - Clarity reads docs, it doesn't create them
- **AI coding assistants** (like Copilot) - Clarity analyzes, it doesn't generate code
- **Architecture diagramming tools** - Clarity produces text, not visualizations

Clarity **complements** these tools by providing a structured understanding phase that informs how developers use other tools.
