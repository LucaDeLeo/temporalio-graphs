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
    ChildWorkflowCall,
    DecisionPoint,
    ExternalSignalCall,
    MultiWorkflowPath,
    SignalPoint,
    WorkflowCallGraph,
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
        paths_count = 2**total_branch_points if total_branch_points > 0 else 1

        # Validate explosion limit (decisions + signals combined)
        if total_branch_points > context.max_decision_points:
            raise GraphGenerationError(
                reason=(
                    f"Too many branch points ({total_branch_points}) would generate "
                    f"{paths_count} paths (limit: {context.max_decision_points}). "
                    f"Branch points: {num_decisions} decisions + {num_signals} signals. "
                    f"Suggestion: Refactor workflow or increase max_decision_points limit"
                ),
                context={
                    "decision_count": num_decisions,
                    "signal_count": num_signals,
                    "total_branch_points": total_branch_points,
                    "limit": context.max_decision_points,
                    "paths_count": paths_count,
                },
            )

        # Validate absolute path count ceiling to prevent path explosion
        if paths_count > context.max_paths:
            raise GraphGenerationError(
                reason=(
                    f"Calculated path count ({paths_count}) exceeds max_paths limit "
                    f"({context.max_paths}). Total branch points: {total_branch_points} "
                    f"({num_decisions} decisions + {num_signals} signals). "
                    f"Suggestion: Reduce decisions/signals or increase context.max_paths"
                ),
                context={
                    "decision_count": num_decisions,
                    "signal_count": num_signals,
                    "total_branch_points": total_branch_points,
                    "paths_count": paths_count,
                    "max_paths_limit": context.max_paths,
                },
            )

        # Log path generation start
        if total_branch_points == 0:
            logger.debug(
                f"Generating paths for linear workflow with {len(metadata.activities)} activities, "
                f"{len(metadata.child_workflow_calls)} child workflows, and "
                f"{len(metadata.external_signals)} external signals"
            )
            # Create single linear path for linear workflows
            path = self._create_linear_path(
                metadata.activities,
                metadata.child_workflow_calls,
                metadata.external_signals,
            )
            logger.debug(f"Created path with ID: {path.path_id}")
            return [path]
        else:
            logger.debug(
                f"Generating {paths_count} paths for workflow with "
                f"{num_decisions} decision points, {num_signals} signal points, "
                f"{len(metadata.activities)} activities, and "
                f"{len(metadata.child_workflow_calls)} child workflows"
            )
            # Generate permutations for workflows with decisions and/or signals
            paths = self._generate_paths_with_branches(
                metadata.decision_points,
                metadata.signal_points,
                metadata.activities,
                metadata.child_workflow_calls,
                metadata.external_signals,
                context,
            )
            logger.debug(
                f"Generated {len(paths)} paths for workflow with {num_decisions} decisions "
                f"and {num_signals} signals"
            )
            return paths

    def _create_linear_path(
        self,
        activities: list[Activity],
        child_workflows: list[ChildWorkflowCall],
        external_signals: tuple[ExternalSignalCall, ...],
    ) -> GraphPath:
        """Create a single linear path from activity, child workflow, and external signal sequence.

        Helper method that constructs a GraphPath with all activities, child workflows, and
        external signals in execution order based on source line numbers. This implements the
        Epic 2 algorithm extended for Epic 6 and Epic 7: create path with path_id="path_0",
        add each activity, child workflow, and external signal sequentially in source code order,
        return the path.

        Args:
            activities: List of Activity objects in order from workflow analysis.
                May be empty for workflows with no activities.
            child_workflows: List of ChildWorkflowCall objects in order from workflow analysis.
                May be empty for workflows with no child workflow calls.
            external_signals: Tuple of ExternalSignalCall objects in order from workflow analysis.
                May be empty for workflows with no external signals.

        Returns:
            GraphPath with path_id="path_0" and all activities/child workflows/external signals
            added in source line order via add_activity(), add_child_workflow(), and
            add_external_signal() calls.
        """
        path = GraphPath(path_id="path_0")

        # Merge activities, child workflows, and external signals, then sort by line number
        execution_order: list[
            tuple[str, Activity | ChildWorkflowCall | ExternalSignalCall | str, int]
        ] = []
        for activity in activities:
            # Handle both Activity objects and strings for backward compatibility
            if isinstance(activity, str):
                # Strings don't have line numbers, so use index as fallback for ordering
                execution_order.append(("activity", activity, activities.index(activity)))
            else:
                execution_order.append(("activity", activity, activity.line_num))
        for child_workflow in child_workflows:
            execution_order.append(
                ("child_workflow", child_workflow, child_workflow.call_site_line)
            )
        for external_signal in external_signals:
            execution_order.append(
                ("external_signal", external_signal, external_signal.source_line)
            )

        # Sort by line number to get execution order
        execution_order.sort(key=lambda x: x[2])

        # Add all nodes in sequence
        for node_type, node, _ in execution_order:
            if node_type == "activity":
                # Handle both Activity objects and strings for backward compatibility
                if isinstance(node, str):
                    path.add_activity(node)
                else:
                    assert isinstance(node, Activity)
                    path.add_activity(node.name)
            elif node_type == "child_workflow":
                assert isinstance(node, ChildWorkflowCall)
                path.add_child_workflow(node.workflow_name, node.call_site_line)
            elif node_type == "external_signal":
                assert isinstance(node, ExternalSignalCall)
                path.add_external_signal(
                    node.signal_name, node.target_workflow_pattern, node.source_line
                )

        return path

    def _generate_paths_with_branches(
        self,
        decisions: list[DecisionPoint],
        signals: list[SignalPoint],
        activities: list[Activity],
        child_workflows: list[ChildWorkflowCall],
        external_signals: tuple[ExternalSignalCall, ...],
        context: GraphBuildingContext,
    ) -> list[GraphPath]:
        """Generate 2^n execution paths for workflows with decision and signal points.

        Uses itertools.product to efficiently generate all 2^n boolean combinations
        for the given decision and signal points. For each combination, creates a GraphPath
        that records the decisions, signals, activities, child workflows, and external signals
        in PROPER EXECUTION ORDER by merging and sorting them by source line number.

        This method implements the Epic 3/4/6/7 path permutation algorithm using the
        efficient C-optimized itertools.product function, maintaining O(2^n)
        time complexity while avoiding manual recursion.

        CRITICAL: Activities, decisions, signals, child workflows, and external signals are
        interleaved based on their source line numbers to generate correct branching topology
        instead of incorrect sequential linear topology. External signals do NOT create
        branches - they are sequential nodes like activities.

        Args:
            decisions: List of DecisionPoint objects from workflow analysis.
            signals: List of SignalPoint objects from workflow analysis.
            activities: List of Activity objects from workflow analysis.
            child_workflows: List of ChildWorkflowCall objects from workflow analysis.
            external_signals: Tuple of ExternalSignalCall objects from workflow analysis.
            context: GraphBuildingContext for configuration (branch labels, etc.).

        Returns:
            List of GraphPath objects, one for each 2^n permutation. Each path
            contains the activities, decisions, signals, child workflows, and external
            signals for that specific execution path in correct source code order.

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

        # Import ExternalSignalCall for type checking
        from temporalio_graphs._internal.graph_models import ExternalSignalCall

        # Merge activities, decisions, signals, child workflows, and external signals with positions
        # Each element is a tuple: (node_type, node_object, line_number)
        execution_order: list[
            tuple[
                str,
                Activity | DecisionPoint | SignalPoint | ChildWorkflowCall | ExternalSignalCall,
                int,
            ]
        ] = []
        for i, activity in enumerate(activities):
            execution_order.append(("activity", activity, activity.line_num))
        for decision in decisions:
            execution_order.append(("decision", decision, decision.line_num))
        for signal in signals:
            execution_order.append(("signal", signal, signal.source_line))
        for child_workflow in child_workflows:
            execution_order.append(
                ("child_workflow", child_workflow, child_workflow.call_site_line)
            )
        for external_signal in external_signals:
            execution_order.append(
                ("external_signal", external_signal, external_signal.source_line)
            )

        # Sort by line number to get execution order
        execution_order.sort(key=lambda x: x[2])

        # Generate all 2^n boolean combinations using itertools.product
        for path_index, branch_values in enumerate(product([False, True], repeat=total_branches)):
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
                if node_type == "activity":
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

                elif node_type == "decision":
                    # node is DecisionPoint object
                    assert isinstance(node, DecisionPoint)
                    value = decision_value_map[node.id]
                    path.add_decision(node.id, value, node.name)
                    # Track this decision for checking future activities
                    decisions_encountered.append(node)

                elif node_type == "signal":
                    # node is SignalPoint object
                    assert isinstance(node, SignalPoint)
                    value = signal_value_map[node.node_id]
                    # True = Signaled, False = Timeout
                    outcome = (
                        context.signal_success_label if value else context.signal_timeout_label
                    )
                    path.add_signal(node.name, outcome)
                    # Track this signal for checking future activities
                    signals_encountered.append(node)

                elif node_type == "child_workflow":
                    # node is ChildWorkflowCall object
                    assert isinstance(node, ChildWorkflowCall)
                    # Child workflows are treated like activities (linear, no branching)
                    # Add them unconditionally unless they're in a conditional branch
                    child_workflow_line = node.call_site_line
                    should_include_child_workflow = True

                    # Check if this child workflow is conditional on any decision
                    for decision in decisions_encountered:
                        if child_workflow_line in decision.true_branch_activities:
                            if not decision_value_map[decision.id]:
                                should_include_child_workflow = False
                                break
                        elif child_workflow_line in decision.false_branch_activities:
                            if decision_value_map[decision.id]:
                                should_include_child_workflow = False
                                break

                    # Check if this child workflow is conditional on any signal
                    for signal in signals_encountered:
                        if child_workflow_line in signal.signaled_branch_activities:
                            if not signal_value_map[signal.node_id]:
                                should_include_child_workflow = False
                                break
                        elif child_workflow_line in signal.timeout_branch_activities:
                            if signal_value_map[signal.node_id]:
                                should_include_child_workflow = False
                                break

                    # Only add child workflow if it should execute in this path
                    if should_include_child_workflow:
                        path.add_child_workflow(node.workflow_name, node.call_site_line)

                elif node_type == "external_signal":
                    # node is ExternalSignalCall object
                    assert isinstance(node, ExternalSignalCall)
                    # External signals are treated like activities (linear, no branching)
                    # Add them unconditionally unless they're in a conditional branch
                    external_signal_line = node.source_line
                    should_include_external_signal = True

                    # Check if this external signal is conditional on any decision
                    for decision in decisions_encountered:
                        if external_signal_line in decision.true_branch_activities:
                            if not decision_value_map[decision.id]:
                                should_include_external_signal = False
                                break
                        elif external_signal_line in decision.false_branch_activities:
                            if decision_value_map[decision.id]:
                                should_include_external_signal = False
                                break

                    # Check if this external signal is conditional on any signal
                    for signal in signals_encountered:
                        if external_signal_line in signal.signaled_branch_activities:
                            if not signal_value_map[signal.node_id]:
                                should_include_external_signal = False
                                break
                        elif external_signal_line in signal.timeout_branch_activities:
                            if signal_value_map[signal.node_id]:
                                should_include_external_signal = False
                                break

                    # Only add external signal if it should execute in this path
                    if should_include_external_signal:
                        path.add_external_signal(
                            node.signal_name, node.target_workflow_pattern, node.source_line
                        )

            paths.append(path)

        return paths

    def generate_cross_workflow_paths(
        self, call_graph: WorkflowCallGraph, context: GraphBuildingContext
    ) -> list[MultiWorkflowPath]:
        """Generate end-to-end execution paths across parent and child workflows.

        Generates complete execution paths that span workflow boundaries based on the
        configured expansion mode. Three modes are supported:

        1. Reference mode (default): Child workflows appear as atomic nodes with no
           path expansion. Returns parent paths only with child workflows as steps.
        2. Inline mode: Generates parent_paths × child_paths permutations showing
           complete end-to-end execution flow. Can cause exponential path growth.
        3. Subgraph mode: Generates separate path sets for each workflow (same as
           reference mode for path generation; rendering differs).

        The method enforces path explosion safeguards for inline mode by checking
        total_paths = parent_paths × child_paths before generation.

        Args:
            call_graph: WorkflowCallGraph from WorkflowCallGraphAnalyzer containing
                root workflow, child workflows, and call relationships.
            context: GraphBuildingContext for configuration including child_workflow_expansion mode.

        Returns:
            List of MultiWorkflowPath objects representing end-to-end execution paths.
            For reference/subgraph modes, returns one MultiWorkflowPath per parent path.
            For inline mode, returns parent_paths × child_paths MultiWorkflowPath objects.

        Raises:
            GraphGenerationError: If inline mode path explosion exceeds context.max_paths limit.
                Error message includes calculation breakdown showing parent × child = total.

        Example:
            >>> # Reference mode (default) - no path expansion
            >>> # Parent with 2 decisions, child with 2 decisions
            >>> call_graph = WorkflowCallGraph(...)
            >>> context = GraphBuildingContext()
            >>> generator = PathPermutationGenerator()
            >>> mw_paths = generator.generate_cross_workflow_paths(call_graph, context)
            >>> len(mw_paths)
            4  # Only parent paths (2^2), child not expanded

            >>> # Inline mode - full path expansion
            >>> context_inline = GraphBuildingContext(
            ...     child_workflow_expansion="inline"
            ... )
            >>> mw_paths = generator.generate_cross_workflow_paths(
            ...     call_graph, context_inline
            ... )
            >>> len(mw_paths)
            16  # Parent paths × child paths (4 × 4)
        """
        expansion_mode = context.child_workflow_expansion

        if expansion_mode == "reference":
            # Reference mode: treat child workflows as atomic nodes
            return self._generate_reference_mode_paths(call_graph, context)
        elif expansion_mode == "inline":
            # Inline mode: expand child workflows into parent paths
            return self._generate_inline_mode_paths(call_graph, context)
        elif expansion_mode == "subgraph":
            # Subgraph mode: same path generation as reference, different rendering
            return self._generate_subgraph_mode_paths(call_graph, context)
        else:
            raise ValueError(
                f"Invalid child_workflow_expansion mode: {expansion_mode}. "
                f"Expected 'reference', 'inline', or 'subgraph'."
            )

    def _generate_reference_mode_paths(
        self, call_graph: WorkflowCallGraph, context: GraphBuildingContext
    ) -> list[MultiWorkflowPath]:
        """Generate paths for reference mode (child workflows as atomic nodes).

        This is the simplest and safest mode. Child workflows appear as [[ChildWorkflow]]
        nodes in the parent workflow paths without any path expansion. No path explosion risk.

        Args:
            call_graph: WorkflowCallGraph containing root and child workflows.
            context: GraphBuildingContext for configuration.

        Returns:
            List of MultiWorkflowPath objects, one per parent path. Each path includes
            only the root workflow with child workflows as atomic steps.
        """
        # Generate parent workflow paths using existing generate_paths method
        parent_paths = self.generate_paths(call_graph.root_workflow, context)

        # Convert GraphPath objects to MultiWorkflowPath objects
        mw_paths: list[MultiWorkflowPath] = []
        for i, parent_path in enumerate(parent_paths):
            # Extract step names from PathStep objects
            step_names = [step.name for step in parent_path.steps]

            # In reference mode, only root workflow is included (no child expansion)
            mw_path = MultiWorkflowPath(
                path_id=f"mwpath_{i}",
                workflows=[call_graph.root_workflow.workflow_class],
                steps=step_names,
                workflow_transitions=[],  # No transitions in reference mode
                total_decisions=len(parent_path.decisions),
            )
            mw_paths.append(mw_path)

        logger.debug(
            f"Reference mode: Generated {len(mw_paths)} paths for root workflow "
            f"{call_graph.root_workflow.workflow_class}"
        )
        return mw_paths

    def _generate_inline_mode_paths(
        self, call_graph: WorkflowCallGraph, context: GraphBuildingContext
    ) -> list[MultiWorkflowPath]:
        """Generate paths for inline mode (full cross-workflow path expansion).

        This mode generates the cross-product of parent and child workflow paths,
        creating complete end-to-end execution flows. Path explosion safeguards
        are enforced BEFORE generation.

        Args:
            call_graph: WorkflowCallGraph containing root and child workflows.
            context: GraphBuildingContext for configuration.

        Returns:
            List of MultiWorkflowPath objects showing end-to-end execution across
            workflow boundaries. Count = parent_paths × child1_paths × child2_paths × ...

        Raises:
            GraphGenerationError: If total paths exceed context.max_paths limit.
        """
        # Generate parent workflow paths
        parent_paths = self.generate_paths(call_graph.root_workflow, context)

        # If no child workflows, return reference mode paths
        if not call_graph.child_workflows:
            logger.debug("Inline mode: No child workflows, using reference mode")
            return self._generate_reference_mode_paths(call_graph, context)

        # Calculate total paths BEFORE generation (path explosion safeguard)
        total_paths = len(parent_paths)
        child_path_counts: dict[str, int] = {}
        for child_name, child_metadata in call_graph.child_workflows.items():
            child_paths = self.generate_paths(child_metadata, context)
            child_path_counts[child_name] = len(child_paths)
            total_paths *= len(child_paths)

        # Check path explosion limit
        if total_paths > context.max_paths:
            # Build detailed error message
            breakdown = f"Parent ({len(parent_paths)} paths)"
            for child_name, count in child_path_counts.items():
                breakdown += f" × {child_name} ({count} paths)"
            breakdown += f" = {total_paths} total paths"

            raise GraphGenerationError(
                reason=(
                    f"Cross-workflow path explosion: {breakdown} "
                    f"exceeds limit {context.max_paths}. "
                    f"Use 'reference' mode or increase max_paths."
                ),
                context={
                    "parent_paths": len(parent_paths),
                    "child_path_counts": child_path_counts,
                    "total_paths": total_paths,
                    "limit": context.max_paths,
                    "expansion_mode": "inline",
                },
            )

        # Generate child workflow paths for all children
        child_paths_map: dict[str, list[GraphPath]] = {}
        for child_name, child_metadata in call_graph.child_workflows.items():
            child_paths_map[child_name] = self.generate_paths(child_metadata, context)

        # Expand parent paths with child workflow paths
        mw_paths: list[MultiWorkflowPath] = []
        mw_path_id = 0

        for parent_path in parent_paths:
            # Find child workflow call sites in this parent path
            child_call_sites: list[
                tuple[int, str, int]
            ] = []  # (step_index, workflow_name, line_number)
            for step_index, step in enumerate(parent_path.steps):
                if step.node_type == "child_workflow":
                    child_call_sites.append((step_index, step.name, step.line_number or 0))

            # If no child calls in this path, create simple MultiWorkflowPath
            if not child_call_sites:
                step_names = [step.name for step in parent_path.steps]
                mw_path = MultiWorkflowPath(
                    path_id=f"mwpath_{mw_path_id}",
                    workflows=[call_graph.root_workflow.workflow_class],
                    steps=step_names,
                    workflow_transitions=[],
                    total_decisions=len(parent_path.decisions),
                )
                mw_paths.append(mw_path)
                mw_path_id += 1
                continue

            # Expand this parent path with all child path combinations
            # For each child call site, get all possible child paths
            child_call_path_options: list[list[GraphPath]] = []
            for _, child_name, _ in child_call_sites:
                if child_name in child_paths_map:
                    child_call_path_options.append(child_paths_map[child_name])
                else:
                    # Child workflow not found in call graph, skip expansion
                    child_call_path_options.append([])

            # Generate cross-product of child path combinations
            if all(child_call_path_options):
                for child_path_combo in product(*child_call_path_options):
                    # Build end-to-end path by injecting child paths at call sites
                    end_to_end_steps: list[str] = []
                    workflows_traversed: list[str] = [call_graph.root_workflow.workflow_class]
                    transitions: list[tuple[int, str, str]] = []
                    total_decisions_count = len(parent_path.decisions)

                    current_step_index = 0

                    # Add parent steps before first child call
                    first_child_index = child_call_sites[0][0]
                    for i in range(first_child_index):
                        end_to_end_steps.append(parent_path.steps[i].name)
                        current_step_index += 1

                    # Inject each child workflow paths
                    for child_idx, (child_step_idx, child_name, _) in enumerate(child_call_sites):
                        child_path = child_path_combo[child_idx]

                        # Record transition from parent to child
                        transitions.append(
                            (
                                current_step_index,
                                call_graph.root_workflow.workflow_class,
                                child_name,
                            )
                        )
                        if child_name not in workflows_traversed:
                            workflows_traversed.append(child_name)

                        # Add child workflow steps
                        for child_step in child_path.steps:
                            end_to_end_steps.append(child_step.name)
                            current_step_index += 1
                        total_decisions_count += len(child_path.decisions)

                        # Record transition from child back to parent
                        transitions.append(
                            (
                                current_step_index,
                                child_name,
                                call_graph.root_workflow.workflow_class,
                            )
                        )

                        # Add parent steps between this child call and next (or end)
                        next_child_index = (
                            child_call_sites[child_idx + 1][0]
                            if child_idx + 1 < len(child_call_sites)
                            else len(parent_path.steps)
                        )
                        for i in range(child_step_idx + 1, next_child_index):
                            end_to_end_steps.append(parent_path.steps[i].name)
                            current_step_index += 1

                    # Create MultiWorkflowPath
                    mw_path = MultiWorkflowPath(
                        path_id=f"mwpath_{mw_path_id}",
                        workflows=workflows_traversed,
                        steps=end_to_end_steps,
                        workflow_transitions=transitions,
                        total_decisions=total_decisions_count,
                    )
                    mw_paths.append(mw_path)
                    mw_path_id += 1

        logger.debug(
            f"Inline mode: Generated {len(mw_paths)} end-to-end paths across "
            f"{call_graph.total_workflows} workflows"
        )
        return mw_paths

    def _generate_subgraph_mode_paths(
        self, call_graph: WorkflowCallGraph, context: GraphBuildingContext
    ) -> list[MultiWorkflowPath]:
        """Generate paths for subgraph mode (separate workflow path sets).

        Subgraph mode generates the same paths as reference mode but includes
        metadata for rendering as Mermaid subgraphs. The actual subgraph rendering
        happens in MermaidRenderer.

        Args:
            call_graph: WorkflowCallGraph containing root and child workflows.
            context: GraphBuildingContext for configuration.

        Returns:
            List of MultiWorkflowPath objects with workflow metadata for subgraph rendering.
        """
        # For now, subgraph mode uses same path generation as reference mode
        # Rendering differences are handled in MermaidRenderer
        return self._generate_reference_mode_paths(call_graph, context)
