"""Internal graph data models for workflow visualization.

This module contains the core data structures used internally for representing
workflow graphs. These models are not part of the public API and should not be
imported directly by library users.
"""

from dataclasses import dataclass, field
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
        CHILD_WORKFLOW: Child workflow execution (subroutine node).
        EXTERNAL_SIGNAL: External signal sent to peer workflow (trapezoid node).
    """

    START = "start"
    END = "end"
    ACTIVITY = "activity"
    DECISION = "decision"
    SIGNAL = "signal"
    CHILD_WORKFLOW = "child_workflow"
    EXTERNAL_SIGNAL = "external_signal"


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
        r"""Generate Mermaid syntax for this node.

        Returns the node representation in Mermaid flowchart syntax, with the
        shape determined by node_type:

        - START/END: Double parentheses for circular nodes: s((Start))
        - ACTIVITY: Square brackets for rectangular nodes: 1[ActivityName]
        - DECISION: Curly braces for diamond nodes: 0{DecisionName}
        - SIGNAL: Double curly braces for hexagonal nodes: 2{{SignalName}}
        - CHILD_WORKFLOW: Double square brackets for subroutine: 3[[ChildWorkflow]]
        - EXTERNAL_SIGNAL: Trapezoid for async signal: 4[/ExternalSignal\]

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
            case NodeType.CHILD_WORKFLOW:
                # Child workflow nodes render with double brackets (subroutine notation)
                return f"{self.node_id}[[{self.display_name}]]"
            case NodeType.EXTERNAL_SIGNAL:
                # External signal nodes render with trapezoid (forward/backslash)
                return f"{self.node_id}[/{self.display_name}\\]"


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


@dataclass(frozen=True)
class Activity:
    """Represents an activity invocation in a workflow.

    An activity is a unit of work executed by Temporal, identified by an
    execute_activity() call in the workflow code. Activities are tracked
    with their source line numbers for proper ordering in the graph.

    The frozen=True attribute ensures Activity instances are immutable,
    preventing accidental modifications to activity metadata once created.

    Args:
        name: Human-readable name of the activity (extracted from the
            execute_activity() call argument).
        line_num: Line number in the workflow source code where the activity
            is invoked. Used for sorting activities and decisions into correct
            execution order.

    Example:
        >>> activity = Activity(
        ...     name="withdraw_funds",
        ...     line_num=35,
        ... )
        >>> activity.name
        'withdraw_funds'
        >>> activity.line_num
        35
    """

    name: str
    line_num: int


@dataclass(frozen=True)
class DecisionPoint:
    """Represents a decision point (branch) in a workflow.

    A decision point is a location in the workflow where execution can branch
    based on a boolean condition, identified by an explicit to_decision() call.
    Each decision doubles the number of possible execution paths.

    The frozen=True attribute ensures DecisionPoint instances are immutable,
    preventing accidental modifications to decision metadata once created.

    Args:
        id: Unique identifier for this decision point (hash-based or sequential).
        name: Human-readable display name for the decision point (extracted from
            the second argument of to_decision()).
        line_number: Line number in the workflow source code where the decision
            is defined. Used for error reporting and debugging.
        line_num: Line number in the workflow source code where the decision
            is defined. Used for sorting activities and decisions into correct
            execution order.
        true_label: Label for the "true" branch (typically "yes").
        false_label: Label for the "false" branch (typically "no").

    Example:
        >>> decision = DecisionPoint(
        ...     id="d1",
        ...     name="NeedToConvert",
        ...     line_number=42,
        ...     line_num=42,
        ...     true_label="yes",
        ...     false_label="no",
        ... )
        >>> decision.name
        'NeedToConvert'
        >>> decision.line_number
        42
    """

    id: str
    name: str
    line_number: int
    line_num: int
    true_label: str
    false_label: str
    # Control flow tracking: line numbers of activities in each branch
    true_branch_activities: tuple[int, ...] = ()
    false_branch_activities: tuple[int, ...] = ()


