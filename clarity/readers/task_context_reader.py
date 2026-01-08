"""Deterministic parser for task_context.md files."""

import re
from pathlib import Path


class TaskContextParseError(Exception):
    """Raised when task context parsing fails."""
    pass


REQUIRED_SECTIONS = {
    "Task",
    "Owned by",
    "What I think I need to do",
    "What I'm unsure about",
    "Constraints I know",
    "Things I'm assuming (might be wrong)",
}

OPTIONAL_SECTIONS = {
    "Documentation hints",
    "Suspected code areas",
}

ALL_SECTIONS = REQUIRED_SECTIONS | OPTIONAL_SECTIONS

SECTION_KEY_MAP = {
    "Task": "task",
    "Owned by": "owned_by",
    "What I think I need to do": "planned_approach",
    "What I'm unsure about": "unknowns",
    "Constraints I know": "constraints",
    "Things I'm assuming (might be wrong)": "assumptions",
    "Documentation hints": "documentation_hints",
    "Suspected code areas": "suspected_code_areas",
}


def read_task_context(path: str) -> dict:
    """
    Parse a task_context.md file into a structured dictionary.

    Args:
        path: Path to the task_context.md file

    Returns:
        Dictionary with parsed sections

    Raises:
        TaskContextParseError: If file cannot be read or required sections are missing
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Task context file not found: {path}")

    if not file_path.is_file():
        raise TaskContextParseError(f"Path is not a file: {path}")

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise TaskContextParseError(f"Failed to read file: {e}")

    return _parse_content(content)


def _parse_content(content: str) -> dict:
    """Parse markdown content into structured sections."""
    sections = _extract_sections(content)

    _validate_required_sections(sections)

    result = {}
    for section_name, section_content in sections.items():
        key = SECTION_KEY_MAP.get(section_name)
        if key:
            result[key] = _parse_section_content(section_content)

    return result


def _extract_sections(content: str) -> dict:
    """Extract sections from markdown content."""
    sections = {}

    # Match ## headers (level 2)
    header_pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

    matches = list(header_pattern.finditer(content))

    if not matches:
        raise TaskContextParseError(
            "No sections found. Expected markdown with ## headers."
        )

    for i, match in enumerate(matches):
        section_name = match.group(1).strip()

        # Only process known sections
        if section_name not in ALL_SECTIONS:
            continue

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        section_content = content[start:end].strip()
        sections[section_name] = section_content

    return sections


def _validate_required_sections(sections: dict) -> None:
    """Validate that all required sections are present."""
    found_sections = set(sections.keys())
    missing = REQUIRED_SECTIONS - found_sections

    if missing:
        missing_list = ", ".join(sorted(missing))
        raise TaskContextParseError(
            f"Missing required sections: {missing_list}"
        )


def _parse_section_content(content: str) -> str | list[str]:
    """
    Parse section content, preserving original text.

    Returns a list if content contains bullet points, otherwise a string.
    """
    if not content:
        return ""

    lines = content.split("\n")
    bullets = []
    plain_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for bullet points (-, *, or numbered)
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered_match = re.match(r"^\d+\.\s+(.+)$", stripped)

        if bullet_match:
            bullets.append(bullet_match.group(1))
        elif numbered_match:
            bullets.append(numbered_match.group(1))
        else:
            plain_lines.append(stripped)

    # If we found bullets, return as list
    if bullets:
        return bullets

    # Otherwise return as single string (joined lines)
    return "\n".join(plain_lines) if plain_lines else ""
