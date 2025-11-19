"""Configuration context for graph building.

This module provides the GraphBuildingContext dataclass which holds all
configuration options for workflow graph generation.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GraphBuildingContext:
    """Configuration context for workflow graph generation.

    This immutable configuration object controls all aspects of graph building,
    including output options, node labeling, and resource limits. Once created,
    the configuration cannot be modified, ensuring consistent behavior across
    the graph generation pipeline.

    All fields have sensible defaults for typical use cases. The context is
    designed to be created once and passed through the analysis pipeline without
    modification.

    Args:
        is_building_graph: Enable graph building mode. When False, workflow
            executes normally without graph generation. Default: True.
        exit_after_building_graph: Exit workflow immediately after completing
            graph generation. Useful for static analysis without executing
            workflow logic. Default: False.
        graph_output_file: Optional path where the generated Mermaid diagram
            will be written. If None, output goes to stdout. Default: None.
        split_names_by_words: Convert PascalCase/snake_case activity names to
            "Pascal Case" / "Snake Case" in graph labels for readability.
            Default: True.
        suppress_validation: Disable graph validation warnings (e.g., excessive
            decision points, path explosion, unreachable activities). Default: False.
        include_validation_report: Include validation report in output when warnings
            exist. Has no effect if suppress_validation is True. Default: True.
        start_node_label: Display label for the workflow start node.
            Default: "Start".
        end_node_label: Display label for the workflow end node.
            Default: "End".
        max_decision_points: Maximum allowed decision points before emitting a
            validation warning. Helps prevent path explosion (2^n paths).
            Default: 10 (generates up to 1024 paths).
        max_paths: Maximum allowed total execution paths before emitting a
            validation warning. Default: 1024.
        decision_true_label: Edge label for decision branches evaluating to True.
            Used in Epic 3 decision node rendering. Default: "yes".
        decision_false_label: Edge label for decision branches evaluating to False.
            Used in Epic 3 decision node rendering. Default: "no".
        signal_success_label: Edge label for successful signal completion.
            Used in Epic 4 signal node rendering. Default: "Signaled".
        signal_timeout_label: Edge label for signal timeout paths.
            Used in Epic 4 signal node rendering. Default: "Timeout".

    Example:
        >>> # Basic usage with defaults
        >>> ctx = GraphBuildingContext()
        >>> assert ctx.is_building_graph is True
        >>> assert ctx.max_decision_points == 10

        >>> # Custom configuration for production
        >>> from pathlib import Path
        >>> ctx = GraphBuildingContext(
        ...     graph_output_file=Path("workflow_diagram.md"),
        ...     max_decision_points=15,
        ...     split_names_by_words=False,
        ... )
        >>> assert ctx.graph_output_file == Path("workflow_diagram.md")

        >>> # Configuration is immutable
        >>> try:
        ...     ctx.max_paths = 2048  # This will raise an error
        ... except AttributeError:
        ...     pass  # Expected: frozen dataclass prevents mutation
    """

    is_building_graph: bool = True
    exit_after_building_graph: bool = False
    graph_output_file: Path | None = None
    split_names_by_words: bool = True
    suppress_validation: bool = False
    include_validation_report: bool = True
    start_node_label: str = "Start"
    end_node_label: str = "End"
    max_decision_points: int = 10
    max_paths: int = 1024
    decision_true_label: str = "yes"
    decision_false_label: str = "no"
    signal_success_label: str = "Signaled"
    signal_timeout_label: str = "Timeout"
