"""Mental Model Synthesizer - First reasoning step in the Clarity pipeline."""

import json
from pathlib import Path
from dataclasses import dataclass


class SynthesisError(Exception):
    """Raised when synthesis fails."""
    pass


class LLMClient:
    """
    Abstract LLM client interface.

    This must be implemented or injected with a concrete provider.
    """

    def complete(self, system_prompt: str, user_content: str) -> str:
        """
        Send a completion request to the LLM.

        Args:
            system_prompt: The system prompt
            user_content: The user message content

        Returns:
            The LLM response text
        """
        raise NotImplementedError("LLM client must be configured")


# Global client instance - must be set before use
_llm_client: LLMClient | None = None


def set_llm_client(client: LLMClient) -> None:
    """Configure the LLM client for synthesis."""
    global _llm_client
    _llm_client = client


def get_llm_client() -> LLMClient:
    """Get the configured LLM client."""
    if _llm_client is None:
        raise SynthesisError(
            "LLM client not configured. Call set_llm_client() first."
        )
    return _llm_client


def _load_prompt() -> str:
    """Load the synthesizer prompt template."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "synthesizer.txt"

    if not prompt_path.exists():
        raise SynthesisError(f"Prompt template not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def _format_task_context(task_ctx: dict) -> str:
    """Format task context for the prompt."""
    lines = ["## Task Context\n"]

    if "task" in task_ctx:
        lines.append(f"**Task:** {task_ctx['task']}\n")

    if "owned_by" in task_ctx:
        lines.append(f"**Owner:** {task_ctx['owned_by']}\n")

    if "planned_approach" in task_ctx:
        lines.append("\n**Planned Approach:**")
        approach = task_ctx["planned_approach"]
        if isinstance(approach, list):
            for item in approach:
                lines.append(f"- {item}")
        else:
            lines.append(str(approach))

    if "unknowns" in task_ctx:
        lines.append("\n**Unknowns:**")
        unknowns = task_ctx["unknowns"]
        if isinstance(unknowns, list):
            for item in unknowns:
                lines.append(f"- {item}")
        else:
            lines.append(str(unknowns))

    if "constraints" in task_ctx:
        lines.append("\n**Constraints:**")
        constraints = task_ctx["constraints"]
        if isinstance(constraints, list):
            for item in constraints:
                lines.append(f"- {item}")
        else:
            lines.append(str(constraints))

    if "assumptions" in task_ctx:
        lines.append("\n**Assumptions:**")
        assumptions = task_ctx["assumptions"]
        if isinstance(assumptions, list):
            for item in assumptions:
                lines.append(f"- {item}")
        else:
            lines.append(str(assumptions))

    return "\n".join(lines)


def _format_docs(docs: dict) -> str:
    """Format documentation for the prompt."""
    lines = ["## Documentation\n"]

    documents = docs.get("documents", [])

    if not documents:
        lines.append("*No documentation provided.*")
        return "\n".join(lines)

    for doc in documents:
        path = doc.get("path", "unknown")
        lines.append(f"### File: {path}\n")

        for section in doc.get("sections", []):
            heading = section.get("heading", "")
            level = section.get("level", 1)
            content = section.get("content", "")
            line_start = section.get("line_start", 0)
            line_end = section.get("line_end", 0)

            prefix = "#" * (level + 3)  # Offset for nesting
            lines.append(f"{prefix} {heading} (lines {line_start}-{line_end})")
            if content:
                lines.append(content)
            lines.append("")

    return "\n".join(lines)


def _format_code(code: dict) -> str:
    """Format code observations for the prompt."""
    lines = ["## Code Observations\n"]

    files = code.get("files", [])

    if not files:
        lines.append("*No code provided.*")
        return "\n".join(lines)

    for file in files:
        path = file.get("path", "unknown")
        lines.append(f"### File: {path}\n")

        # Imports
        imports = file.get("imports", [])
        if imports:
            lines.append("**Imports:**")
            for imp in imports[:10]:  # Limit to avoid token overflow
                lines.append(f"- `{imp}`")
            if len(imports) > 10:
                lines.append(f"- ... and {len(imports) - 10} more")
            lines.append("")

        # Functions
        functions = file.get("functions", [])
        if functions:
            lines.append("**Functions:**")
            for func in functions:
                name = func.get("name", "")
                sig = func.get("signature", "")
                line_start = func.get("line_start", 0)
                line_end = func.get("line_end", 0)
                docstring = func.get("docstring")

                lines.append(f"\n`{sig}` (lines {line_start}-{line_end})")
                if docstring:
                    # Truncate long docstrings
                    doc_preview = docstring[:200]
                    if len(docstring) > 200:
                        doc_preview += "..."
                    lines.append(f"  Docstring: {doc_preview}")
            lines.append("")

        # Classes
        classes = file.get("classes", [])
        if classes:
            lines.append("**Classes:**")
            for cls in classes:
                name = cls.get("name", "")
                sig = cls.get("signature", "")
                line_start = cls.get("line_start", 0)
                line_end = cls.get("line_end", 0)
                docstring = cls.get("docstring")
                bases = cls.get("bases", [])
                methods = cls.get("methods", [])

                lines.append(f"\n`{sig}` (lines {line_start}-{line_end})")
                if docstring:
                    doc_preview = docstring[:200]
                    if len(docstring) > 200:
                        doc_preview += "..."
                    lines.append(f"  Docstring: {doc_preview}")

                if methods:
                    lines.append(f"  Methods ({len(methods)}):")
                    for method in methods[:5]:  # Limit methods shown
                        m_name = method.get("name", "")
                        m_sig = method.get("signature", "")
                        m_start = method.get("line_start", 0)
                        m_end = method.get("line_end", 0)
                        lines.append(f"    - `{m_sig}` (lines {m_start}-{m_end})")
                    if len(methods) > 5:
                        lines.append(f"    - ... and {len(methods) - 5} more methods")
            lines.append("")

    return "\n".join(lines)


def _build_user_content(task_ctx: dict, docs: dict, code: dict) -> str:
    """Build the complete user content for the LLM."""
    parts = [
        _format_task_context(task_ctx),
        "",
        _format_docs(docs),
        "",
        _format_code(code),
        "",
        "---",
        "",
        "Analyze these inputs and produce the mental model JSON.",
    ]
    return "\n".join(parts)


def _parse_response(response: str) -> dict:
    """Parse the LLM response as JSON."""
    # Try to extract JSON from the response
    response = response.strip()

    # Handle markdown code blocks
    if response.startswith("```json"):
        response = response[7:]
    elif response.startswith("```"):
        response = response[3:]

    if response.endswith("```"):
        response = response[:-3]

    response = response.strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise SynthesisError(f"Failed to parse LLM response as JSON: {e}")


def _validate_output(output: dict) -> None:
    """Validate the synthesis output has required fields."""
    required_keys = {
        "system_intent",
        "observed_reality",
        "feature_fit",
        "assumptions_and_risks",
        "open_decisions",
        "documentation_gaps",
        "confidence_assessment",
    }

    missing = required_keys - set(output.keys())
    if missing:
        raise SynthesisError(
            f"Synthesis output missing required keys: {', '.join(sorted(missing))}"
        )


def synthesize(task_ctx: dict, docs: dict, code: dict) -> dict:
    """
    Synthesize inputs into a grounded mental model.

    This function makes exactly ONE LLM call to analyze the provided inputs
    and produce a structured mental model.

    Args:
        task_ctx: Parsed task context from read_task_context()
        docs: Parsed documentation from read_docs()
        code: Parsed code observations from read_code()

    Returns:
        Dictionary containing:
        - system_intent: What the system is designed to do (from docs)
        - observed_reality: What the code actually shows
        - feature_fit: Alignments and conflicts
        - assumptions_and_risks: Flagged assumptions
        - open_decisions: Decisions that need to be made
        - documentation_gaps: Missing documentation
        - confidence_assessment: Overall confidence level

    Raises:
        SynthesisError: If synthesis fails
    """
    client = get_llm_client()

    system_prompt = _load_prompt()
    user_content = _build_user_content(task_ctx, docs, code)

    try:
        response = client.complete(system_prompt, user_content)
    except Exception as e:
        raise SynthesisError(f"LLM call failed: {e}")

    output = _parse_response(response)
    _validate_output(output)

    return output
