"""Mermaid flowchart renderer for workflow execution paths.

This module provides the MermaidRenderer class which converts GraphPath objects
into valid Mermaid flowchart LR syntax for visualization.
"""

import re

from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath


class MermaidRenderer:
    """Renders workflow execution paths as Mermaid flowchart syntax.

    This stateless renderer converts a list of GraphPath objects into valid
    Mermaid flowchart LR syntax with proper node deduplication and edge
    formatting. The output is a complete markdown string with fenced code blocks.

    The renderer respects GraphBuildingContext configuration for:
    - Custom start/end node labels
    - camelCase name splitting (word wrapping)
    - Future expansion (decision labels, etc.)

    Example usage:
        >>> from temporalio_graphs.renderer import MermaidRenderer
        >>> from temporalio_graphs.path import GraphPath
        >>> from temporalio_graphs.context import GraphBuildingContext
        >>> renderer = MermaidRenderer()
        >>> path = GraphPath(path_id="path_0")
        >>> path.add_activity("ValidateInput")
        >>> path.add_activity("ProcessOrder")
        >>> context = GraphBuildingContext()
        >>> output = renderer.to_mermaid([path], context)
        >>> print(output)  # Outputs valid Mermaid markdown with diagram
    """

    def to_mermaid(self, paths: list[GraphPath], context: GraphBuildingContext) -> str:
        """Convert workflow execution paths to Mermaid flowchart syntax.

        Generates valid Mermaid flowchart LR syntax from a list of execution
        paths and configuration context. Output includes fenced code blocks
        with triple backticks and proper formatting.

        The algorithm uses a two-pass approach:
        1. First pass: Collect all node definitions and edge connections
           - Track seen node IDs and edges for deduplication
           - Validate activity names
           - Build node and edge collections
        2. Second pass: Output nodes block, then edges block
           - Output all unique node definitions
           - Output all unique edge definitions
           - Wrap with Mermaid fence and flowchart LR directive

        This ensures the output format matches architecture specification:
        all nodes grouped together, followed by all edges.

        Args:
            paths: List of GraphPath objects representing workflow execution
                paths. Each path contains an ordered sequence of activities
                in the steps attribute. May be empty (generates Start -> End).
            context: GraphBuildingContext providing configuration options:
                - start_node_label: Display label for Start node (default "Start")
                - end_node_label: Display label for End node (default "End")
                - split_names_by_words: If True, split camelCase to "camel Case"
                  (default True)

        Returns:
            A complete Mermaid markdown string with fenced code blocks:
            ```mermaid
            flowchart LR
            s((Start))
            1[Activity1]
            2[Activity2]
            e((End))
            s --> 1
            1 --> 2
            2 --> e
            ```
            Ready to include in documentation or pass to Mermaid viewers.

        Raises:
            ValueError: If any activity name in paths is None or empty string.
                Includes context about which path and step caused the error.

        Example:
            >>> renderer = MermaidRenderer()
            >>> path = GraphPath(path_id="path_0")
            >>> path.add_activity("Withdraw")
            '1'
            >>> path.add_activity("Deposit")
            '2'
            >>> context = GraphBuildingContext(
            ...     start_node_label="BEGIN",
            ...     end_node_label="FINISH",
            ...     split_names_by_words=False
            ... )
            >>> result = renderer.to_mermaid([path], context)
            >>> assert "```mermaid" in result
            >>> assert "flowchart LR" in result
            >>> assert "s((BEGIN))" in result
            >>> assert "1[Withdraw]" in result
            >>> assert "2[Deposit]" in result
            >>> assert "e((FINISH))" in result

        Note:
            In Epic 2, typically processes a single linear path. Epic 3 will
            extend this to handle multiple paths with reconverging nodes.
            Deduplication logic is foundation for that multi-path support.
        """
        # Initialize output structure - use lists to preserve order
        node_definitions: dict[str, str] = {}  # node_id -> definition
        edges: list[str] = []
        seen_edges: set[tuple[str, str, str]] = set()

        # First pass: collect all nodes and edges
        # Handle empty paths (edge case: Start -> End only)
        if not paths:
            node_definitions["s"] = f"s(({context.start_node_label}))"
            node_definitions["e"] = f"e(({context.end_node_label}))"
            edge_key = ("s", "e", "")
            edges.append("s --> e")
            seen_edges.add(edge_key)
        else:
            # Process each path
            for path in paths:
                # Add Start node
                if "s" not in node_definitions:
                    node_definitions["s"] = f"s(({context.start_node_label}))"

                # Process activities in path
                prev_node_id = "s"
                for step_index, activity_name in enumerate(path.steps, 1):
                    # Validate activity name
                    if activity_name is None or activity_name == "":
                        raise ValueError(
                            f"Activity name cannot be None or empty string in path "
                            f"{path.path_id} at step index {step_index}"
                        )

                    # Generate node ID (1-based index per GraphPath.add_activity pattern)
                    node_id = str(step_index)

                    # Apply word splitting if enabled
                    display_name = activity_name
                    if context.split_names_by_words:
                        display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", activity_name)

                    # Add activity node definition (deduplicated by dict key)
                    if node_id not in node_definitions:
                        node_definitions[node_id] = f"{node_id}[{display_name}]"

                    # Record edge connection (deduplicated by set)
                    edge_key = (prev_node_id, node_id, "")
                    if edge_key not in seen_edges:
                        edges.append(f"{prev_node_id} --> {node_id}")
                        seen_edges.add(edge_key)

                    prev_node_id = node_id

                # Add End node
                if "e" not in node_definitions:
                    node_definitions["e"] = f"e(({context.end_node_label}))"

                # Record edge to End node
                edge_key = (prev_node_id, "e", "")
                if edge_key not in seen_edges:
                    edges.append(f"{prev_node_id} --> e")
                    seen_edges.add(edge_key)

        # Second pass: build output with nodes first, then edges
        lines: list[str] = []
        lines.append("```mermaid")
        lines.append("flowchart LR")

        # Add all node definitions (preserve order: s, 1-n, e)
        for node_id in ["s"] + [str(i) for i in range(1, len(node_definitions))] + ["e"]:
            if node_id in node_definitions:
                lines.append(node_definitions[node_id])

        # Add all edge definitions
        for edge in edges:
            lines.append(edge)

        # Close Mermaid fence
        lines.append("```")

        return "\n".join(lines)

