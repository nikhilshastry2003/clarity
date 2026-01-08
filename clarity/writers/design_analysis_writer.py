"""Design Analysis Writer - Renders synthesis output to markdown."""

from pathlib import Path


class WriteError(Exception):
    """Raised when writing fails."""
    pass


def write_design_analysis(analysis: dict, output_path: str) -> None:
    """
    Write synthesis analysis to a markdown file.

    Args:
        analysis: The synthesis output dictionary
        output_path: Path to write the markdown file

    Raises:
        WriteError: If writing fails
    """
    try:
        content = _render_markdown(analysis)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise WriteError(f"Failed to write design analysis: {e}")


def _render_markdown(analysis: dict) -> str:
    """Render the analysis dict to markdown string."""
    sections = [
        _render_header(analysis),
        _render_system_intent(analysis.get("system_intent", {})),
        _render_observed_reality(analysis.get("observed_reality", {})),
        _render_feature_fit(analysis.get("feature_fit", {})),
        _render_assumptions_and_risks(analysis.get("assumptions_and_risks", [])),
        _render_open_decisions(analysis.get("open_decisions", [])),
        _render_documentation_gaps(analysis.get("documentation_gaps", [])),
    ]

    return "\n\n".join(sections)


def _render_header(analysis: dict) -> str:
    """Render the document header with confidence assessment."""
    lines = ["# Design Analysis"]

    confidence = analysis.get("confidence_assessment", {})
    if confidence:
        overall = confidence.get("overall", "unknown")
        sufficient = confidence.get("sufficient_to_proceed", False)
        status = "Ready to proceed" if sufficient else "Needs review"

        lines.append("")
        lines.append(f"**Confidence:** {overall} | **Status:** {status}")

        limiting_factors = confidence.get("limiting_factors", [])
        if limiting_factors:
            lines.append("")
            lines.append("**Limiting Factors:**")
            for factor in limiting_factors:
                lines.append(f"- {factor}")

    return "\n".join(lines)


def _render_system_intent(system_intent: dict) -> str:
    """Render the System Intent section."""
    lines = ["## 1. System Intent"]

    if not system_intent:
        lines.append("")
        lines.append("*No system intent information available.*")
        return "\n".join(lines)

    summary = system_intent.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary)

    key_points = system_intent.get("key_points", [])
    if key_points:
        lines.append("")
        lines.append("**Key Points:**")
        for point in key_points:
            lines.append(f"- {point}")

    citations = system_intent.get("citations", [])
    if citations:
        lines.append("")
        lines.append("**Sources:**")
        for citation in citations:
            lines.append(f"- `{citation}`")

    return "\n".join(lines)


def _render_observed_reality(observed_reality: dict) -> str:
    """Render the Observed Code Reality section."""
    lines = ["## 2. Observed Code Reality"]

    if not observed_reality:
        lines.append("")
        lines.append("*No code observations available.*")
        return "\n".join(lines)

    summary = observed_reality.get("summary", "")
    if summary:
        lines.append("")
        lines.append(summary)

    relevant_code = observed_reality.get("relevant_code", [])
    if relevant_code:
        lines.append("")
        lines.append("**Relevant Code:**")
        lines.append("")
        for item in relevant_code:
            path = item.get("path", "unknown")
            element = item.get("element", "")
            line_range = item.get("lines", "")
            relevance = item.get("relevance", "")

            lines.append(f"- **`{path}`** ")
            if element:
                lines.append(f"  - Element: `{element}`")
            if line_range:
                lines.append(f"  - Lines: {line_range}")
            if relevance:
                lines.append(f"  - Relevance: {relevance}")

    patterns_found = observed_reality.get("patterns_found", [])
    if patterns_found:
        lines.append("")
        lines.append("**Patterns Found:**")
        for pattern in patterns_found:
            lines.append(f"- {pattern}")

    return "\n".join(lines)


