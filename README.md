# Clarity

**Think before you code.**

Clarity helps you understand how your planned changes fit into an existing codebase *before* you start writing code.

## The Problem

You're about to add a new feature. You've read some docs, skimmed the code, and you *think* you know what to do. But:

- What if the docs are outdated?
- What if your assumptions about the codebase are wrong?
- What if there's a constraint you missed?

These issues usually surface *after* you've written code—when fixing them is expensive.

## The Solution

Clarity reads your task description, the relevant docs, and the actual code. Then it produces a **design analysis** that shows you:

- What the system is supposed to do (from docs)
- What the code actually does (from parsing)
- Where your plan aligns or conflicts with reality
- Assumptions you've made that might be wrong
- Decisions you need to make before starting

All grounded in evidence. All with citations.

## Installation

```bash
pip install -e .
```

## Usage

### 1. Create a task context file

Write a markdown file describing what you want to do:

```markdown
## Task
Add user authentication to the API

## What I think I need to do
- Add login endpoint
- Create session management
- Store user credentials

## What I'm unsure about
- Should we use JWT or sessions?
- Where should passwords be hashed?

## Constraints I know
- Must work with existing PostgreSQL database

## Things I'm assuming
- Users already have email addresses in the system
```

### 2. Run Clarity

```bash
clarity task_context.md --docs README.md docs/api.md --code src/
```

### 3. Read the output

Clarity generates `.clarity/scratch/design_analysis.md` with:

1. **System Intent** - What the docs say the system should do
2. **Observed Reality** - What the code actually does
3. **Feature Fit** - Where your plan aligns or conflicts
4. **Assumptions & Risks** - Your assumptions checked against evidence
5. **Open Decisions** - Things you need to decide before coding
6. **Documentation Gaps** - Missing docs that could cause problems

## Example Output

```markdown
# Design Analysis

**Confidence:** medium | **Status:** Ready to proceed with caveats

## 1. System Intent
The API documentation describes a RESTful service with token-based auth...
**Sources:** `docs/api.md:15-23`

## 2. Observed Reality
Found `AuthService` class in `src/auth.py:12-45` with login/logout methods...

## 3. Feature Fit
**Alignments:**
- Existing session table matches your plan

**Conflicts:**
- Docs say JWT, but code uses sessions
```

## Command Reference

```bash
clarity <task_context.md> [options]

Options:
  --docs PATH [PATH ...]   Documentation files to analyze
  --code PATH [PATH ...]   Code files or directories to analyze
  --output PATH            Output path (default: .clarity/scratch/design_analysis.md)
  --dry-run                Parse inputs only, skip synthesis
```

## How It Works

```
task_context.md ─┐
                 │
docs/*.md ───────┼──▶ [Readers] ──▶ [Synthesizer] ──▶ [Writer] ──▶ design_analysis.md
                 │     (parse)       (1 LLM call)      (format)
src/*.py ────────┘
```

- **Readers** - Parse files into structured data (no AI, fully deterministic)
- **Synthesizer** - Makes one LLM call to analyze and connect the evidence
- **Writer** - Formats the analysis as markdown (no AI, fully deterministic)

## What Clarity Does NOT Do

- **Generate code** - It analyzes, not creates
- **Propose solutions** - It surfaces problems, you decide answers
- **Modify your files** - Read-only; output goes to a scratch file
- **Replace your judgment** - It presents evidence, you make decisions

## Requirements

- Python 3.10+
- An LLM client (configure your own, or use the stub for testing)

