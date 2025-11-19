"""Circular workflow A (calls B which calls A)."""

from temporalio import workflow


# Forward reference to avoid import issues
@workflow.defn
class CircularWorkflowA:
    """Workflow A that calls workflow B."""

    @workflow.run
    async def run(self) -> str:
        """Run workflow A."""
        # Import here to avoid circular import at module level
        from tests.fixtures.parent_child_workflows.circular_b import CircularWorkflowB

        result = await workflow.execute_child_workflow(CircularWorkflowB)
        return f"a: {result}"