def _render_feature_fit(feature_fit: dict) -> str:
    """Render the Feature Fit Analysis section."""
    lines = ["## 3. Feature Fit Analysis"]

    if not feature_fit:
        lines.append("")
        lines.append("*No feature fit analysis available.*")
        return "\n".join(lines)

    alignments = feature_fit.get("alignments", [])
    conflicts = feature_fit.get("conflicts", [])

    if not alignments and not conflicts:
        lines.append("")
        lines.append("*No alignments or conflicts identified.*")
        return "\n".join(lines)

    if alignments:
        lines.append("")
        lines.append("### Alignments")
        lines.append("")
        for item in alignments:
            aspect = item.get("aspect", "")
            evidence = item.get("evidence", "")
            confidence = item.get("confidence", "unknown")

            lines.append(f"**{aspect}**")
            if evidence:
                lines.append(f"- Evidence: {evidence}")
            lines.append(f"- Confidence: {confidence}")
            lines.append("")

    if conflicts:
        lines.append("")
        lines.append("### Conflicts")
        lines.append("")
        for item in conflicts:
            aspect = item.get("aspect", "")
            docs_say = item.get("docs_say", "")
            code_shows = item.get("code_shows", "")
            severity = item.get("severity", "unknown")

            lines.append(f"**{aspect}** (Severity: {severity})")
            if docs_say:
                lines.append(f"- Documentation says: {docs_say}")
            if code_shows:
                lines.append(f"- Code shows: {code_shows}")
            lines.append("")

    return "\n".join(lines)


def _render_assumptions_and_risks(assumptions: list) -> str:
    """Render the Assumptions & Risks section."""
    lines = ["## 4. Assumptions & Risks"]

    if not assumptions:
        lines.append("")
        lines.append("*No assumptions or risks identified.*")
        return "\n".join(lines)

    lines.append("")
    for i, item in enumerate(assumptions, 1):
        assumption = item.get("assumption", "")
        source = item.get("source", "unknown")
        risk = item.get("risk_if_wrong", "")
        validation = item.get("validation_needed", "")

        lines.append(f"### {i}. {assumption}")
        lines.append("")
        lines.append(f"- **Source:** {source}")
        if risk:
            lines.append(f"- **Risk if wrong:** {risk}")
        if validation:
            lines.append(f"- **Validation needed:** {validation}")
        lines.append("")

    return "\n".join(lines)


def _render_open_decisions(decisions: list) -> str:
    """Render the Open Decisions section."""
    lines = ["## 5. Open Decisions"]

    if not decisions:
        lines.append("")
        lines.append("*No open decisions identified.*")
        return "\n".join(lines)

    lines.append("")
    for i, item in enumerate(decisions, 1):
        decision = item.get("decision", "")
        options = item.get("options", [])
        blocking = item.get("blocking", False)
        context = item.get("context", "")

        blocking_label = "BLOCKING" if blocking else "Non-blocking"
        lines.append(f"### {i}. {decision}")
        lines.append("")
        lines.append(f"**Status:** {blocking_label}")
        if context:
            lines.append(f"")
            lines.append(context)
        if options:
            lines.append("")
            lines.append("**Options:**")
            for opt in options:
                lines.append(f"- {opt}")
        lines.append("")

    return "\n".join(lines)


def _render_documentation_gaps(gaps: list) -> str:
    """Render the Documentation Gaps section."""
    lines = ["## 6. Documentation Gaps"]

    if not gaps:
        lines.append("")
        lines.append("*No documentation gaps identified.*")
        return "\n".join(lines)

    lines.append("")
    for item in gaps:
        gap = item.get("gap", "")
        impact = item.get("impact", "")
        suggested_source = item.get("suggested_source", "")

        lines.append(f"### {gap}")
        lines.append("")
        if impact:
            lines.append(f"**Impact:** {impact}")
        if suggested_source:
            lines.append(f"")
            lines.append(f"**Suggested source:** {suggested_source}")
        lines.append("")

    return "\n".join(lines)