@dataclass(frozen=True)
class SignalPoint:
    """Represents a signal/wait condition point in a workflow.

    A signal point is a location where workflow waits for external event or condition,
    identified by wait_condition() call. Each signal creates 2 execution paths (Signaled/Timeout).

    The frozen=True attribute ensures SignalPoint instances are immutable,
    preventing accidental modifications to signal metadata once created.

    Args:
        name: Human-readable display name for signal node (from 3rd argument of wait_condition).
        condition_expr: String representation of condition check expression (1st argument).
        timeout_expr: String representation of timeout duration (2nd argument).
        source_line: Line number in workflow source code where signal is defined.
        node_id: Unique deterministic identifier for this signal node (sig_{name}_{line}).

    Example:
        >>> signal = SignalPoint(
        ...     name="WaitForApproval",
        ...     condition_expr="lambda: self.approved",
        ...     timeout_expr="timedelta(hours=24)",
        ...     source_line=67,
        ...     node_id="sig_waitforapproval_67"
        ... )
        >>> signal.name
        'WaitForApproval'
        >>> signal.source_line
        67
    """

    name: str
    condition_expr: str
    timeout_expr: str
    source_line: int
    node_id: str
    # Control flow tracking: line numbers of activities in each branch
    signaled_branch_activities: tuple[int, ...] = ()
    timeout_branch_activities: tuple[int, ...] = ()


@dataclass(frozen=True)
class ChildWorkflowCall:
    """Represents a child workflow execution call in a parent workflow.

    A child workflow call is a location where the parent workflow invokes another workflow
    via workflow.execute_child_workflow(). This is detected for cross-workflow visualization
    to show dependencies between parent and child workflows.

    The frozen=True attribute ensures ChildWorkflowCall instances are immutable,
    preventing accidental modifications to call metadata once created.

    Args:
        workflow_name: Name of the child workflow class or string identifier.
            Can be extracted from either a class reference (MyWorkflow) or
            string literal ("MyWorkflow").
        call_site_line: Line number in parent workflow source code where the
            execute_child_workflow() call is made.
        call_id: Unique identifier for this child workflow call within the parent.
            Format: child_{workflow_name}_{line}
        parent_workflow: Name of the parent workflow class containing this call.

    Example:
        >>> child_call = ChildWorkflowCall(
        ...     workflow_name="ProcessOrderWorkflow",
        ...     call_site_line=45,
        ...     call_id="child_processorderworkflow_45",
        ...     parent_workflow="CheckoutWorkflow"
        ... )
        >>> child_call.workflow_name
        'ProcessOrderWorkflow'
        >>> child_call.call_site_line
        45
    """

    workflow_name: str
    call_site_line: int
    call_id: str
    parent_workflow: str


@dataclass(frozen=True)
class ExternalSignalCall:
    """Represents a peer-to-peer signal sent to an external workflow.

    An external signal call is detected when a workflow uses
    workflow.get_external_workflow_handle() to obtain a handle to another workflow
    and then calls .signal() on that handle to send a signal. This enables
    peer-to-peer communication visualization between workflows.

    The frozen=True attribute ensures ExternalSignalCall instances are immutable,
    preventing accidental modifications to signal metadata once created.

    Args:
        signal_name: Name of the signal being sent (from first argument to .signal()).
        target_workflow_pattern: Pattern describing the target workflow ID.
            Can be: exact string literal ("shipping-123"), wildcard pattern for
            f-strings ("ship-{*}"), or "<dynamic>" for variables/function calls.
        source_line: Line number in source code where the signal call is made.
        node_id: Unique identifier for this signal node in the graph.
            Format: ext_sig_{signal_name}_{line_number}
        source_workflow: Name of the workflow class sending the signal.

    Example:
        >>> signal_call = ExternalSignalCall(
        ...     signal_name="ship_order",
        ...     target_workflow_pattern="shipping-123",
        ...     source_line=45,
        ...     node_id="ext_sig_ship_order_45",
        ...     source_workflow="OrderWorkflow"
        ... )
        >>> signal_call.signal_name
        'ship_order'
        >>> signal_call.target_workflow_pattern
        'shipping-123'
    """

    signal_name: str
    target_workflow_pattern: str
    source_line: int
    node_id: str
    source_workflow: str


