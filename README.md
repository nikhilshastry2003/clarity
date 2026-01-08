# clarity

A CLI tool for generating structured design analysis before implementation.

## What This Tool Does

clarity reads task context (requirements, documentation, selected code) and produces a design analysis document. The intent is to force deliberate thinking about how a change fits into an existing codebase before writing code.

## What This Tool Is Not

- Not a code generator
- Not an auto-pilot for implementation
- Not a replacement for understanding the codebase yourself

The output is a structured analysis to inform your decisions, not decisions made for you.

## Current State

**Step 1 complete.** The CLI skeleton exists with:

- Argument parsing
- Input validation
- Folder structure

### Not Yet Implemented

- Code analysis
- Documentation parsing
- design_analysis.md generation
- Any integration with language models

This is scaffolding only. The tool currently validates inputs and exits.

## Installation

```
pip install -e .
```

## Usage

```
clarity <task_context.md> --docs <files...> --code <dirs...>
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `task_context.md` | Path to task context file (positional) |

### Optional Arguments

| Argument | Description |
|----------|-------------|
| `--docs` | Documentation files to include |
| `--code` | Code directories to analyze |

## Project Structure

```
clarity/
├── clarity/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── errors.py
├── pyproject.toml
├── README.md
└── task_context.md
```

## Development

```
pip install -e .
clarity --help
```

## Limitations

1. **No analysis engine exists yet.** The tool parses arguments and validates paths. That's it.
2. **No output generation.** Analysis output is not implemented.
3. **No configuration support.** Config loading is not implemented.
