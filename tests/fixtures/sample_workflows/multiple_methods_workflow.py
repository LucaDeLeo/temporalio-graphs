"""Workflow with multiple methods - only run method should be detected."""

from temporalio import workflow


@workflow.defn
class MyWorkflow:
    """Workflow with multiple methods."""

    def __init__(self) -> None:
        """Initialize workflow."""
        self.counter = 0

    async def helper_method(self, value: int) -> int:
        """Helper method, not a run method."""
        return value * 2

    @workflow.run
    async def run(self, name: str) -> str:
        """Run the workflow."""
        return f"Hello {name}"

    async def another_helper(self) -> None:
        """Another helper method."""
        pass
