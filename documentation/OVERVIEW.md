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

## Safety and Scope Boundaries

### Input Boundaries

- **Task Context**: A markdown file describing what the developer wants to do
- **Documentation**: Markdown files treated as authoritative system intent
- **Code**: Python source files parsed for structure (not executed)

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

This hierarchy ensures that developer assumptions are checked against authoritative sources.
