"""
Deterministic parser for task_context.md files.

This module provides pure, deterministic parsing of markdown task context files.
No LLM calls are made. Same input always produces same output.

The parser extracts structured data from markdown sections, preserving original
text exactly as written without summarization or interpretation.
"""

import re
from pathlib import Path


class TaskContextValidationError(Exception):
    """
    Raised when task context validation fails.

    This indicates the input file is missing required sections
    or has structural problems that prevent parsing.
    """
    pass


# Section header mappings: markdown header -> output key
# These are the exact headers the parser looks for (case-sensitive)
REQUIRED_SECTIONS = {
    "Task": "task",
    "Owned by": "owned_by",
    "What I think I need to do": "planned_approach",
    "What I'm unsure about": "unknowns",
    "Constraints I know": "constraints",
    "Things I'm assuming (might be wrong)": "assumptions",
}

OPTIONAL_SECTIONS = {
    "Documentation hints": "documentation_hints",
    "Suspected code areas": "suspected_code_areas",
}

# Sections that should be parsed as lists (bullet points)
LIST_SECTIONS = {
    "planned_approach",
    "unknowns",
    "constraints",
    "assumptions",
    "documentation_hints",
    "suspected_code_areas",
}


def read_task_context(path: str) -> dict:
    """
    Parse a task_context.md file into a structured dictionary.

    This function reads a markdown file and extracts structured data from
    predefined sections. It performs validation to ensure required sections
    are present.

    Args:
        path: Path to the task_context.md file

    Returns:
        Dictionary with parsed sections:
        - task: str - The task description
        - owned_by: str - Team or person responsible
        - planned_approach: list[str] - What the developer plans to do
        - unknowns: list[str] - What the developer is unsure about
        - constraints: list[str] - Known constraints
        - assumptions: list[str] - Assumptions that might be wrong
        - documentation_hints: list[str] (optional) - Where to look in docs
        - suspected_code_areas: list[str] (optional) - Suspected relevant code

    Raises:
        TaskContextValidationError: If required sections are missing
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Task context file not found: {path}")

    if not file_path.is_file():
        raise TaskContextValidationError(f"Path is not a file: {path}")

    content = file_path.read_text(encoding="utf-8")
    return _parse_content(content)


def _parse_content(content: str) -> dict:
    """
    Parse markdown content into structured sections.

    Extracts sections based on ## headers and maps them to output keys.
    List sections are parsed as bullet points, text sections are kept as strings.
    """
    sections = _extract_sections(content)

    # Build result dict from required sections
    result = {}

    for header, key in REQUIRED_SECTIONS.items():
        raw_content = sections.get(header, "")
        if key in LIST_SECTIONS:
            result[key] = _parse_list(raw_content)
        else:
            result[key] = raw_content.strip()

    # Add optional sections if present
    for header, key in OPTIONAL_SECTIONS.items():
        if header in sections:
            result[key] = _parse_list(sections[header])

    # Validate required fields
    _validate(result)

    return result


def _extract_sections(content: str) -> dict:
    """
    Extract sections from markdown content based on ## headers.

    Sections are identified by level-2 headers (##). Content between
    one header and the next (or end of file) belongs to that section.
    """
    sections = {}

    # Match ## headers (level 2 only)
    header_pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    matches = list(header_pattern.finditer(content))

    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        # Section ends at next header or end of content
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_content = content[start:end].strip()
        sections[section_name] = section_content

    return sections


def _parse_list(content: str) -> list[str]:
    """
    Parse content as a list of bullet points.

    Supports both dash (-) and asterisk (*) bullet markers,
    as well as numbered lists (1., 2., etc.).
    Only extracts top-level bullets; nested bullets are ignored.
    """
    if not content:
        return []

    items = []
    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Match bullet points (-, *)
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        # Match numbered lists (1., 2., etc.)
        numbered_match = re.match(r"^\d+\.\s+(.+)$", stripped)

        if bullet_match:
            items.append(bullet_match.group(1))
        elif numbered_match:
            items.append(numbered_match.group(1))

    return items


def _validate(result: dict) -> None:
    """
    Validate the parsed result has all required content.

    Raises TaskContextValidationError if:
    - Task description is empty
    - Owner is not specified
    - Planned approach is empty (must have at least one item)
    """
    errors = []

    # Task and owned_by are required text fields
    if not result.get("task"):
        errors.append("'Task' section is required and cannot be empty")

    if not result.get("owned_by"):
        errors.append("'Owned by' section is required and cannot be empty")

    # Planned approach must have at least one item
    if not result.get("planned_approach"):
        errors.append("'What I think I need to do' must contain at least one item")

    if errors:
        raise TaskContextValidationError("; ".join(errors))