@dataclass(frozen=True)
class SignalHandler:
    """Represents a @workflow.signal decorated method in a workflow class.

    A signal handler is a method that can receive external signals from other
    workflows. Signal handlers are detected via @workflow.signal decorator on
    async or sync methods. The signal name can be explicitly provided via the
    name= argument or defaults to the method name.

    The frozen=True attribute ensures SignalHandler instances are immutable,
    preventing accidental modifications to handler metadata once created.

    Args:
        signal_name: Name of the signal this handler receives. Either explicitly
            provided via @workflow.signal(name="custom") or defaults to method name.
        method_name: Actual Python method name of the signal handler.
        workflow_class: Name of the workflow class containing this signal handler.
        source_line: Line number in source code where the method is defined.
        node_id: Unique identifier for this handler in the graph.
            Format: sig_handler_{signal_name}_{line_number}

    Example:
        >>> signal_handler = SignalHandler(
        ...     signal_name="ship_order",
        ...     method_name="ship_order",
        ...     workflow_class="ShippingWorkflow",
        ...     source_line=67,
        ...     node_id="sig_handler_ship_order_67"
        ... )
        >>> signal_handler.signal_name
        'ship_order'
        >>> signal_handler.workflow_class
        'ShippingWorkflow'
    """

    signal_name: str
    method_name: str
    workflow_class: str
    source_line: int
    node_id: str


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
        activities: List of Activity objects detected in the workflow.
            Order matches the sequence of activity calls in the source code,
            including line number information for proper graph topology.
        decision_points: List of decision point identifiers detected in the
            workflow. Each decision creates 2 execution paths (true/false).
        signal_points: List of signal point identifiers detected in the workflow.
            Each signal creates 2 execution paths (success/timeout).
        source_file: Path to the Python source file containing the workflow.
        total_paths: Total number of execution paths that will be generated,
            calculated as 2^(len(decision_points) + len(signal_points)).
        child_workflow_calls: List of child workflow calls detected in the workflow
            (from Epic 6).
        external_signals: Tuple of external signals sent to peer workflows
            (from Epic 7). External signals are sequential nodes that don't
            create branching.
        signal_handlers: Tuple of signal handlers detected in the workflow
            (from Epic 8). Signal handlers are @workflow.signal decorated methods
            that can receive signals from external workflows.

    Example:
        >>> from pathlib import Path
        >>> # Simple workflow with 2 decisions
        >>> metadata = WorkflowMetadata(
        ...     workflow_class="MoneyTransferWorkflow",
        ...     workflow_run_method="run",
        ...     activities=[
        ...         Activity("Withdraw", 35),
        ...         Activity("CurrencyConvert", 42),
        ...         Activity("Deposit", 55),
        ...     ],
        ...     decision_points=[
        ...         DecisionPoint("d0", "NeedToConvert", 38, 38, "yes", "no"),
        ...         DecisionPoint("d1", "IsTFN_Known", 48, 48, "yes", "no"),
        ...     ],
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
    activities: list[Activity]
    decision_points: list[DecisionPoint]
    signal_points: list[SignalPoint]
    source_file: Path
    total_paths: int
    child_workflow_calls: list[ChildWorkflowCall] = field(default_factory=list)
    external_signals: tuple[ExternalSignalCall, ...] = ()
    signal_handlers: tuple[SignalHandler, ...] = ()

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

    @property
    def total_branch_points(self) -> int:
        """Total decision + signal points (determines path count).

        Returns:
            Sum of decision points and signal points in workflow.
        """
        return len(self.decision_points) + len(self.signal_points)

    @property
    def total_paths_from_branches(self) -> int:
        """Calculate total execution paths from branch points.

        Returns:
            2^(total_branch_points) representing all path permutations.
        """
        result: int = 2**self.total_branch_points
        return result


@dataclass(frozen=True)
class MultiWorkflowPath:
    """Represents a complete end-to-end execution path across multiple workflows.

    A multi-workflow path captures a single execution sequence that spans parent and
    child workflows, showing complete end-to-end flow across workflow boundaries. This
    is used for inline mode cross-workflow visualization where parent paths are expanded
    to include all child workflow steps.

    The frozen=True attribute ensures MultiWorkflowPath instances are immutable,
    preventing accidental modifications to path structure once created.

    Args:
        path_id: Unique identifier for this end-to-end path (e.g., "mwpath_0", "mwpath_1").
        workflows: Ordered list of workflow class names traversed in this path, starting
            with root workflow and including all child workflows encountered.
        steps: Ordered list of all step names (activities, decisions, signals, child workflows)
            encountered in this end-to-end path across all workflows.
        workflow_transitions: List of workflow boundary crossings in this path. Each tuple
            is (step_index, from_workflow, to_workflow) where step_index is 0-based position
            in steps list where transition occurs.
        total_decisions: Total number of decision points across all workflows in this path.
            Used for path explosion calculations and validation.

    Example:
        >>> # Parent workflow calling child workflow
        >>> mw_path = MultiWorkflowPath(
        ...     path_id="mwpath_0",
        ...     workflows=["ParentWorkflow", "ChildWorkflow"],
        ...     steps=[
        ...         "ParentActivity1",
        ...         "ParentDecision",
        ...         "ChildActivity1",
        ...         "ChildDecision",
        ...         "ParentActivity2",
        ...     ],
        ...     workflow_transitions=[
        ...         (2, "ParentWorkflow", "ChildWorkflow"),
        ...         (4, "ChildWorkflow", "ParentWorkflow"),
        ...     ],
        ...     total_decisions=2
        ... )
        >>> mw_path.workflows
        ['ParentWorkflow', 'ChildWorkflow']
        >>> len(mw_path.workflow_transitions)
        2
    """

    path_id: str
    workflows: list[str]
    steps: list[str]
    workflow_transitions: list[tuple[int, str, str]]
    total_decisions: int


@dataclass(frozen=True)
class WorkflowCallGraph:
    """Represents a complete workflow call graph for multi-workflow analysis.

    A workflow call graph captures all workflows (parent and children) discovered during
    recursive analysis, their relationships, and call metadata. This is the primary output
    of WorkflowCallGraphAnalyzer and serves as input for cross-workflow visualization.

    The frozen=True attribute ensures WorkflowCallGraph instances are immutable,
    preventing accidental modifications to call graph structure once created.

    Args:
        root_workflow: WorkflowMetadata for the entry point workflow.
        child_workflows: Dictionary mapping child workflow class names to their
            WorkflowMetadata. Contains all discovered child workflows recursively.
        call_relationships: List of (parent_name, child_name) tuples representing
            parent-child relationships in the call graph. Forms a directed graph.
        all_child_calls: Complete list of ChildWorkflowCall objects from all workflows.
            Used for cross-workflow path generation and visualization.
        total_workflows: Total number of workflows in the graph (root + children).

    Example:
        >>> root = WorkflowMetadata(...)  # Parent workflow
        >>> child1 = WorkflowMetadata(...)  # Child workflow
        >>> call_graph = WorkflowCallGraph(
        ...     root_workflow=root,
        ...     child_workflows={"ChildWorkflow": child1},
        ...     call_relationships=[("ParentWorkflow", "ChildWorkflow")],
        ...     all_child_calls=[
        ...         ChildWorkflowCall(
        ...             "ChildWorkflow",
        ...             45,
        ...             "child_childworkflow_45",
        ...             "ParentWorkflow",
        ...         )
        ...     ],
        ...     total_workflows=2
        ... )
        >>> call_graph.total_workflows
        2
        >>> len(call_graph.child_workflows)
        1
    """

    root_workflow: WorkflowMetadata
    child_workflows: dict[str, WorkflowMetadata]
    call_relationships: list[tuple[str, str]]
    all_child_calls: list[ChildWorkflowCall]
    total_workflows: int
