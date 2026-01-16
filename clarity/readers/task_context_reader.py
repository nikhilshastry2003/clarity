"""
TaskContextReader - A robust parser for task_context.md files.

Expected File Format:
---------------------
The parser expects a Markdown file with the following sections:

Required sections:
  - Task (or "# Task" or "## Task") - single value
  - Owned by (or "# Owned by") - single value
  - What I think I need to do - list section, must have at least 1 item

Optional sections:
  - What I'm unsure about - list section
  - Constraints I know - list section
  - Things I'm assuming (might be wrong) - list section

Section headers can be:
  - Plain text: "Task:" or "Task:"
  - Markdown headers: "# Task" or "## Task"
  - Case-insensitive: "TASK:", "task:", "Task:" all work

List items can use:
  - Dash bullets: "- item"
  - Asterisk bullets: "* item"
  - Numbered lists: "1. item"
  - Plain paragraphs (non-bullet text under a section)

Example valid file:
-------------------
# Task Context

Task: Build a user authentication system

Owned by: Backend Team

What I think I need to do:
- Implement login endpoint
- Add JWT token generation
- Create user session management

What I'm unsure about:
- OAuth integration details
- Session timeout requirements

Constraints I know:
- Must use existing database schema
- No third-party auth services

Things I'm assuming (might be wrong):
- Users will have email addresses
- Single sign-on is not needed
"""

import re
from pathlib import Path
from typing import Optional


class TaskContextValidationError(Exception):
    """
    Raised when task context validation fails.

    This indicates the input file is missing required sections
    or has structural problems that prevent parsing.
    """
    pass


# ---------------------------------------------------------------------------
# Section Configuration
# ---------------------------------------------------------------------------
# This configuration-driven approach allows adding new sections without
# changing parsing logic. Each section defines:
# - display_name: For error messages (user-facing)
# - patterns: All acceptable header variations (case-insensitive)
# - output_key: The key used in the output dictionary
# - type: 'inline' (single value after colon) or 'list' (bullet points)
# - required_items: Minimum items for list sections (optional)

SECTION_CONFIG = {
    'task': {
        'display_name': 'Task',
        'patterns': ['task'],
        'output_key': 'task',
        'type': 'inline',
    },
    'owned_by': {
        'display_name': 'Owned by',
        'patterns': ['owned by', 'owner'],
        'output_key': 'owned_by',
        'type': 'inline',
    },
    'planned_approach': {
        'display_name': 'What I think I need to do',
        'patterns': ['what i think i need to do', 'what i need to do'],
        'output_key': 'planned_approach',
        'type': 'list',
        'required_items': 1,
    },
    'unknowns': {
        'display_name': "What I'm unsure about",
        'patterns': ["what i'm unsure about", "what im unsure about", "unsure about"],
        'output_key': 'unknowns',
        'type': 'list',
    },
    'constraints': {
        'display_name': 'Constraints I know',
        'patterns': ['constraints i know', 'constraints'],
        'output_key': 'constraints',
        'type': 'list',
    },
    'assumptions': {
        'display_name': 'Things I\'m assuming (might be wrong)',
        'patterns': [
            "things i'm assuming",
            "things im assuming",
            "assumptions",
            "assuming"
        ],
        'output_key': 'assumptions',
        'type': 'list',
    },
}

# Fields that are required to be present and non-empty
REQUIRED_FIELDS = {'task', 'owned_by', 'planned_approach'}


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
    lines = content.splitlines()

    return _parse_lines(lines)


