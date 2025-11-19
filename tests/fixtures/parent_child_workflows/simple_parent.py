"""Simple parent workflow that calls one child."""

from temporalio import workflow
from tests.fixtures.parent_child_workflows.simple_child import SimpleChildWorkflow


@workflow.defn
class SimpleParentWorkflow:
    """A parent workflow that calls one child workflow."""

    @workflow.run
    async def run(self) -> str:
        """Run the parent workflow."""
        # Call child workflow
        result = await workflow.execute_child_workflow(SimpleChildWorkflow)
        return f"parent_complete: {result}"
