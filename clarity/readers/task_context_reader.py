"""
TaskContextReader - A robust parser for task_context.md files.

==============================================================================
PURPOSE
==============================================================================
This reader parses human-written task context documents that describe what a
developer is working on, what they plan to do, and their uncertainties. The
parsed data feeds into AI prompt generation to provide context-aware assistance.

==============================================================================
DESIGN PHILOSOPHY: STRICTNESS IS INTENTIONAL
==============================================================================
This parser enforces strict validation for required fields. This is NOT
arbitrary bureaucracy - it's essential for downstream reliability:

1. GARBAGE IN, GARBAGE OUT: The parsed data becomes part of AI prompts. If the
   task description is missing, the AI cannot provide relevant help. If the
   planned approach is empty, the AI has no context for what the developer
   intends to do. Missing required fields = useless or misleading AI output.

2. FAIL FAST, FAIL CLEARLY: When a task_context.md file is malformed, we raise
   TaskContextValidationError immediately with a clear message. This is better
   than silently producing incomplete data that causes confusing failures later
   in the pipeline (or worse, subtly wrong AI responses).

3. HUMAN ACCOUNTABILITY: Requiring explicit task ownership and planned approach
   forces developers to think through their work before asking for AI help.
   This is a feature, not a bug - it improves both the human's clarity and
   the AI's ability to assist.

==============================================================================
REQUIRED SECTIONS (must be present and non-empty)
==============================================================================
  - Task: What the developer is working on (single value)
    WHY REQUIRED: Without knowing the task, AI assistance is blind guessing.

  - Owned by: Team or person responsible (single value)
    WHY REQUIRED: Establishes accountability and helps route questions.

  - What I think I need to do: Developer's planned approach (list, min 1 item)
    WHY REQUIRED: The AI needs to know the developer's mental model to provide
    relevant suggestions, catch potential issues, or validate the approach.

==============================================================================
OPTIONAL SECTIONS (can be empty or omitted)
==============================================================================
  - What I'm unsure about: Developer's uncertainties (list)
  - Constraints I know: Known limitations or requirements (list)
  - Things I'm assuming (might be wrong): Explicit assumptions (list)

These are optional because not every task has uncertainties, constraints, or
assumptions worth documenting. However, when present, they significantly
improve AI assistance quality.

==============================================================================
FORMAT FLEXIBILITY
==============================================================================
Section headers can be:
  - Plain text: "Task:" or "Task"
  - Markdown headers: "# Task" or "## Task"
  - Case-insensitive: "TASK:", "task:", "Task:" all work

List items can use:
  - Dash bullets: "- item"
  - Asterisk bullets: "* item"
  - Numbered lists: "1. item"
  - Plain paragraphs (non-bullet text under a section)

WHY FLEXIBLE: Humans write markdown in many styles. We don't want to reject
valid content just because someone prefers "## Task" over "Task:". Strictness
is for semantic content (required fields), not syntactic style.

==============================================================================
ERROR HANDLING STRATEGY
==============================================================================
1. FileNotFoundError: Raised if the file doesn't exist. No wrapping.
2. TaskContextValidationError: Raised for structural/semantic problems:
   - Missing required sections
   - Empty required sections
   - File path points to a directory instead of a file
3. All validation errors are collected and reported together, so users see
   ALL problems at once instead of fixing them one at a time.

==============================================================================
EXAMPLE VALID FILE
==============================================================================
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

    This exception indicates the input file is structurally invalid:
    - Missing required sections (Task, Owned by, What I think I need to do)
    - Empty required sections (section header exists but no content)
    - File path points to a directory instead of a file

    WHY A CUSTOM EXCEPTION:
    Using a specific exception type (not generic ValueError) allows callers to:
    1. Catch validation errors separately from other failures
    2. Distinguish "malformed input" from "file not found" or "permission denied"
    3. Provide user-friendly error messages at the appropriate level

    The error message contains ALL validation failures concatenated with ";",
    so users can fix everything at once instead of playing whack-a-mole.
    """
    pass