def _parse_lines(lines: list[str]) -> dict:
    """
    Parse lines into a dictionary of field values.

    The parsing logic:
    1. Initialize empty result dict with all fields
    2. Iterate through each line
    3. Check if line is a section header (case-insensitive)
    4. For inline sections: extract value from same line or next non-empty line
    5. For list sections: collect bullet points and plain paragraphs

    Args:
        lines: Raw lines from the file

    Returns:
        Dictionary with parsed field values
    """
    # Initialize result with default empty values.
    # All fields start empty so missing optional sections return empty lists,
    # which is cleaner than None for downstream processing.
    result = {
        'task': '',
        'owned_by': '',
        'planned_approach': [],
        'unknowns': [],
        'constraints': [],
        'assumptions': [],
    }

    # State machine: tracks which section we're currently inside.
    # This allows collecting multi-line content under a single heading.
    current_section: Optional[str] = None

    # For inline sections like "Task: Build X", the value might be on the
    # same line (after the colon) or on the next line. This flag tells us
    # to capture the next non-empty line as the value.
    waiting_for_inline_value: Optional[str] = None

    for line in lines:
        # Clean the line - strip whitespace
        trimmed = line.strip() if line else ''

        # Skip completely empty lines
        if not trimmed:
            continue

        # Skip document title lines (e.g., "# Task Context")
        if _is_document_title(trimmed):
            continue

        # Check if this line is a section header
        detected_section = _detect_section_header(trimmed)

        if detected_section is not None:
            # We found a new section header
            current_section = detected_section
            section_config = SECTION_CONFIG[detected_section]
            output_key = section_config['output_key']

            if section_config['type'] == 'inline':
                # For inline sections, try to extract value from this line
                inline_value = _extract_inline_value(trimmed)
                if inline_value:
                    result[output_key] = inline_value
                    waiting_for_inline_value = None
                else:
                    # Value might be on the next line
                    waiting_for_inline_value = output_key
            else:
                # List section - reset to empty list and prepare to collect items
                result[output_key] = []
                waiting_for_inline_value = None

        elif waiting_for_inline_value is not None:
            # We're waiting for an inline value from previous header
            result[waiting_for_inline_value] = trimmed
            waiting_for_inline_value = None

        elif current_section is not None:
            # We're inside a section, collect content
            section_config = SECTION_CONFIG[current_section]
            output_key = section_config['output_key']

            if section_config['type'] == 'list':
                # Collect list items
                item = _extract_list_item(trimmed)
                if item:
                    result[output_key].append(item)

    # Validate required fields
    _validate(result)

    return result


def _normalize_apostrophes(text: str) -> str:
    """
    Normalize various apostrophe characters to ASCII apostrophe.

    WHY: Text editors and word processors often auto-replace straight quotes
    with "smart" curly quotes. When users copy-paste from such sources or
    type on mobile keyboards, the file may contain Unicode apostrophes.
    Normalizing them ensures "What I'm" matches "What I'm" regardless of
    which apostrophe character was used.

    Args:
        text: Text that may contain Unicode apostrophes

    Returns:
        Text with all apostrophe variants normalized to ASCII (')
    """
    apostrophe_chars = [
        '\u2019',  # RIGHT SINGLE QUOTATION MARK (') - common in Word/macOS
        '\u2018',  # LEFT SINGLE QUOTATION MARK (') - opening quote
        '\u0060',  # GRAVE ACCENT (`) - sometimes used as apostrophe
        '\u00B4',  # ACUTE ACCENT (´) - common on international keyboards
        '\u201A',  # SINGLE LOW-9 QUOTATION MARK (‚) - European usage
    ]
    result = text
    for char in apostrophe_chars:
        result = result.replace(char, "'")
    return result


def _strip_markdown_header(line: str) -> str:
    """
    Remove markdown header markers (# ## ### etc.).

    Args:
        line: Line that may start with # markers

    Returns:
        The text content after stripping markers
    """
    return line.lstrip('#').strip()


