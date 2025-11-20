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

        # Build mapping of decision IDs to their names from PathStep objects
        # With typed steps, we can directly identify decisions without heuristics
        decision_id_to_name: dict[str, str] = {}
        # Build mapping of signal names to their outcomes in each path
        signal_outcomes: dict[str, dict[str, str]] = {}  # path_id -> {signal_name -> outcome}

        if paths:
            # Use the first path to build the decision mapping
            first_path = paths[0]
            for step in first_path.steps:
                if step.node_type == 'decision' and step.decision_id:
                    decision_id_to_name[step.decision_id] = step.name

            # Build signal outcomes mapping for all paths
            for path in paths:
                signal_outcomes[path.path_id] = {}
                for step in path.steps:
                    if step.node_type == 'signal' and step.signal_outcome:
                        signal_outcomes[path.path_id][step.name] = step.signal_outcome

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

                # Process activities and decisions in path
                # With typed PathStep objects, we can directly check node_type
                prev_node_id = "s"
                for step_index, step in enumerate(path.steps, 1):
                    # Validate step
                    if step.name is None or step.name == "":
                        raise ValueError(
                            f"Step name cannot be None or empty string in path "
                            f"{path.path_id} at step index {step_index}"
                        )

                    # Determine node type directly from PathStep
                    is_decision = step.node_type == 'decision'
                    is_signal = step.node_type == 'signal'
                    is_child_workflow = step.node_type == 'child_workflow'
                    is_external_signal = step.node_type == 'external_signal'

                    if is_external_signal:
                        # External signal node - skip if show_external_signals is False
                        if not context.show_external_signals:
                            continue

                        # Use deterministic ID: ext_sig_{signal_name}_{line_number}
                        if step.line_number is None:
                            raise ValueError(
                                f"External signal step '{step.name}' missing line_number "
                                f"in path {path.path_id}"
                            )

                        node_id = f"ext_sig_{step.name}_{step.line_number}"

                        # Format label based on external_signal_label_style
                        if context.external_signal_label_style == "target-pattern":
                            target = step.target_workflow_pattern or "<unknown>"
                            display_name = f"Signal '{step.name}' to {target}"
                        else:  # "name-only"
                            display_name = f"Signal '{step.name}'"

                        # Add external signal node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            external_signal_node = GraphNode(
                                node_id, NodeType.EXTERNAL_SIGNAL, display_name
                            )
                            node_definitions[node_id] = external_signal_node.to_mermaid()

                        # Add dashed edge from previous node to external signal node
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )
                        elif prev_node_id in signal_outcomes[path.path_id]:
                            edge_label = signal_outcomes[path.path_id][prev_node_id]

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            if edge_label:
                                edge = f"{prev_node_id} -- {edge_label} -.signal.-> {node_id}"
                                edges.append(edge)
                            else:
                                edges.append(f"{prev_node_id} -.signal.-> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id

                    elif is_signal:
                        # Signal node - use signal name as node ID for reconvergence
                        node_id = step.name

                        # Apply word splitting if enabled
                        display_name = step.name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step.name)

                        # Add signal node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            signal_node = GraphNode(node_id, NodeType.SIGNAL, display_name)
                            node_definitions[node_id] = signal_node.to_mermaid()

                        # Add edge from previous node to signal node
                        # Check if previous node was a decision or signal to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )
                        elif prev_node_id in signal_outcomes[path.path_id]:
                            # Previous node is a signal - use its outcome as label
                            edge_label = signal_outcomes[path.path_id][prev_node_id]

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            # Use dashed edge if previous node is external signal
                            if prev_node_id.startswith("ext_sig_"):
                                if edge_label:
                                    edge = f"{prev_node_id} -- {edge_label} -.signal.-> {node_id}"
                                    edges.append(edge)
                                else:
                                    edges.append(f"{prev_node_id} -.signal.-> {node_id}")
                            else:
                                if edge_label:
                                    edges.append(f"{prev_node_id} -- {edge_label} --> {node_id}")
                                else:
                                    edges.append(f"{prev_node_id} --> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id

                    elif is_decision:
                        # Get decision ID directly from PathStep
                        if step.decision_id is None:
                            raise ValueError(
                                f"Decision step '{step.name}' missing decision_id "
                                f"in path {path.path_id}"
                            )

                        node_id = step.decision_id

                        # Apply word splitting if enabled
                        display_name = step.name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step.name)

                        # Add decision node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            decision_node = GraphNode(node_id, NodeType.DECISION, display_name)
                            node_definitions[node_id] = decision_node.to_mermaid()

                        # Add edges from previous node to decision node
                        # Check if previous node was a decision or signal to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )
                        elif prev_node_id in signal_outcomes[path.path_id]:
                            # Previous node is a signal - use its outcome as label
                            edge_label = signal_outcomes[path.path_id][prev_node_id]

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            # Use dashed edge if previous node is external signal
                            if prev_node_id.startswith("ext_sig_"):
                                if edge_label:
                                    edge = f"{prev_node_id} -- {edge_label} -.signal.-> {node_id}"
                                    edges.append(edge)
                                else:
                                    edges.append(f"{prev_node_id} -.signal.-> {node_id}")
                            else:
                                if edge_label:
                                    edges.append(f"{prev_node_id} -- {edge_label} --> {node_id}")
                                else:
                                    edges.append(f"{prev_node_id} --> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id

                    elif is_child_workflow:
                        # Child workflow node - use deterministic ID based on name + line number
                        # Format: child_{workflow_name}_{line} (lowercase for consistency)
                        if step.line_number is None:
                            raise ValueError(
                                f"Child workflow step '{step.name}' missing line_number "
                                f"in path {path.path_id}"
                            )

                        node_id = f"child_{step.name.lower()}_{step.line_number}"

                        # Apply word splitting if enabled
                        display_name = step.name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step.name)

                        # Add child workflow node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            child_workflow_node = GraphNode(
                                node_id, NodeType.CHILD_WORKFLOW, display_name
                            )
                            node_definitions[node_id] = child_workflow_node.to_mermaid()

                        # Add edge from previous node to child workflow node
                        # Check if previous node was a decision or signal to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )
                        elif prev_node_id in signal_outcomes[path.path_id]:
                            # Previous node is a signal - use its outcome as label
                            edge_label = signal_outcomes[path.path_id][prev_node_id]

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            # Use dashed edge if previous node is external signal
                            if prev_node_id.startswith("ext_sig_"):
                                if edge_label:
                                    edge = f"{prev_node_id} -- {edge_label} -.signal.-> {node_id}"
                                    edges.append(edge)
                                else:
                                    edges.append(f"{prev_node_id} -.signal.-> {node_id}")
                            else:
                                if edge_label:
                                    edges.append(f"{prev_node_id} -- {edge_label} --> {node_id}")
                                else:
                                    edges.append(f"{prev_node_id} --> {node_id}")
                            seen_edges.add(edge_key)

                        prev_node_id = node_id

                    else:
                        # This is an activity node
                        # Use activity NAME as node ID for natural reconvergence (.NET pattern)
                        # This makes the same activity across paths become the same node
                        node_id = step.name

                        # Apply word splitting if enabled
                        display_name = step.name
                        if context.split_names_by_words:
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", step.name)

                        # Add activity node definition (deduplicated by dict key)
                        if node_id not in node_definitions:
                            node_definitions[node_id] = f"{node_id}[{display_name}]"

                        # Add edge from previous node to this activity
                        # Check if previous node was a decision or signal to add appropriate label
                        edge_label = ""
                        if prev_node_id in path.decisions:
                            # Previous node is a decision - check its value
                            decision_value = path.decisions[prev_node_id]
                            edge_label = (
                                context.decision_true_label
                                if decision_value
                                else context.decision_false_label
                            )
                        elif prev_node_id in signal_outcomes[path.path_id]:
                            # Previous node is a signal - use its outcome as label
                            edge_label = signal_outcomes[path.path_id][prev_node_id]

                        edge_key = (prev_node_id, node_id, edge_label)
                        if edge_key not in seen_edges:
                            # Use dashed edge if previous node is external signal
                            if prev_node_id.startswith("ext_sig_"):
                                if edge_label:
                                    edge = f"{prev_node_id} -- {edge_label} -.signal.-> {node_id}"
                                    edges.append(edge)
                                else:
                                    edges.append(f"{prev_node_id} -.signal.-> {node_id}")
                            else:
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
                # Check if previous node was a decision or signal to add appropriate label
                edge_label_to_end = ""
                if prev_node_id in path.decisions:
                    # Previous node is a decision - check its value
                    decision_value = path.decisions[prev_node_id]
                    edge_label_to_end = (
                        context.decision_true_label
                        if decision_value
                        else context.decision_false_label
                    )
                elif prev_node_id in signal_outcomes[path.path_id]:
                    # Previous node is a signal - use its outcome as label
                    edge_label_to_end = signal_outcomes[path.path_id][prev_node_id]

                edge_key = (prev_node_id, "e", edge_label_to_end)
                if edge_key not in seen_edges:
                    # Use dashed edge if previous node is external signal
                    if prev_node_id.startswith("ext_sig_"):
                        if edge_label_to_end:
                            edge = f"{prev_node_id} -- {edge_label_to_end} -.signal.-> e"
                            edges.append(edge)
                        else:
                            edges.append(f"{prev_node_id} -.signal.-> e")
                    else:
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

        # Add style directives for external signal nodes (orange/amber color)
        for node_id, node_def in node_definitions.items():
            if node_id.startswith("ext_sig_"):
                lines.append(f"style {node_id} fill:#fff4e6,stroke:#ffa500")

        # Close Mermaid fence
        lines.append("```")

        return "\n".join(lines)