# =============================================================================
# SECTION CONFIGURATION
# =============================================================================
# This configuration-driven approach centralizes all section definitions in one
# place. Adding a new section requires only updating this dict - no changes to
# the parsing logic itself.
#
# Each section defines:
#   - display_name: Human-readable name for error messages
#   - patterns: All acceptable header text (lowercase, checked with startswith)
#   - output_key: The key used in the returned dictionary
#   - type: 'inline' (single value after colon) or 'list' (bullet points below)
#   - required_items: (optional) Minimum items for list sections
#
# WHY CONFIGURATION-DRIVEN:
# 1. Single source of truth - section names aren't scattered across the code
# 2. Easy to add/modify sections without understanding parsing internals
# 3. Consistent validation - all sections follow the same rules
# 4. Self-documenting - the config IS the specification

SECTION_CONFIG = {
    # -------------------------------------------------------------------------
    # REQUIRED: Task description (inline value)
    # The core question: "What are you working on?"
    # Without this, the AI has no idea what to help with.
    # -------------------------------------------------------------------------
    'task': {
        'display_name': 'Task',
        'patterns': ['task'],
        'output_key': 'task',
        'type': 'inline',  # Value appears after colon on same line
    },

    # -------------------------------------------------------------------------
    # REQUIRED: Ownership (inline value)
    # Who is responsible for this work?
    # Establishes accountability and helps route follow-up questions.
    # -------------------------------------------------------------------------
    'owned_by': {
        'display_name': 'Owned by',
        'patterns': ['owned by', 'owner'],  # Accept "Owner:" as shorthand
        'output_key': 'owned_by',
        'type': 'inline',
    },

    # -------------------------------------------------------------------------
    # REQUIRED: Planned approach (list, minimum 1 item)
    # What does the developer THINK they need to do?
    # This is crucial - it reveals the developer's mental model.
    # The AI can validate, suggest improvements, or catch blind spots.
    # MUST have at least one item - an empty plan is useless.
    # -------------------------------------------------------------------------
    'planned_approach': {
        'display_name': 'What I think I need to do',
        'patterns': ['what i think i need to do', 'what i need to do'],
        'output_key': 'planned_approach',
        'type': 'list',  # Bullet points below the header
        'required_items': 1,  # STRICT: Must have at least one planned step
    },

    # -------------------------------------------------------------------------
    # OPTIONAL: Unknowns/uncertainties (list)
    # What is the developer unsure about?
    # Extremely valuable for AI assistance - tells it where to focus help.
    # -------------------------------------------------------------------------
    'unknowns': {
        'display_name': "What I'm unsure about",
        # Multiple patterns handle apostrophe variations (smart quotes vs ASCII)
        'patterns': ["what i'm unsure about", "what im unsure about", "unsure about"],
        'output_key': 'unknowns',
        'type': 'list',
    },

    # -------------------------------------------------------------------------
    # OPTIONAL: Known constraints (list)
    # Technical or business limitations the developer is aware of.
    # Helps AI avoid suggesting impossible solutions.
    # -------------------------------------------------------------------------
    'constraints': {
        'display_name': 'Constraints I know',
        'patterns': ['constraints i know', 'constraints'],
        'output_key': 'constraints',
        'type': 'list',
    },

    # -------------------------------------------------------------------------
    # OPTIONAL: Explicit assumptions (list)
    # What is the developer assuming that might be wrong?
    # The "(might be wrong)" phrasing encourages intellectual humility.
    # AI can challenge or validate these assumptions.
    # -------------------------------------------------------------------------
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

# =============================================================================
# REQUIRED FIELDS
# =============================================================================
# These fields MUST be present and non-empty. Validation will fail otherwise.
#
# WHY THESE THREE ARE REQUIRED:
# - task: Can't help without knowing what the work is
# - owned_by: Accountability matters; also useful for routing/context
# - planned_approach: The developer's intent is essential for useful AI help
#
# Optional fields (unknowns, constraints, assumptions) are valuable when present
# but not every task has them. We don't want to force developers to write
# "N/A" or make up uncertainties they don't actually have.

REQUIRED_FIELDS = {'task', 'owned_by', 'planned_approach'}


# =============================================================================
# PUBLIC API
# =============================================================================

def read_task_context(path: str) -> dict:
    """
    Parse a task_context.md file into a structured dictionary.

    This is the main entry point for the task context reader. It handles:
    1. File existence and type validation
    2. Reading and decoding the file content
    3. Parsing the markdown structure
    4. Validating required fields are present

    STRICTNESS NOTE: This function will raise an exception if required fields
    are missing. This is intentional - see module docstring for rationale.
    Callers should NOT catch and ignore TaskContextValidationError; they should
    either let it propagate or handle it by prompting the user to fix the file.

    Args:
        path: Path to the task_context.md file (absolute or relative)

    Returns:
        Dictionary with parsed sections. All keys are always present:
        - task: str - The task description (REQUIRED, never empty)
        - owned_by: str - Team or person responsible (REQUIRED, never empty)
        - planned_approach: list[str] - Planned steps (REQUIRED, at least 1 item)
        - unknowns: list[str] - Uncertainties (optional, may be empty list)
        - constraints: list[str] - Known constraints (optional, may be empty list)
        - assumptions: list[str] - Assumptions (optional, may be empty list)

    Raises:
        FileNotFoundError: If the file does not exist at the given path.
            We do NOT wrap this - callers can distinguish "file missing" from
            "file malformed" by exception type.

        TaskContextValidationError: If the file exists but is invalid:
            - Path points to a directory, not a file
            - Required sections are missing or empty
            - Planned approach has zero items
            The error message lists ALL validation failures, not just the first.

    Example:
        >>> data = read_task_context("docs/task_context.md")
        >>> print(data['task'])  # Always exists and non-empty
        "Build authentication system"
        >>> print(data['unknowns'])  # May be empty list
        ["OAuth integration details"]
    """
    file_path = Path(path)

    # -------------------------------------------------------------------------
    # FILE EXISTENCE CHECK
    # Raise FileNotFoundError (not wrapped) so callers can distinguish
    # "file doesn't exist" from "file is malformed".
    # -------------------------------------------------------------------------
    if not file_path.exists():
        raise FileNotFoundError(f"Task context file not found: {path}")

    # -------------------------------------------------------------------------
    # FILE TYPE CHECK
    # Catch the case where someone passes a directory path.
    # This is a validation error, not a file-not-found error.
    # -------------------------------------------------------------------------
    if not file_path.is_file():
        raise TaskContextValidationError(f"Path is not a file: {path}")

    # -------------------------------------------------------------------------
    # READ AND PARSE
    # Always use UTF-8 encoding. If the file has encoding issues, Python will
    # raise UnicodeDecodeError - we let that propagate unmodified.
    # -------------------------------------------------------------------------
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    return _parse_lines(lines)


# =============================================================================
# INTERNAL PARSING FUNCTIONS
# =============================================================================

def _parse_lines(lines: list[str]) -> dict:
    """
    Parse lines into a dictionary of field values using a state machine.

    PARSING ALGORITHM:
    This is a single-pass, line-by-line state machine parser. We iterate through
    each line exactly once, maintaining state about which section we're in.

    State machine variables:
    - current_section: Which section header we're under (or None if outside)
    - waiting_for_inline_value: For headers like "Task:" where the value might
      be on the next line instead of after the colon

    Line classification (in priority order):
    1. Empty line -> skip
    2. Document title (e.g., "# Task Context") -> skip
    3. Section header -> update state, possibly extract inline value
    4. Inline value we're waiting for -> capture it
    5. Content under a list section -> extract and append item

    WHY SINGLE-PASS:
    - Predictable performance: O(n) where n = number of lines
    - Simple mental model: each line is processed exactly once
    - Easy to debug: state at any point depends only on lines seen so far

    Args:
        lines: Raw lines from the file (already split by newline)

    Returns:
        Dictionary with parsed field values. All keys always present.
        Validation happens at the end - may raise TaskContextValidationError.
    """
    # -------------------------------------------------------------------------
    # INITIALIZE RESULT
    # All fields start with empty defaults. This ensures:
    # - Missing optional sections get empty lists (not None)
    # - Downstream code doesn't need null checks
    # - The return type is predictable (always same keys)
    # -------------------------------------------------------------------------
    result = {
        'task': '',
        'owned_by': '',
        'planned_approach': [],
        'unknowns': [],
        'constraints': [],
        'assumptions': [],
    }

    # -------------------------------------------------------------------------
    # STATE MACHINE VARIABLES
    # -------------------------------------------------------------------------
    # Which section are we currently inside? None = not in any section yet.
    # This persists across lines until we hit another section header.
    current_section: Optional[str] = None

    # For inline sections (Task, Owned by), the value might be on the next line.
    # "Task: Build X" -> inline_value = "Build X"
    # "Task:\nBuild X" -> need to wait for next line
    # When set, the next non-empty line becomes this field's value.
    waiting_for_inline_value: Optional[str] = None

    # -------------------------------------------------------------------------
    # MAIN PARSING LOOP
    # -------------------------------------------------------------------------
    for line in lines:
        # Normalize: strip leading/trailing whitespace
        trimmed = line.strip() if line else ''

        # Skip blank lines - they're just formatting
        if not trimmed:
            continue

        # Skip document titles like "# Task Context"
        # These are headers that don't match any known section pattern.
        if _is_document_title(trimmed):
            continue

        # -------------------------------------------------------------------
        # CHECK FOR SECTION HEADER
        # -------------------------------------------------------------------
        detected_section = _detect_section_header(trimmed)

        if detected_section is not None:
            # New section starts here - update state
            current_section = detected_section
            section_config = SECTION_CONFIG[detected_section]
            output_key = section_config['output_key']

            if section_config['type'] == 'inline':
                # INLINE SECTION (Task, Owned by)
                # Try to extract value from same line: "Task: Build X"
                inline_value = _extract_inline_value(trimmed)
                if inline_value:
                    # Found it on this line
                    result[output_key] = inline_value
                    waiting_for_inline_value = None
                else:
                    # No value after colon - expect it on next line
                    waiting_for_inline_value = output_key
            else:
                # LIST SECTION (planned_approach, unknowns, etc.)
                # Reset to empty list - items will be appended below
                result[output_key] = []
                waiting_for_inline_value = None

        elif waiting_for_inline_value is not None:
            # -------------------------------------------------------------------
            # CAPTURE DEFERRED INLINE VALUE
            # The previous line was a header like "Task:" with no value.
            # This line IS the value.
            # -------------------------------------------------------------------
            result[waiting_for_inline_value] = trimmed
            waiting_for_inline_value = None

        elif current_section is not None:
            # -------------------------------------------------------------------
            # CONTENT LINE UNDER A SECTION
            # We're inside a section - process based on section type.
            # -------------------------------------------------------------------
            section_config = SECTION_CONFIG[current_section]
            output_key = section_config['output_key']

            if section_config['type'] == 'list':
                # Extract list item (bullet point or plain text)
                item = _extract_list_item(trimmed)
                if item:
                    result[output_key].append(item)
            # Note: for inline sections, extra lines after the value are ignored.
            # "Task: Build X\nMore details here" -> only "Build X" is captured.
            # This is intentional - inline sections are single-value.

    # -------------------------------------------------------------------------
    # VALIDATION
    # After parsing, check that required fields are present and non-empty.
    # This is where we enforce the "strictness is intentional" policy.
    # -------------------------------------------------------------------------
    _validate(result)

    return result


# =============================================================================
# TEXT NORMALIZATION HELPERS
# =============================================================================
# These functions handle the messy reality of human-written text: Unicode
# variations, markdown formatting, etc. They make the parser robust against
# common variations without being overly permissive.

def _normalize_apostrophes(text: str) -> str:
    """
    Normalize various apostrophe characters to ASCII apostrophe.

    PROBLEM: Section headers like "What I'm unsure about" contain apostrophes.
    But users might write files using:
    - Smart quotes from Word/Google Docs: "What I'm unsure about"
    - Grave accents from programming contexts: "What I`m unsure about"
    - International keyboard variations: "What I´m unsure about"

    Without normalization, these would fail to match our patterns, leading to
    confusing "missing required section" errors for files that LOOK correct
    to the human eye.

    SOLUTION: Replace all apostrophe-like characters with ASCII apostrophe (')
    before pattern matching. This is done during matching only - the original
    text is preserved in the output.

    Args:
        text: Text that may contain Unicode apostrophes

    Returns:
        Text with all apostrophe variants normalized to ASCII (')
    """
    # List of characters that humans use interchangeably with apostrophe
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
    Remove markdown header markers (# ## ### etc.) from a line.

    Examples:
        "# Task" -> "Task"
        "## Owned by: Team A" -> "Owned by: Team A"
        "### What I need to do" -> "What I need to do"

    Args:
        line: Line that may start with # markers

    Returns:
        The text content after stripping markers and surrounding whitespace
    """
    return line.lstrip('#').strip()


# =============================================================================
# LINE CLASSIFICATION HELPERS
# =============================================================================
# These functions determine what role each line plays in the document structure.

def _is_document_title(trimmed_line: str) -> bool:
    """
    Check if a line is a document title (to be skipped).

    PROBLEM: Files often start with a title like "# Task Context" or
    "# My Development Notes". These are markdown headers but NOT section
    headers we care about. If we don't skip them, they'd be treated as
    content under the previous section (which doesn't exist), or cause
    parsing confusion.

    SOLUTION: A line is a document title if:
    1. It starts with # (markdown header syntax)
    2. Its text doesn't match any known section pattern

    This allows "# Task" to be recognized as a section (matches 'task' pattern)
    while "# Task Context" is skipped (no pattern match).

    Args:
        trimmed_line: The trimmed line to check

    Returns:
        True if this is a document title that should be skipped
    """
    # Only markdown headers can be document titles
    if not trimmed_line.startswith('#'):
        return False

    # Extract and normalize the text after the # markers
    header_text = _strip_markdown_header(trimmed_line)
    normalized = _normalize_apostrophes(header_text).lower()

    # If it matches ANY known section pattern, it's a section header, not a title
    for section_config in SECTION_CONFIG.values():
        for pattern in section_config['patterns']:
            if normalized.startswith(pattern):
                return False

    # Markdown header that doesn't match any section = document title (skip it)
    return True


def _detect_section_header(trimmed_line: str) -> Optional[str]:
    """
    Detect if a line is a known section header and return its field name.

    FORMAT FLEXIBILITY (strictness is for content, not syntax):
    This function accepts many equivalent ways to write section headers:
    - Plain text: "Task:" or "Task"
    - Markdown: "## Task" or "# Task:"
    - Case variations: "TASK:", "task:", "Task:"
    - Unicode apostrophes: "What I'm" matches "What I'm"

    MATCHING LOGIC:
    1. Strip markdown header markers (# ## etc.)
    2. Normalize apostrophes to ASCII
    3. Convert to lowercase
    4. Check if it STARTS WITH any known pattern
    5. If match, verify what follows is valid (nothing, colon, or space)

    The "verify what follows" step prevents false positives:
    - "Task:" -> matches (colon follows)
    - "Task" -> matches (nothing follows)
    - "Taskforce:" -> does NOT match (letters follow "Task")

    Args:
        trimmed_line: The trimmed line to check

    Returns:
        Internal field name ('task', 'owned_by', etc.) if this is a section header,
        None if this is regular content
    """
    # Normalize for case-insensitive, apostrophe-flexible matching
    normalized = _strip_markdown_header(trimmed_line)
    normalized = _normalize_apostrophes(normalized)
    check_text = normalized.lower()

    # Try to match against each section's patterns
    for field_name, config in SECTION_CONFIG.items():
        for pattern in config['patterns']:
            if check_text.startswith(pattern):
                # Verify it's actually a complete header match
                # "Task:" matches, "Taskforce:" does not
                remaining = check_text[len(pattern):]
                if (not remaining or
                        remaining.startswith(':') or
                        remaining.startswith(' ')):
                    return field_name

    return None


# =============================================================================
# VALUE EXTRACTION HELPERS
# =============================================================================
# These functions extract the actual content from different line formats.

def _extract_inline_value(trimmed_line: str) -> str:
    """
    Extract the inline value from a section header line.

    For INLINE sections (Task, Owned by), the value appears after a colon
    on the same line as the header.

    Examples:
        "Task: Build authentication" -> "Build authentication"
        "## Owned by: Backend Team" -> "Backend Team"
        "Task:" -> "" (empty - value might be on next line)
        "Task" -> "" (no colon at all)

    Args:
        trimmed_line: The header line (may include markdown markers)

    Returns:
        Extracted value (trimmed), or empty string if no value on this line
    """
    text = _strip_markdown_header(trimmed_line)
    colon_pos = text.find(':')
    if colon_pos == -1:
        # No colon - can't have inline value
        return ''
    return text[colon_pos + 1:].strip()


def _extract_list_item(trimmed_line: str) -> Optional[str]:
    """
    Extract a list item from a line under a list section.

    For LIST sections (planned_approach, unknowns, etc.), content appears
    as bullet points or numbered items below the header.

    SUPPORTED FORMATS (flexible to match how humans write markdown):
    - Dash bullets: "- item text"
    - Asterisk bullets: "* item text"
    - Numbered lists: "1. item text", "2. item text"
    - Plain paragraphs: Any non-bullet, non-header text

    The plain paragraph support is intentional - some users write lists without
    bullets, just as separate paragraphs. We accept this rather than being
    pedantic about markdown formatting.

    Args:
        trimmed_line: The trimmed line (already determined to be under a list section)

    Returns:
        Extracted item text, or None if line is empty/invalid

    Note:
        Returns None for empty bullets like "- " with no text.
        This prevents blank items from polluting the list.
    """
    # Check for dash bullets (most common in markdown)
    if trimmed_line.startswith('- '):
        item = trimmed_line[2:].strip()
        return item if item else None  # Reject "- " with no content

    # Check for asterisk bullets (also valid markdown)
    if trimmed_line.startswith('* '):
        item = trimmed_line[2:].strip()
        return item if item else None

    # Check for numbered lists: "1. text", "2. text", etc.
    numbered_match = re.match(r'^\d+\.\s+(.+)$', trimmed_line)
    if numbered_match:
        return numbered_match.group(1)

    # Fall back to plain paragraph text (no bullet marker)
    # Only accept if it's not a markdown header or section header
    if trimmed_line and not trimmed_line.startswith('#'):
        if _detect_section_header(trimmed_line) is None:
            return trimmed_line

    return None


# =============================================================================
# VALIDATION
# =============================================================================
# This is where "strictness is intentional" gets enforced. After parsing
# completes, we verify that all required fields have valid content.

def _validate(result: dict) -> None:
    """
    Validate the parsed result has all required content.

    VALIDATION RULES:
    - INLINE required fields (task, owned_by): Must be non-empty string
    - LIST required fields (planned_approach): Must have >= required_items

    WHY VALIDATE AFTER PARSING (not during):
    Collecting all errors before raising allows us to report ALL problems at
    once. This is much friendlier than fixing one error, re-running, finding
    another error, fixing that, re-running... etc.

    ERROR MESSAGE FORMAT:
    Errors are joined with "; " into a single message. Example:
    "'Task' section is required and cannot be empty; 'What I think I need to do' must contain at least 1 item(s)"

    Raises:
        TaskContextValidationError: If ANY required field validation fails.
            The error message contains ALL failures, not just the first one.
    """
    errors = []

    # Check each required field according to its type
    for field_name in REQUIRED_FIELDS:
        config = SECTION_CONFIG[field_name]
        display_name = config['display_name']
        output_key = config['output_key']
        value = result.get(output_key)

        if config['type'] == 'inline':
            # INLINE FIELDS: Must have non-empty string value
            if not value or not str(value).strip():
                errors.append(f"'{display_name}' section is required and cannot be empty")

        elif config['type'] == 'list':
            # LIST FIELDS: Must have at least 'required_items' entries
            min_items = config.get('required_items', 0)
            actual_items = len(value) if value else 0
            if actual_items < min_items:
                errors.append(
                    f"'{display_name}' must contain at least {min_items} item(s)"
                )

    # If any validation failed, raise with ALL error messages
    if errors:
        raise TaskContextValidationError("; ".join(errors))
