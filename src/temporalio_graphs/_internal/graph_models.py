"""Internal graph data models for workflow visualization.

This module contains the core data structures used internally for representing
workflow graphs. These models are not part of the public API and should not be
imported directly by library users.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class NodeType(Enum):
    """Type classification for workflow graph nodes.

    Each node type corresponds to a different workflow element and renders
    with distinct Mermaid syntax for visual differentiation in the diagram.

    Attributes:
        START: Workflow entry point (circular node with double parentheses).
        END: Workflow exit point (circular node with double parentheses).
        ACTIVITY: Temporal activity invocation (rectangular node).
        DECISION: Conditional branching point (diamond node).
        SIGNAL: Signal wait or condition check (hexagonal node).
    """

    START = "start"
    END = "end"
    ACTIVITY = "activity"
    DECISION = "decision"
    SIGNAL = "signal"


@dataclass
class GraphNode:
    """Represents a single node in the workflow graph.

    A node corresponds to a workflow element (activity, decision, signal, etc.)
    and is rendered as a specific shape in the Mermaid diagram based on its type.

    The to_mermaid() method generates the correct Mermaid syntax for the node,
    following the .NET Temporalio.Graphs format for compatibility with regression
    tests.

    Args:
        node_id: Unique identifier for this node in the graph. For activities,
            this is typically a sequential number ("1", "2", "3"). For special
            nodes, use "s" (start) and "e" (end).
        node_type: The type of workflow element this node represents.
        display_name: Human-readable label shown in the diagram. May be formatted
            from the original activity/decision name (e.g., PascalCase -> "Pascal Case").
        source_line: Optional line number in the workflow source code where this
            element is defined. Used for debugging and traceability.

    Example:
        >>> # Start node with circular rendering
        >>> start = GraphNode("s", NodeType.START, "Start", source_line=None)
        >>> start.to_mermaid()
        's((Start))'

        >>> # Activity node with rectangular rendering
        >>> activity = GraphNode("1", NodeType.ACTIVITY, "Validate Input", source_line=42)
        >>> activity.to_mermaid()
        '1[Validate Input]'

        >>> # Decision node with diamond rendering
        >>> decision = GraphNode("0", NodeType.DECISION, "HighValue", source_line=55)
        >>> decision.to_mermaid()
        '0{HighValue}'

        >>> # Signal node with hexagonal rendering
        >>> signal = GraphNode("2", NodeType.SIGNAL, "WaitForApproval", source_line=67)
        >>> signal.to_mermaid()
        '2{{WaitForApproval}}'
    """

    node_id: str
    node_type: NodeType
    display_name: str
    source_line: int | None = None

    def to_mermaid(self) -> str:
        """Generate Mermaid syntax for this node.

        Returns the node representation in Mermaid flowchart syntax, with the
        shape determined by node_type:

        - START/END: Double parentheses for circular nodes: s((Start))
        - ACTIVITY: Square brackets for rectangular nodes: 1[ActivityName]
        - DECISION: Curly braces for diamond nodes: 0{DecisionName}
        - SIGNAL: Double curly braces for hexagonal nodes: 2{{SignalName}}

        Returns:
            Mermaid node syntax string.

        Example:
            >>> GraphNode("s", NodeType.START, "Start").to_mermaid()
            's((Start))'
            >>> GraphNode("1", NodeType.ACTIVITY, "ProcessOrder").to_mermaid()
            '1[ProcessOrder]'
        """
        match self.node_type:
            case NodeType.START | NodeType.END:
                return f"{self.node_id}(({self.display_name}))"
            case NodeType.ACTIVITY:
                return f"{self.node_id}[{self.display_name}]"
            case NodeType.DECISION:
                return f"{self.node_id}{{{self.display_name}}}"
            case NodeType.SIGNAL:
                return f"{self.node_id}{{{{{self.display_name}}}}}"


@dataclass
class GraphEdge:
    """Represents a directed edge between two nodes in the workflow graph.

    Edges connect workflow elements to show execution flow. They can optionally
    include labels to indicate conditions (e.g., "yes"/"no" for decision branches,
    "Signaled"/"Timeout" for signal outcomes).

    This class implements __hash__ and __eq__ to support set-based deduplication,
    which is essential for removing duplicate edges when merging multiple execution
    paths in the Mermaid renderer (Story 2.5).

    Args:
        from_node: Node ID where the edge originates.
        to_node: Node ID where the edge terminates.
        label: Optional edge label shown on the connecting line. Common labels
            include "yes"/"no" for decisions and "Signaled"/"Timeout" for signals.

    Example:
        >>> # Simple unlabeled edge
        >>> edge1 = GraphEdge("s", "1", None)
        >>> edge1.to_mermaid()
        's --> 1'

        >>> # Labeled edge for decision branch
        >>> edge2 = GraphEdge("0", "1", "yes")
        >>> edge2.to_mermaid()
        '0 -- yes --> 1'

        >>> # Deduplication with sets
        >>> edge3 = GraphEdge("s", "1", None)
        >>> edge4 = GraphEdge("s", "1", None)
        >>> edges = {edge3, edge4}
        >>> len(edges)  # Only one edge stored
        1
    """

    from_node: str
    to_node: str
    label: str | None = None

    def to_mermaid(self) -> str:
        """Generate Mermaid syntax for this edge.

        Returns the edge representation in Mermaid flowchart syntax:

        - Without label: node1 --> node2
        - With label: node1 -- label --> node2

        Returns:
            Mermaid edge syntax string.

        Example:
            >>> GraphEdge("s", "1", None).to_mermaid()
            's --> 1'
            >>> GraphEdge("0", "1", "yes").to_mermaid()
            '0 -- yes --> 1'
        """
        if self.label is None:
            return f"{self.from_node} --> {self.to_node}"
        return f"{self.from_node} -- {self.label} --> {self.to_node}"

    def __hash__(self) -> int:
        """Compute hash for set-based deduplication.

        Uses a tuple of all fields to ensure edges are deduplicated based on
        complete equality (same nodes and same label).

        Returns:
            Hash value for this edge.
        """
        return hash((self.from_node, self.to_node, self.label))

    def __eq__(self, other: object) -> bool:
        """Check equality for set-based deduplication.

        Two edges are equal if they connect the same nodes with the same label.

        Args:
            other: Object to compare with.

        Returns:
            True if edges are equal, False otherwise.
        """
        if not isinstance(other, GraphEdge):
            return False
        return (
            self.from_node == other.from_node
            and self.to_node == other.to_node
            and self.label == other.label
        )


@dataclass
class WorkflowMetadata:
    """Metadata describing a workflow and its graph characteristics.

    This dataclass captures the results of workflow analysis, including all
    detected activities, decision points, and signals. It serves as a summary
    of the workflow structure before path generation and rendering.

    The calculate_total_paths static method computes the theoretical number of
    execution paths based on the permutation formula 2^(decisions + signals),
    which is critical for validating whether path generation is feasible.

    Args:
        workflow_class: Fully qualified class name of the workflow (e.g.,
            "myapp.workflows.MoneyTransferWorkflow").
        workflow_run_method: Name of the workflow's run method (typically "run").
        activities: List of activity method names detected in the workflow.
            Order matches the sequence of activity calls in the source code.
        decision_points: List of decision point identifiers detected in the
            workflow. Each decision creates 2 execution paths (true/false).
        signal_points: List of signal point identifiers detected in the workflow.
            Each signal creates 2 execution paths (success/timeout).
        source_file: Path to the Python source file containing the workflow.
        total_paths: Total number of execution paths that will be generated,
            calculated as 2^(len(decision_points) + len(signal_points)).

    Example:
        >>> from pathlib import Path
        >>> # Simple workflow with 2 decisions
        >>> metadata = WorkflowMetadata(
        ...     workflow_class="MoneyTransferWorkflow",
        ...     workflow_run_method="run",
        ...     activities=["Withdraw", "CurrencyConvert", "Deposit"],
        ...     decision_points=["NeedToConvert", "IsTFN_Known"],
        ...     signal_points=[],
        ...     source_file=Path("workflows.py"),
        ...     total_paths=4,
        ... )
        >>> assert metadata.total_paths == 4  # 2^2 = 4 paths

        >>> # Calculate paths for different scenarios
        >>> WorkflowMetadata.calculate_total_paths(0, 0)  # Linear workflow
        1
        >>> WorkflowMetadata.calculate_total_paths(2, 0)  # 2 decisions
        4
        >>> WorkflowMetadata.calculate_total_paths(2, 1)  # 2 decisions + 1 signal
        8
    """

    workflow_class: str
    workflow_run_method: str
    activities: list[str]
    decision_points: list[str]
    signal_points: list[str]
    source_file: Path
    total_paths: int

    @staticmethod
    def calculate_total_paths(num_decisions: int, num_signals: int) -> int:
        """Calculate total execution paths from decision and signal counts.

        Each decision point and signal point doubles the number of possible
        execution paths through the workflow. This follows the permutation
        formula: total_paths = 2^(num_decisions + num_signals).

        Args:
            num_decisions: Number of decision points in the workflow.
            num_signals: Number of signal points in the workflow.

        Returns:
            Total number of unique execution paths. Minimum value is 1
            (linear workflow with no branches).

        Example:
            >>> WorkflowMetadata.calculate_total_paths(0, 0)
            1
            >>> WorkflowMetadata.calculate_total_paths(3, 0)
            8
            >>> WorkflowMetadata.calculate_total_paths(2, 2)
            16
        """
        total: int = 2 ** (num_decisions + num_signals)
        return total
