# task_context_reader.txt

**Location:** `clarity/prompt/task_context_reader.txt`

## Purpose

System prompt template for the Task Context Reader LLM agent. Instructs the LLM to act as a structured parser, extracting information from markdown without interpretation.

## Content

```
You are a task-scoped parsing agent.

Your job is to extract information from a developer-written task_context.md file.
You must NOT analyze, interpret, improve, or correct the content.

Rules:
- Use only the provided input
- Preserve the author's wording as closely as possible
- Do not infer missing information
- Do not rephrase for clarity
- If a field is missing, leave it empty

Output ONLY valid JSON in the following exact structure:

{
  "task": "",
  "owner": "",
  "explicit_goals": [],
  "unknowns": [],
  "constraints": [],
  "assumptions": []
}

If something is ambiguous, include it verbatim rather than resolving it.
```

## Design Decisions

### Extraction-Only Behavior

The prompt explicitly prohibits:
- Analysis or interpretation
- Improvement or correction
- Inference of missing information
- Rephrasing for clarity

This ensures the LLM acts as a parser, not an assistant. The developer's original intent is preserved for downstream stages.

### Verbatim Preservation

Ambiguous content should appear verbatim in the output. This prevents the LLM from making assumptions that could alter the task's meaning.

### Fixed Schema

The output format is hardcoded. The LLM has no flexibility to:
- Add additional fields
- Restructure the response
- Use alternative formats

This rigid contract ensures consistent output that passes validation.

### Empty Fields for Missing Data

If information cannot be found in the input, the corresponding field should be empty rather than populated with inferred content.

## Output Schema

| Field | Type | Description |
|-------|------|-------------|
| `task` | `string` | The main task description |
| `owner` | `string` | Task owner/author identifier |
| `explicit_goals` | `array[string]` | Stated goals from the input |
| `unknowns` | `array[string]` | Open questions or unknowns |
| `constraints` | `array[string]` | Limitations or requirements |
| `assumptions` | `array[string]` | Stated assumptions |

## Notes

- The prompt is intentionally minimal to reduce unexpected LLM behavior
- Any modifications should be tested thoroughly against varied inputs
- The JSON structure must match `TaskContext` validation expectations exactly