def _is_document_title(trimmed_line: str) -> bool:
    """
    Check if a line is a document title (not a section header).

    Document titles are markdown headers like "# Task Context" that
    don't match any known section pattern.

    Args:
        trimmed_line: The trimmed line to check

    Returns:
        True if this is a document title, False otherwise
    """
    # Only consider lines that start with # as potential titles
    if not trimmed_line.startswith('#'):
        return False

    # Extract the text after the # markers
    header_text = _strip_markdown_header(trimmed_line)
    normalized = _normalize_apostrophes(header_text).lower()

    # Check if this matches any known section
    for section_config in SECTION_CONFIG.values():
        for pattern in section_config['patterns']:
            if normalized.startswith(pattern):
                return False

    # Markdown header that doesn't match any section = document title
    return True


def _detect_section_header(trimmed_line: str) -> Optional[str]:
    """
    Detect if a line is a known section header.

    Handles multiple formats:
    - Plain text: "Task:" or "Task"
    - Markdown: "## Task" or "# Task:"
    - Case variations: "TASK:", "task:", "Task:"
    - Unicode apostrophes: "What I'm" matches "What I'm"

    Args:
        trimmed_line: The trimmed line to check

    Returns:
        Field name if this is a section header, None otherwise
    """
    # Normalize the line for comparison
    normalized = _strip_markdown_header(trimmed_line)
    normalized = _normalize_apostrophes(normalized)
    check_text = normalized.lower()

    # Try to match against each section's patterns
    for field_name, config in SECTION_CONFIG.items():
        for pattern in config['patterns']:
            if check_text.startswith(pattern):
                # Verify it's actually a header
                remaining = check_text[len(pattern):]
                if (not remaining or
                        remaining.startswith(':') or
                        remaining.startswith(' ')):
                    return field_name

    return None


def _extract_inline_value(trimmed_line: str) -> str:
    """
    Extract the inline value from a section header line.

    For lines like "Task: Build authentication", extracts "Build authentication".

    Args:
        trimmed_line: The header line

    Returns:
        Extracted value, or empty string if none found
    """
    text = _strip_markdown_header(trimmed_line)
    colon_pos = text.find(':')
    if colon_pos == -1:
        return ''
    return text[colon_pos + 1:].strip()


def _extract_list_item(trimmed_line: str) -> Optional[str]:
    """
    Extract a list item from a line.

    Handles:
    - Dash bullets: "- item text"
    - Asterisk bullets: "* item text"
    - Numbered lists: "1. item text"
    - Plain paragraphs (non-bullet, non-header text)

    Args:
        trimmed_line: The trimmed line

    Returns:
        Extracted item text, or None if line is not a valid item
    """
    # Check for dash bullets
    if trimmed_line.startswith('- '):
        item = trimmed_line[2:].strip()
        return item if item else None

    # Check for asterisk bullets
    if trimmed_line.startswith('* '):
        item = trimmed_line[2:].strip()
        return item if item else None

    # Check for numbered lists
    numbered_match = re.match(r'^\d+\.\s+(.+)$', trimmed_line)
    if numbered_match:
        return numbered_match.group(1)

    # Check for plain paragraph (non-empty, non-header text)
    if trimmed_line and not trimmed_line.startswith('#'):
        if _detect_section_header(trimmed_line) is None:
            return trimmed_line

    return None


def _validate(result: dict) -> None:
    """
    Validate the parsed result has all required content.

    Raises TaskContextValidationError if:
    - Task description is empty
    - Owner is not specified
    - Planned approach is empty (must have at least one item)
    """
    errors = []

    for field_name in REQUIRED_FIELDS:
        config = SECTION_CONFIG[field_name]
        display_name = config['display_name']
        output_key = config['output_key']
        value = result.get(output_key)

        if config['type'] == 'inline':
            if not value or not str(value).strip():
                errors.append(f"'{display_name}' section is required and cannot be empty")

        elif config['type'] == 'list':
            min_items = config.get('required_items', 0)
            actual_items = len(value) if value else 0
            if actual_items < min_items:
                errors.append(
                    f"'{display_name}' must contain at least {min_items} item(s)"
                )

    if errors:
        raise TaskContextValidationError("; ".join(errors))
