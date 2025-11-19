"""Temporalio-graphs: Generate workflow visualization diagrams from Temporal workflows.

This library provides static code analysis of Temporal Python workflows to generate
complete Mermaid flowchart diagrams showing all possible execution paths.

Quick start:
    >>> from temporalio_graphs import analyze_workflow
    >>> result = analyze_workflow("my_workflow.py")
    >>> print(result)  # Prints Mermaid diagram
"""

from pathlib import Path
from typing import Literal

from temporalio_graphs._internal.graph_models import MultiWorkflowPath
from temporalio_graphs.analyzer import WorkflowAnalyzer
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import (
    GraphGenerationError,
    InvalidDecisionError,
    TemporalioGraphsError,
    UnsupportedPatternError,
    WorkflowParseError,
)
from temporalio_graphs.formatter import format_path_list
from temporalio_graphs.generator import PathPermutationGenerator
from temporalio_graphs.helpers import to_decision, wait_condition
from temporalio_graphs.renderer import MermaidRenderer
from temporalio_graphs.validator import ValidationReport, ValidationWarning, validate_workflow

__version__ = "0.1.0"

__all__ = [
    "GraphBuildingContext",
    "MultiWorkflowPath",
    "analyze_workflow",
    "to_decision",
    "wait_condition",
    "ValidationWarning",
    "ValidationReport",
    "TemporalioGraphsError",
    "WorkflowParseError",
    "UnsupportedPatternError",
    "GraphGenerationError",
    "InvalidDecisionError",
]


def _validate_context(context: GraphBuildingContext) -> None:
    """Validate GraphBuildingContext configuration options.

    Args:
        context: GraphBuildingContext to validate.

    Raises:
        ValueError: If any configuration value is invalid.
        TypeError: If any configuration field has wrong type.
    """
    if context.max_decision_points <= 0:
        raise ValueError(
            f"max_decision_points must be positive, got {context.max_decision_points}. "
            f"Consider increasing this value (default: 10)"
        )

    if context.max_paths <= 0:
        raise ValueError(
            f"max_paths must be positive, got {context.max_paths}. "
            f"Consider increasing this value (default: 1024)"
        )

    if not isinstance(context.start_node_label, str):
        raise TypeError(
            f"start_node_label must be string, got {type(context.start_node_label).__name__}"
        )

    if not isinstance(context.end_node_label, str):
        raise TypeError(
            f"end_node_label must be string, got {type(context.end_node_label).__name__}"
        )


def analyze_workflow(
    workflow_file: Path | str,
    context: GraphBuildingContext | None = None,
    output_format: Literal["mermaid", "json", "paths"] = "mermaid",
) -> str:
    """Analyze workflow source file and return graph representation.

    Performs static code analysis on the workflow file to detect workflow
    structure and generate a complete visualization diagram. The workflow
    code is NEVER executed during analysis.

    Args:
        workflow_file: Path to Python workflow source file (.py).
            Can be absolute or relative path, as string or Path object.
        context: Optional configuration for graph generation. If None,
            uses GraphBuildingContext() defaults. Customize to change
            node labels, enable/disable word splitting, etc.
        output_format: Output format mode. Controls which sections are included:
            - "mermaid": Mermaid diagram only (default, backward compatible)
            - "paths": Path list only (no diagram, no validation)
            - "json": Reserved for future use (not yet implemented)
            Note: GraphBuildingContext.output_format can override this for
            "full" mode (Mermaid + path list + validation).

    Returns:
        Graph representation as string in requested format.
        - "mermaid": Complete markdown with fenced code blocks
        - "paths": Text-based path list showing all execution paths
        - If context.output_format="full": Mermaid + path list + validation

    Raises:
        ValueError: If workflow_file is None or output_format is invalid.
        FileNotFoundError: If workflow_file does not exist.
        PermissionError: If workflow_file is not readable.
        WorkflowParseError: If workflow file cannot be parsed, no
            @workflow.defn decorator found, or workflow structure invalid.

    Example:
        Basic usage (3 lines):

        >>> from temporalio_graphs import analyze_workflow
        >>> result = analyze_workflow("my_workflow.py")
        >>> print(result)
        ```mermaid
        flowchart LR
        s((Start)) --> 1[Activity Name]
        1 --> e((End))
        ```

    Example:
        With custom configuration:

        >>> from temporalio_graphs import analyze_workflow, GraphBuildingContext
        >>> context = GraphBuildingContext(
        ...     split_names_by_words=False,
        ...     start_node_label="BEGIN"
        ... )
        >>> result = analyze_workflow("workflow.py", context)

    Note:
        This function performs STATIC ANALYSIS only. It does not execute
        the workflow code or invoke any activities.

        Epic 2 scope: Linear workflows only (no decision points or signals).
        Decision support will be added in Epic 3.
    """
    # Validate inputs
    if workflow_file is None:
        raise ValueError("workflow_file parameter required, cannot be None")

    workflow_path = Path(workflow_file)

    if output_format not in ("mermaid", "paths", "json"):
        raise ValueError(
            f"output_format '{output_format}' not supported. "
            f"Use 'mermaid', 'paths', or 'json'."
        )

    if output_format == "json":
        raise ValueError(
            "output_format 'json' is reserved for future use (not yet implemented)"
        )

    # Track whether context was explicitly provided
    context_provided = context is not None

    # Prepare context
    if context is None:
        context = GraphBuildingContext()

    # Validate context configuration
    _validate_context(context)

    # Analyze workflow (file validation happens in analyzer)
    analyzer = WorkflowAnalyzer()
    metadata = analyzer.analyze(workflow_path, context)

    # Generate execution paths
    generator = PathPermutationGenerator()
    paths = generator.generate_paths(metadata, context)

    # Validate workflow quality (do this before output assembly)
    validation_report = validate_workflow(metadata, paths, context)

    # Determine effective output format
    # Priority: parameter > explicit context.output_format > default context.output_format
    # If context was explicitly provided and has output_format, use context's value
    # Otherwise, use parameter value (which defaults to "mermaid" for backward compat)
    if context_provided and hasattr(context, 'output_format'):
        # Context was explicitly provided, respect its output_format preference
        effective_format = context.output_format
    else:
        # No explicit context provided, use parameter value
        effective_format = output_format

    # Assemble output parts based on format
    output_parts: list[str] = []

    # Conditional Mermaid rendering
    if effective_format in ("mermaid", "full"):
        renderer = MermaidRenderer()
        mermaid_output = renderer.to_mermaid(paths, context)
        output_parts.append(mermaid_output)

    # Conditional path list
    if effective_format in ("paths", "full"):
        # Check if context has include_path_list field (backward compat)
        include_list = getattr(context, 'include_path_list', True)
        if include_list:
            path_list = format_path_list(paths)
            output_parts.append(path_list.format())

    # Conditional validation report (only in full mode)
    if effective_format == "full" and context.include_validation_report:
        if validation_report.has_warnings():
            output_parts.append(validation_report.format())

    # Join output parts with newline
    result = "\n".join(output_parts)

    # Write to file if configured
    if context.graph_output_file is not None:
        output_path = Path(context.graph_output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")

    return result
