"""
Command-line interface for clarity.

This module provides the main entry point for the clarity CLI tool.
It orchestrates the full pipeline: read inputs, synthesize analysis, write output.

Usage:
    clarity <task_context.md> --docs <doc1.md> <doc2.md> --code <dir1> <dir2>

Output:
    .clarity/scratch/design_analysis.md
"""

import argparse
import sys
from pathlib import Path

from clarity.readers import read_task_context, read_docs, read_code
from clarity.readers import TaskContextValidationError, DocsReadError, CodeReadError
from clarity.agents import synthesize, set_llm_client, SynthesisError, LLMClient
from clarity.writers import write_design_analysis, WriteError


def _create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.

    Returns an argparse.ArgumentParser configured with all supported options.
    """
    parser = argparse.ArgumentParser(
        prog="clarity",
        description="Generate structured design analysis before implementation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clarity task_context.md
  clarity task_context.md --docs README.md docs/api.md
  clarity task_context.md --docs README.md --code src/
  clarity task_context.md --docs README.md docs/arch.md --code src/ lib/
        """,
    )

    parser.add_argument(
        "task_context",
        type=str,
        help="Path to the task_context.md file",
    )

    parser.add_argument(
        "--docs",
        nargs="*",
        default=[],
        metavar="PATH",
        help="Paths to documentation files (markdown)",
    )

    parser.add_argument(
        "--code",
        nargs="*",
        default=[],
        metavar="PATH",
        help="Paths to code files or directories",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=".clarity/scratch/design_analysis.md",
        metavar="PATH",
        help="Output path for design analysis (default: .clarity/scratch/design_analysis.md)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse inputs only, skip synthesis (useful for testing)",
    )

    return parser


def _validate_paths(args: argparse.Namespace) -> list[str]:
    """
    Validate that all provided paths exist.

    Returns list of error messages, empty if all paths are valid.
    """
    errors = []

    # Check task context file
    if not Path(args.task_context).exists():
        errors.append(f"Task context file not found: {args.task_context}")

    # Check doc paths
    for doc_path in args.docs:
        if not Path(doc_path).exists():
            errors.append(f"Documentation file not found: {doc_path}")

    # Check code paths
    for code_path in args.code:
        if not Path(code_path).exists():
            errors.append(f"Code path not found: {code_path}")

    return errors


class StubLLMClient(LLMClient):
    """
    Stub LLM client for when no real LLM is configured.

    This produces a placeholder response indicating synthesis was skipped.
    In production, replace with a real LLM client implementation.
    """

    def complete(self, system_prompt: str, user_content: str) -> str:
        """Return a placeholder synthesis response."""
        return """{
    "system_intent": {
        "summary": "LLM client not configured - synthesis skipped",
        "key_points": ["Configure an LLM client to enable synthesis"],
        "citations": []
    },
    "observed_reality": {
        "summary": "Code observations were parsed but not analyzed",
        "relevant_code": [],
        "patterns_found": []
    },
    "feature_fit": {
        "alignments": [],
        "conflicts": []
    },
    "assumptions_and_risks": [
        {
            "assumption": "LLM synthesis is required for meaningful analysis",
            "source": "inferred",
            "risk_if_wrong": "Manual analysis needed",
            "validation_needed": "Configure LLM client"
        }
    ],
    "open_decisions": [
        {
            "decision": "Which LLM provider to use",
            "options": ["OpenAI", "Anthropic", "Local model"],
            "blocking": true,
            "context": "Synthesis requires an LLM client implementation"
        }
    ],
    "documentation_gaps": [],
    "confidence_assessment": {
        "overall": "low",
        "limiting_factors": ["No LLM configured for synthesis"],
        "sufficient_to_proceed": false
    }
}"""


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the CLI.

    Parses arguments, runs the pipeline, and returns exit code.
    Returns 0 on success, 1 on error.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _create_parser()
    args = parser.parse_args(argv)

    # Validate paths before processing
    path_errors = _validate_paths(args)
    if path_errors:
        for error in path_errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Read task context
        print(f"Reading task context: {args.task_context}")
        task_ctx = read_task_context(args.task_context)

        # Step 2: Read documentation (if provided)
        docs = {"documents": []}
        if args.docs:
            print(f"Reading documentation: {', '.join(args.docs)}")
            docs = read_docs(args.docs)

        # Step 3: Read code (if provided)
        code = {"files": []}
        if args.code:
            print(f"Reading code: {', '.join(args.code)}")
            code = read_code(args.code)

        # Dry run stops here
        if args.dry_run:
            print("Dry run complete - inputs parsed successfully")
            print(f"  Task: {task_ctx.get('task', 'N/A')}")
            print(f"  Docs: {len(docs.get('documents', []))} files")
            print(f"  Code: {len(code.get('files', []))} files")
            return 0

        # Step 4: Synthesize (requires LLM client)
        # Use stub client if none configured - in production, configure a real one
        try:
            from clarity.agents import get_llm_client
            get_llm_client()
        except SynthesisError:
            # No client configured, use stub
            print("Warning: No LLM client configured, using stub")
            set_llm_client(StubLLMClient())

        print("Running synthesis...")
        analysis = synthesize(task_ctx, docs, code)

        # Step 5: Write output
        print(f"Writing design analysis: {args.output}")
        write_design_analysis(analysis, str(output_path))

        print(f"Done! Output: {args.output}")
        return 0

    except TaskContextValidationError as e:
        print(f"Error: Task context validation failed: {e}", file=sys.stderr)
        return 1
    except DocsReadError as e:
        print(f"Error: Failed to read documentation: {e}", file=sys.stderr)
        return 1
    except CodeReadError as e:
        print(f"Error: Failed to read code: {e}", file=sys.stderr)
        return 1
    except SynthesisError as e:
        print(f"Error: Synthesis failed: {e}", file=sys.stderr)
        return 1
    except WriteError as e:
        print(f"Error: Failed to write output: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
