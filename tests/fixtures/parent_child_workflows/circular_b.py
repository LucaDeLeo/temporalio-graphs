"""Circular workflow B (calls A which calls B)."""

from temporalio import workflow


@workflow.defn
class CircularWorkflowB:
    """Workflow B that calls workflow A (creates circular dependency)."""

    @workflow.run
    async def run(self) -> str:
        """Run workflow B."""
        # Import here to avoid circular import at module level
        from tests.fixtures.parent_child_workflows.circular_a import CircularWorkflowA

        result = await workflow.execute_child_workflow(CircularWorkflowA)
        return f"b: {result}"
