"""Path generation for workflow graph construction.

This module provides the PathPermutationGenerator class which transforms
WorkflowMetadata (containing activity sequences and decision points) into
GraphPath objects representing execution paths through the workflow.

Epic 2 scope: Linear workflows only (0 decisions, single execution path).
Epic 3 scope: Decision-based permutations (2^n paths for n decision points).
"""

import logging
from itertools import product

from temporalio_graphs._internal.graph_models import DecisionPoint, WorkflowMetadata
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

        # Check for decision points and explosion limit
        num_decisions = len(metadata.decision_points)

        # Validate explosion limit
        if num_decisions > context.max_decision_points:
            paths_count = 2**num_decisions
            raise GraphGenerationError(
                f"Too many decision points ({num_decisions}) would generate "
                f"{paths_count} paths (limit: {context.max_decision_points}). "
                f"Suggestion: Refactor workflow or increase max_decision_points limit"
            )

        # Log path generation start
        if num_decisions == 0:
            logger.debug(
                f"Generating paths for linear workflow with {len(metadata.activities)} activities"
            )
            # Create single linear path for linear workflows
            path = self._create_linear_path(metadata.activities)
            logger.debug(f"Created path with ID: {path.path_id}")
            return [path]
        else:
            logger.debug(
                f"Generating {2**num_decisions} paths for workflow with "
                f"{num_decisions} decision points and {len(metadata.activities)} activities"
            )
            # Generate permutations for workflows with decisions
            paths = self._generate_paths_with_decisions(
                metadata.decision_points, metadata.activities, context
            )
            logger.debug(
                f"Generated {len(paths)} paths for workflow with {num_decisions} decisions"
            )
            return paths

    def _create_linear_path(self, activities: list[str]) -> GraphPath:
        """Create a single linear path from activity sequence.

        Helper method that constructs a GraphPath with all activities in order.
        This implements the Epic 2 algorithm: create path with path_id="path_0",
        add each activity sequentially, return the path.

        Args:
            activities: List of activity names in order from workflow analysis.
                May be empty for workflows with no activities.

        Returns:
            GraphPath with path_id="path_0" and all activities added in order
            via add_activity() calls.
        """
        path = GraphPath(path_id="path_0")

        # Add all activities in sequence
        for activity_name in activities:
            path.add_activity(activity_name)

        return path

    def _generate_paths_with_decisions(
        self,
        decisions: list[DecisionPoint],
        activities: list[str],
        context: GraphBuildingContext,
    ) -> list[GraphPath]:
        """Generate 2^n execution paths for workflows with decision points.

        Uses itertools.product to efficiently generate all 2^n boolean combinations
        for the given decision points. For each combination, creates a GraphPath
        that records the decisions and activities in order.

        This method implements the Epic 3 path permutation algorithm using the
        efficient C-optimized itertools.product function, maintaining O(2^n)
        time complexity while avoiding manual recursion.

        Args:
            decisions: List of DecisionPoint objects from workflow analysis.
            activities: List of activity names from workflow analysis.
            context: GraphBuildingContext for configuration (branch labels, etc.).

        Returns:
            List of GraphPath objects, one for each 2^n permutation. Each path
            contains the activities and decisions for that specific execution path.

        Example:
            >>> decisions = [
            ...     DecisionPoint("d0", "NeedConvert", 42, "yes", "no"),
            ...     DecisionPoint("d1", "HighValue", 55, "yes", "no"),
            ... ]
            >>> activities = ["Withdraw", "CurrencyConvert", "Deposit"]
            >>> context = GraphBuildingContext()
            >>> gen = PathPermutationGenerator()
            >>> paths = gen._generate_paths_with_decisions(decisions, activities, context)
            >>> len(paths)
            4
            >>> # Each path should have a unique decision combination
            >>> for path in paths:
            ...     assert len(path.decisions) == 2
            ...     assert all(isinstance(v, bool) for v in path.decisions.values())
        """
        num_decisions = len(decisions)
        paths: list[GraphPath] = []

        # Generate all 2^n boolean combinations using itertools.product
        for path_index, decision_values in enumerate(
            product([False, True], repeat=num_decisions)
        ):
            # Create path ID in binary format for clarity
            # path_0b00, path_0b01, path_0b10, path_0b11, etc.
            binary_str = "".join(str(int(v)) for v in decision_values)
            path_id = f"path_0b{binary_str}"

            # Create new path for this permutation
            path = GraphPath(path_id=path_id)

            # Add decisions and activities in sequence
            # Simplified approach: add all activities first, then decisions
            # (In a real scenario with nested decisions, this would be more complex)
            for activity_name in activities:
                path.add_activity(activity_name)

            # Record decision values in the path
            for decision, value in zip(decisions, decision_values):
                path.add_decision(decision.id, value, decision.name)

            paths.append(path)

        return paths
