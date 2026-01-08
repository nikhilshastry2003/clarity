"""Deterministic parser for Markdown documentation files."""

import re
from pathlib import Path
from dataclasses import dataclass


class DocsReadError(Exception):
    """Raised when documentation reading fails."""
    pass


@dataclass
class Section:
    """A parsed section from a Markdown document."""
    heading: str
    level: int
    content: str
    line_start: int
    line_end: int

    def to_dict(self) -> dict:
        return {
            "heading": self.heading,
            "level": self.level,
            "content": self.content,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass
class Document:
    """A parsed Markdown document."""
    path: str
    sections: list[Section]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "sections": [s.to_dict() for s in self.sections],
        }


def read_docs(paths: list[str]) -> dict:
    """
    Parse multiple Markdown documentation files into structured output.

    Args:
        paths: List of paths to Markdown files

    Returns:
        Dictionary with 'documents' key containing list of parsed documents

    Raises:
        DocsReadError: If any file cannot be read
        FileNotFoundError: If any file does not exist
    """
    if not paths:
        return {"documents": []}

    documents = []

    for path in paths:
        doc = _read_single_doc(path)
        documents.append(doc.to_dict())

    return {"documents": documents}


def _read_single_doc(path: str) -> Document:
    """Read and parse a single Markdown file."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Documentation file not found: {path}")

    if not file_path.is_file():
        raise DocsReadError(f"Path is not a file: {path}")

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise DocsReadError(f"Failed to read file {path}: {e}")

    sections = _parse_sections(content)

    return Document(path=str(file_path.resolve()), sections=sections)


def _parse_sections(content: str) -> list[Section]:
    """Parse Markdown content into sections based on headings."""
    lines = content.split("\n")
    sections = []

    # Pattern for Markdown headings (# to ###)
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+?)\s*$")

    current_heading = None
    current_level = 0
    current_start = 0
    content_lines = []

    for line_num, line in enumerate(lines, start=1):
        match = heading_pattern.match(line)

        if match:
            # Save previous section if exists
            if current_heading is not None:
                sections.append(Section(
                    heading=current_heading,
                    level=current_level,
                    content="\n".join(content_lines).strip(),
                    line_start=current_start,
                    line_end=line_num - 1,
                ))

            # Start new section
            current_level = len(match.group(1))
            current_heading = match.group(2)
            current_start = line_num
            content_lines = []
        else:
            content_lines.append(line)

    # Save final section
    if current_heading is not None:
        sections.append(Section(
            heading=current_heading,
            level=current_level,
            content="\n".join(content_lines).strip(),
            line_start=current_start,
            line_end=len(lines),
        ))

    return sections
