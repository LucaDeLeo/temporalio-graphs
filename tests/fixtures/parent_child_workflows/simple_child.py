"""Simple child workflow for testing."""

from temporalio import workflow


@workflow.defn
class SimpleChildWorkflow:
    """A simple child workflow with no children of its own."""

    @workflow.run
    async def run(self) -> str:
        """Run the child workflow."""
        # Simple child workflow with no activity calls
        return "child_complete"
