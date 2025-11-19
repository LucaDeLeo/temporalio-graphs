"""Path generation for workflow graph construction.

This module provides the PathPermutationGenerator class which transforms
WorkflowMetadata (containing activity sequences and decision points) into
GraphPath objects representing execution paths through the workflow.

Epic 2 scope: Linear workflows only (0 decisions, single execution path).
Epic 3 scope: Decision-based permutations (2^n paths for n decision points).
"""

import logging
from itertools import product

from temporalio_graphs._internal.graph_models import (
    Activity,
    DecisionPoint,
    SignalPoint,
    WorkflowMetadata,
)
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.exceptions import GraphGenerationError
from temporalio_graphs.path import GraphPath

logger = logging.getLogger(__name__)


class PathPermutationGenerator:
    """Generates execution paths from workflow metadata.

    Transforms WorkflowMetadata (which contains activity sequences and decision
    points) into GraphPath objects suitable for Mermaid diagram rendering.

    For linear workflows (0 decision points), creates a single execution path
    containing all activities in order. For workflows with decision points,
    generates 2^n paths representing all possible true/false combinations
    of decisions using efficient itertools.product iteration.

    The generator respects GraphBuildingContext configuration for node labeling,
    decision branch labels, and validates workflow constraints (e.g., explosion
    limit checking).

    Example:
        >>> from pathlib import Path
        >>> from temporalio_graphs._internal.graph_models import WorkflowMetadata, DecisionPoint
        >>> from temporalio_graphs.context import GraphBuildingContext
        >>> from temporalio_graphs.generator import PathPermutationGenerator
        >>>
        >>> # Linear workflow (0 decisions)
        >>> metadata = WorkflowMetadata(
        ...     workflow_class="SimpleWorkflow",
        ...     workflow_run_method="run",
        ...     activities=["ValidateInput", "ProcessOrder", "SendConfirmation"],
        ...     decision_points=[],
        ...     signal_points=[],
        ...     source_file=Path("workflows.py"),
        ...     total_paths=1,
        ... )
        >>>
        >>> generator = PathPermutationGenerator()
        >>> paths = generator.generate_paths(metadata, GraphBuildingContext())
        >>> assert len(paths) == 1  # Linear workflows generate 1 path
        >>> assert paths[0].path_id == "path_0"
        >>> assert paths[0].steps == ["ValidateInput", "ProcessOrder", "SendConfirmation"]
        >>>
        >>> # Workflow with 1 decision (2 paths)
        >>> decision = DecisionPoint(
        ...     id="d0",
        ...     name="HighValue",
        ...     line_number=42,
        ...     true_label="yes",
        ...     false_label="no",
        ... )
        >>> metadata2 = WorkflowMetadata(
        ...     workflow_class="PaymentWorkflow",
        ...     workflow_run_method="run",
        ...     activities=["Withdraw", "Deposit"],
        ...     decision_points=[decision],
        ...     signal_points=[],
        ...     source_file=Path("workflows.py"),
        ...     total_paths=2,
        ... )
        >>>
        >>> paths2 = generator.generate_paths(metadata2, GraphBuildingContext())
        >>> assert len(paths2) == 2  # 2^1 = 2 paths for 1 decision
    """

    def generate_paths(
        self, metadata: WorkflowMetadata, context: GraphBuildingContext
    ) -> list[GraphPath]:
        """Generate execution paths from workflow metadata.

        For linear workflows (0 decision points), creates a single GraphPath
        containing all activities in sequential order. For workflows with
        decision points, generates 2^n paths representing all possible
        true/false combinations using itertools.product for efficient generation.

        This method performs validation on input parameters and raises
        informative errors for invalid inputs or unsupported workflow types.

        Args:
            metadata: WorkflowMetadata object from analyzer containing activity
                list and decision point list. Required.
            context: GraphBuildingContext configuration for graph generation
                (node labels, max decision points, decision branch labels, etc.).
                Required.

        Returns:
            A list containing GraphPath objects representing execution paths
            through the workflow. For linear workflows (0 decisions), returns
            a list with exactly one GraphPath element. For workflows with n
            decision points, returns 2^n GraphPath elements.

        Raises:
            ValueError: If metadata is None or context is None. Provides
                actionable error messages with suggestions for fix.
            GraphGenerationError: If the number of decision points exceeds
                context.max_decision_points, which would generate too many paths.
                Error message includes the calculated path count and limit,
                plus a suggestion to refactor or increase the limit.

        Example:
            >>> import time
            >>> from pathlib import Path
            >>> from temporalio_graphs._internal.graph_models import WorkflowMetadata, DecisionPoint
            >>> from temporalio_graphs.context import GraphBuildingContext
            >>>
            >>> # Workflow with 2 decisions generates 4 paths (2^2)
            >>> d1 = DecisionPoint("d0", "NeedConvert", 42, "yes", "no")
            >>> d2 = DecisionPoint("d1", "HighValue", 55, "yes", "no")
            >>> metadata = WorkflowMetadata(
            ...     workflow_class="PaymentWorkflow",
            ...     workflow_run_method="run",
            ...     activities=["Withdraw", "CurrencyConvert", "Deposit"],
            ...     decision_points=[d1, d2],
            ...     signal_points=[],
            ...     source_file=Path("workflows.py"),
            ...     total_paths=4,
            ... )
            >>>
            >>> generator = PathPermutationGenerator()
            >>> paths = generator.generate_paths(metadata, GraphBuildingContext())
            >>> assert len(paths) == 4, f"Expected 4 paths, got {len(paths)}"
            >>> # Each path has a different combination of decisions
            >>> path_decisions = [p.decisions for p in paths]
            >>> assert {'d0': True, 'd1': True} in path_decisions
            >>> assert {'d0': True, 'd1': False} in path_decisions
            >>> assert {'d0': False, 'd1': True} in path_decisions
            >>> assert {'d0': False, 'd1': False} in path_decisions

        Notes:
            Start and End nodes are NOT included in path.steps. Renderer
            adds them implicitly when generating Mermaid output.

            Node IDs are auto-generated by GraphPath methods in sequential order:
            "1", "2", "3", etc., regardless of whether they are activities or
            decision nodes.

            Decision node labels are controlled by context.decision_true_label and
            context.decision_false_label (default: "yes" and "no").
        """
        # Validate inputs
        if metadata is None:
            raise ValueError(
                "metadata cannot be None. Pass WorkflowMetadata from analyzer.analyze()."
            )

        if context is None:
            logger.debug("context is None, using GraphBuildingContext defaults")
            context = GraphBuildingContext()

        # Check for decision points + signal points and explosion limit
        num_decisions = len(metadata.decision_points)
        num_signals = len(metadata.signal_points)
        total_branch_points = num_decisions + num_signals

        # Validate explosion limit (decisions + signals combined)
        if total_branch_points > context.max_decision_points:
            paths_count = 2**total_branch_points
            raise GraphGenerationError(
                f"Too many branch points ({total_branch_points}) would generate "
                f"{paths_count} paths (limit: {context.max_decision_points}). "
                f"Branch points: {num_decisions} decisions + {num_signals} signals. "
                f"Suggestion: Refactor workflow or increase max_decision_points limit"
            )

        # Log path generation start
        if total_branch_points == 0:
            logger.debug(
                f"Generating paths for linear workflow with {len(metadata.activities)} activities"
            )
            # Create single linear path for linear workflows
            path = self._create_linear_path(metadata.activities)
            logger.debug(f"Created path with ID: {path.path_id}")
            return [path]
        else:
            logger.debug(
                f"Generating {2**total_branch_points} paths for workflow with "
                f"{num_decisions} decision points, {num_signals} signal points, "
                f"and {len(metadata.activities)} activities"
            )
            # Generate permutations for workflows with decisions and/or signals
            paths = self._generate_paths_with_branches(
                metadata.decision_points, metadata.signal_points, metadata.activities, context
            )
            logger.debug(
                f"Generated {len(paths)} paths for workflow with {num_decisions} decisions "
                f"and {num_signals} signals"
            )
            return paths

    def _create_linear_path(self, activities: list[Activity]) -> GraphPath:
        """Create a single linear path from activity sequence.

        Helper method that constructs a GraphPath with all activities in order.
        This implements the Epic 2 algorithm: create path with path_id="path_0",
        add each activity sequentially, return the path.

        Args:
            activities: List of Activity objects or strings in order from workflow analysis.
                May be empty for workflows with no activities.

        Returns:
            GraphPath with path_id="path_0" and all activities added in order
            via add_activity() calls.
        """
        path = GraphPath(path_id="path_0")

        # Add all activities in sequence
        for activity in activities:
            # Handle both Activity objects and strings for backward compatibility
            if isinstance(activity, str):
                path.add_activity(activity)
            else:
                path.add_activity(activity.name)

        return path

    def _generate_paths_with_branches(
        self,
        decisions: list[DecisionPoint],
        signals: list[SignalPoint],
        activities: list[Activity],
        context: GraphBuildingContext,
    ) -> list[GraphPath]:
        """Generate 2^n execution paths for workflows with decision and signal points.

        Uses itertools.product to efficiently generate all 2^n boolean combinations
        for the given decision and signal points. For each combination, creates a GraphPath
        that records the decisions, signals, and activities in PROPER EXECUTION ORDER by
        merging and sorting them by source line number.

        This method implements the Epic 3/4 path permutation algorithm using the
        efficient C-optimized itertools.product function, maintaining O(2^n)
        time complexity while avoiding manual recursion.

        CRITICAL: Activities, decisions, and signals are interleaved based on their source
        line numbers to generate correct branching topology instead of incorrect sequential
        linear topology.

        Args:
            decisions: List of DecisionPoint objects from workflow analysis.
            signals: List of SignalPoint objects from workflow analysis.
            activities: List of Activity objects from workflow analysis.
            context: GraphBuildingContext for configuration (branch labels, etc.).

        Returns:
            List of GraphPath objects, one for each 2^n permutation. Each path
            contains the activities, decisions, and signals for that specific execution path
            in correct source code order.

        Example:
            >>> from temporalio_graphs._internal.graph_models import Activity
            >>> decisions = [
            ...     DecisionPoint("d0", "NeedConvert", 42, 42, "yes", "no"),
            ... ]
            >>> signals = [
            ...     SignalPoint(
            ...         "WaitApproval", "lambda: approved", "timedelta(hours=24)", 55, "sig_0"
            ...     ),
            ... ]
            >>> activities = [
            ...     Activity("Withdraw", 35),
            ...     Activity("Deposit", 60),
            ... ]
            >>> context = GraphBuildingContext()
            >>> gen = PathPermutationGenerator()
            >>> paths = gen._generate_paths_with_branches(decisions, signals, activities, context)
            >>> len(paths)
            4
            >>> # Each path should have a unique decision+signal combination
            >>> for path in paths:
            ...     assert len(path.decisions) == 1
        """
        num_decisions = len(decisions)
        num_signals = len(signals)
        total_branches = num_decisions + num_signals
        paths: list[GraphPath] = []

        # Merge activities, decisions, and signals with their positions
        # Each element is a tuple: (node_type, node_object, line_number)
        execution_order: list[tuple[str, Activity | DecisionPoint | SignalPoint, int]] = []
        for i, activity in enumerate(activities):
            execution_order.append(('activity', activity, activity.line_num))
        for decision in decisions:
            execution_order.append(('decision', decision, decision.line_num))
        for signal in signals:
            execution_order.append(('signal', signal, signal.source_line))

        # Sort by line number to get execution order
        execution_order.sort(key=lambda x: x[2])

        # Generate all 2^n boolean combinations using itertools.product
        for path_index, branch_values in enumerate(
            product([False, True], repeat=total_branches)
        ):
            # Create path ID in binary format for clarity
            # path_0b00, path_0b01, path_0b10, path_0b11, etc.
            binary_str = "".join(str(int(v)) for v in branch_values)
            path_id = f"path_0b{binary_str}"

            # Create new path for this permutation
            path = GraphPath(path_id=path_id)

            # Build decision and signal value lookup dictionaries for this permutation
            decision_value_map = {}
            signal_value_map = {}

            # Assign values to decisions first, then signals
            branch_index = 0
            for decision in decisions:
                decision_value_map[decision.id] = branch_values[branch_index]
                branch_index += 1
            for signal in signals:
                signal_value_map[signal.node_id] = branch_values[branch_index]
                branch_index += 1

            # Track decisions and signals encountered so far in this path (for control flow)
            decisions_encountered: list[DecisionPoint] = []
            signals_encountered: list[SignalPoint] = []

            # Add nodes in correct interleaved order based on source line numbers
            # Only include activities that match the decision/signal path (control flow aware)
            for node_type, node, line_num in execution_order:
                if node_type == 'activity':
                    # node is Activity object
                    assert isinstance(node, Activity)
                    activity_name = node.name
                    activity_line = node.line_num

                    # Check if this activity is conditional on any decision or signal
                    should_include_activity = True

                    for decision in decisions_encountered:
                        # Check if activity is in this decision's true branch
                        if activity_line in decision.true_branch_activities:
                            # Activity is conditional on decision being True
                            if not decision_value_map[decision.id]:
                                should_include_activity = False
                                break
                        # Check if activity is in this decision's false branch
                        elif activity_line in decision.false_branch_activities:
                            # Activity is conditional on decision being False
                            if decision_value_map[decision.id]:
                                should_include_activity = False
                                break
                        # If not in either branch, activity is unconditional
                        # relative to this decision

                    # Check if this activity is conditional on any signal
                    for signal in signals_encountered:
                        # Check if activity is in this signal's signaled branch
                        if activity_line in signal.signaled_branch_activities:
                            # Activity is conditional on signal being Signaled (True)
                            if not signal_value_map[signal.node_id]:
                                should_include_activity = False
                                break
                        # Check if activity is in this signal's timeout branch
                        elif activity_line in signal.timeout_branch_activities:
                            # Activity is conditional on signal being Timeout (False)
                            if signal_value_map[signal.node_id]:
                                should_include_activity = False
                                break
                        # If not in either branch, activity is unconditional
                        # relative to this signal

                    # Only add activity if it should execute in this path
                    if should_include_activity:
                        path.add_activity(activity_name)

                elif node_type == 'decision':
                    # node is DecisionPoint object
                    assert isinstance(node, DecisionPoint)
                    value = decision_value_map[node.id]
                    path.add_decision(node.id, value, node.name)
                    # Track this decision for checking future activities
                    decisions_encountered.append(node)

                elif node_type == 'signal':
                    # node is SignalPoint object
                    assert isinstance(node, SignalPoint)
                    value = signal_value_map[node.node_id]
                    # True = Signaled, False = Timeout
                    outcome = (
                        context.signal_success_label
                        if value
                        else context.signal_timeout_label
                    )
                    path.add_signal(node.name, outcome)
                    # Track this signal for checking future activities
                    signals_encountered.append(node)

            paths.append(path)

        return paths
