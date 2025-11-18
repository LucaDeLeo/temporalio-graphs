"""Path generation for workflow graph construction.

This module provides the PathPermutationGenerator class which transforms
WorkflowMetadata (containing activity sequences and decision points) into
GraphPath objects representing execution paths through the workflow.

Epic 2 scope: Linear workflows only (0 decisions, single execution path).
Decision-based permutations (2^n paths) will be implemented in Epic 3.
"""

import logging

from temporalio_graphs._internal.graph_models import WorkflowMetadata
from temporalio_graphs.context import GraphBuildingContext
from temporalio_graphs.path import GraphPath

logger = logging.getLogger(__name__)


class PathPermutationGenerator:
    """Generates execution paths from workflow metadata.

    Transforms WorkflowMetadata (which contains activity sequences and decision
    points) into GraphPath objects suitable for Mermaid diagram rendering.

    For Epic 2, this class handles linear workflows (0 decision points) by
    creating a single execution path containing all activities in order.
    Future epics will extend this to generate 2^n paths for workflows with
    branching logic.

    The generator respects GraphBuildingContext configuration for node labeling
    and validates workflow constraints (e.g., no decision points in Epic 2).

    Example:
        >>> from pathlib import Path
        >>> from temporalio_graphs._internal.graph_models import WorkflowMetadata
        >>> from temporalio_graphs.context import GraphBuildingContext
        >>> from temporalio_graphs.generator import PathPermutationGenerator
        >>>
        >>> # Create workflow metadata for a simple linear workflow
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
        >>> # Generate paths using default context
        >>> generator = PathPermutationGenerator()
        >>> paths = generator.generate_paths(metadata, GraphBuildingContext())
        >>> assert len(paths) == 1
        >>> assert paths[0].path_id == "path_0"
        >>> assert paths[0].steps == ["ValidateInput", "ProcessOrder", "SendConfirmation"]
    """

    def generate_paths(
        self, metadata: WorkflowMetadata, context: GraphBuildingContext
    ) -> list[GraphPath]:
        """Generate execution paths from workflow metadata.

        For linear workflows (0 decision points), creates a single GraphPath
        containing all activities in sequential order. For workflows with
        decision points, raises NotImplementedError (deferred to Epic 3).

        This method performs validation on input parameters and raises
        informative errors for invalid inputs or unsupported workflow types.

        Args:
            metadata: WorkflowMetadata object from analyzer containing activity
                list and decision point count. Required.
            context: GraphBuildingContext configuration for graph generation
                (node labels, max decision points, etc.). Required.

        Returns:
            A list containing GraphPath objects representing execution paths
            through the workflow. For linear workflows (0 decisions), returns
            a list with exactly one GraphPath element.

        Raises:
            ValueError: If metadata is None or context is None. Provides
                actionable error messages with suggestions for fix.
            NotImplementedError: If workflow contains decision points (>0).
                Decision support is deferred to Epic 3. Error message indicates
                which epic will add this feature.

        Example:
            >>> import time
            >>> from pathlib import Path
            >>> from temporalio_graphs._internal.graph_models import WorkflowMetadata
            >>> from temporalio_graphs.context import GraphBuildingContext
            >>>
            >>> # Simple linear workflow
            >>> metadata = WorkflowMetadata(
            ...     workflow_class="PaymentWorkflow",
            ...     workflow_run_method="run",
            ...     activities=["Withdraw", "Deposit"],
            ...     decision_points=[],
            ...     signal_points=[],
            ...     source_file=Path("workflows.py"),
            ...     total_paths=1,
            ... )
            >>>
            >>> generator = PathPermutationGenerator()
            >>> ctx = GraphBuildingContext(
            ...     start_node_label="BEGIN",
            ...     end_node_label="FINISH"
            ... )
            >>>
            >>> # Time the generation for performance validation
            >>> start = time.perf_counter()
            >>> paths = generator.generate_paths(metadata, ctx)
            >>> elapsed = time.perf_counter() - start
            >>>
            >>> # Verify results
            >>> assert len(paths) == 1, "Linear workflows generate exactly 1 path"
            >>> assert paths[0].path_id == "path_0"
            >>> assert len(paths[0].steps) == 2
            >>> assert elapsed < 0.0001, f"Performance requirement: <0.1ms, got {elapsed*1000}ms"

        Notes:
            Start and End nodes are NOT included in path.steps. Renderer
            adds them implicitly when generating Mermaid output.

            Node IDs for activities are auto-generated by GraphPath.add_activity()
            in sequential order: "1", "2", "3", etc.

            Decision point support will be added in Epic 3 (Story 3.3).
            Signal point support will be added in Epic 4 (Story 4.x).
        """
        # Validate inputs
        if metadata is None:
            raise ValueError(
                "metadata cannot be None. Pass WorkflowMetadata from analyzer.analyze()."
            )

        if context is None:
            logger.debug("context is None, using GraphBuildingContext defaults")
            context = GraphBuildingContext()

        # Check for decision points (Epic 3 feature)
        if len(metadata.decision_points) > 0:
            raise NotImplementedError(
                f"Decision point support not in Epic 2. Workflow has "
                f"{len(metadata.decision_points)} decision points. "
                f"Decision handling will be added in Epic 3 (Story 3.3)."
            )

        # Log path generation start
        logger.debug(
            f"Generating paths for linear workflow with {len(metadata.activities)} activities"
        )

        # Create single linear path for Epic 2
        path = self._create_linear_path(metadata.activities)

        logger.debug(f"Created path with ID: {path.path_id}")

        return [path]

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
