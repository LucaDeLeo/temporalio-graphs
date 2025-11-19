"""Mermaid flowchart renderer for workflow execution paths.

This module provides the MermaidRenderer class which converts GraphPath objects
into valid Mermaid flowchart LR syntax for visualization.
"""

import re

from temporalio_graphs._internal.graph_models import GraphNode, NodeType
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
           - Handle both activity nodes and decision nodes
        2. Second pass: Output nodes block, then edges block
           - Output all unique node definitions
           - Output all unique edge definitions
           - Wrap with Mermaid fence and flowchart LR directive

        This ensures the output format matches architecture specification:
        all nodes grouped together, followed by all edges.

        Decision nodes are rendered as diamond shapes with yes/no branch labels
        from the GraphBuildingContext configuration.

        Args:
            paths: List of GraphPath objects representing workflow execution
                paths. Each path contains an ordered sequence of activities
                and decisions in the steps attribute. May be empty (generates Start -> End).
            context: GraphBuildingContext providing configuration options:
                - start_node_label: Display label for Start node (default "Start")
                - end_node_label: Display label for End node (default "End")
                - split_names_by_words: If True, split camelCase to "camel Case"
                  (default True)
                - decision_true_label: Label for true branches (default "yes")
                - decision_false_label: Label for false branches (default "no")

        Returns:
            A complete Mermaid markdown string with fenced code blocks:
            ```mermaid
            flowchart LR
            s((Start))
            1[Activity1]
            0{Decision}
            2[Activity2]
            e((End))
            s --> 1
            1 --> 0
            0 -- yes --> 2
            0 -- no --> 3
            2 --> e
            ```
            Ready to include in documentation or pass to Mermaid viewers.

        Raises:
            ValueError: If any step name in paths is None or empty string.
                Includes context about which path and step caused the error.

        Example:
            >>> renderer = MermaidRenderer()
            >>> path = GraphPath(path_id="path_0")
            >>> path.add_activity("Withdraw")
            '1'
            >>> decision_id = path.add_decision("d0", True, "HighValue")
            >>> path.add_activity("Deposit")
            >>> context = GraphBuildingContext(
            ...     start_node_label="BEGIN",
            ...     end_node_label="FINISH",
            ...     split_names_by_words=False
            ... )
            >>> result = renderer.to_mermaid([path], context)
            >>> assert "```mermaid" in result
            >>> assert "flowchart LR" in result
            >>> assert "d0{HighValue}" in result
            >>> assert "-- yes -->" in result

        Note:
            In Epic 2, typically processes a single linear path. Epic 3 handles
            multiple paths with reconverging nodes and decision branches.
            Deduplication ensures each decision node appears only once.
        """
        # Initialize output structure - use lists to preserve order
        node_definitions: dict[str, str] = {}  # node_id -> definition
        edges: list[str] = []
        seen_edges: set[tuple[str, str, str]] = set()

        # Build mapping of decision IDs to their names by analyzing all paths
        # The first path gives us the decision order
        decision_id_to_name: dict[str, str] = {}
        if paths and paths[0].decisions:
            # Get the first path to determine decision names in order
            first_path = paths[0]
            # All decisions come after all activities in the generator output
            # We need to map decision IDs to their names
            # The path.decisions dict has ID->value, but we need ID->name
            # We can infer this from the step order

            # For now, we'll map by matching the order of decisions in the path
            # The generator adds decisions in the order they appear in metadata.decision_points
            # So first path.decisions key (in iteration order) corresponds to first decision name
            # and so on

            # Better approach: iterate through the steps and identify decision names
            # by checking which are NOT in the metadata.activities list
            # Since we don't have metadata here, we'll use a heuristic:
            # The generator adds activities first, then decisions
            # So we can identify decisions by the fact that there are
            # len(path.steps) - len(path.decisions) activities

            num_activities = len(first_path.steps) - len(first_path.decisions)
            decision_step_names = first_path.steps[num_activities:]

            # Now map decision IDs to these names in order
            for i, decision_id in enumerate(sorted(first_path.decisions.keys())):
                if i < len(decision_step_names):
                    decision_id_to_name[decision_id] = decision_step_names[i]

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

                # Build a mapping of decision names in this path
                # to identify which steps are decisions
                decision_names_in_path = (
                    set(decision_id_to_name.values())
                    if decision_id_to_name
                    else set()
                )

                # Process activities and decisions in path
                prev_node_id = "s"
                activity_counter = 0  # CRITICAL FIX: Separate counter for activities only
                for step_index, step_name in enumerate(path.steps, 1):
                    # Validate step name
                    if step_name is None:
                        raise ValueError(
                            f"Activity name cannot be None or empty string in path "
                            f"{path.path_id} at step index {step_index}"
                        )
                    if step_name == "":
                        raise ValueError(
                            f"Activity name cannot be None or empty string in path "
                            f"{path.path_id} at step index {step_index}"
                        )

                    # Determine if this is a decision or activity
                    is_decision = step_name in decision_names_in_path

                    if is_decision:
                        # Find the decision ID for this decision name
                        found_decision_id: str | None = None
                        for dec_id, dec_name in decision_id_to_name.items():
                            if dec_name == step_name:
                                found_decision_id = dec_id
                                break

                        if found_decision_id is None:
                            # Shouldn't happen, but handle gracefully
                            raise ValueError(
                                f"Could not find decision ID for decision name '{step_name}' "
                                f"in path {path.path_id}"
                            )

                        node_id = found_decision_id

                        # Apply word splitting if enabled
                        display_name = step_name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step_name)

                        # Add decision node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            decision_node = GraphNode(node_id, NodeType.DECISION, display_name)
                            node_definitions[node_id] = decision_node.to_mermaid()

                        # Add edges from previous node to decision node
                        # Check if previous node was a decision to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            if edge_label:
                                edges.append(f"{prev_node_id} -- {edge_label} --> {node_id}")
                            else:
                                edges.append(f"{prev_node_id} --> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id
                    else:
                        # This is an activity node
                        # CRITICAL FIX: Use separate activity_counter instead of step_index
                        activity_counter += 1
                        node_id = str(activity_counter)

                        # Apply word splitting if enabled
                        display_name = step_name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step_name)

                        # Add activity node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            node_definitions[node_id] = f"{node_id}[{display_name}]"

                        # Add edge from previous node to this activity
                        # Check if previous node was a decision to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            if edge_label:
                                edges.append(f"{prev_node_id} -- {edge_label} --> {node_id}")
                            else:
                                edges.append(f"{prev_node_id} --> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id

                # Add End node
                if "e" not in node_definitions:
                    node_definitions["e"] = f"e(({context.end_node_label}))"

                # Record edge to End node
                # Check if previous node was a decision to add appropriate label
                edge_label_to_end = ""
                if prev_node_id in path.decisions:
                    # Previous node is a decision - check its value
                    decision_value = path.decisions[prev_node_id]
                    edge_label_to_end = (
                        context.decision_true_label
                        if decision_value
                        else context.decision_false_label
                    )

                edge_key = (prev_node_id, "e", edge_label_to_end)
                if edge_key not in seen_edges:
                    if edge_label_to_end:
                        edges.append(f"{prev_node_id} -- {edge_label_to_end} --> e")
                    else:
                        edges.append(f"{prev_node_id} --> e")
                    seen_edges.add(edge_key)

        # Second pass: build output with nodes first, then edges
        lines: list[str] = []
        lines.append("```mermaid")
        lines.append("flowchart LR")

        # Add all node definitions (preserve order: s, then numbered/decision nodes, then e)
        # Collect numeric and decision node IDs separately
        numeric_ids = []
        decision_ids = []

        for node_id in node_definitions.keys():
            if node_id == "s" or node_id == "e":
                continue
            if node_id.isdigit():
                numeric_ids.append(int(node_id))
            else:
                decision_ids.append(node_id)

        numeric_ids.sort()

        # Output nodes in order: s, numeric nodes, decision nodes, e
        output_order = ["s"] + [str(i) for i in numeric_ids] + sorted(decision_ids) + ["e"]

        for node_id in output_order:
            if node_id in node_definitions:
                lines.append(node_definitions[node_id])

        # Add all edge definitions
        for edge in edges:
            lines.append(edge)

        # Close Mermaid fence
        lines.append("```")

        return "\n".join(lines)

