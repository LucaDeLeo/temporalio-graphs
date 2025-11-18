"""Workflow missing @workflow.defn decorator - should raise error."""

from temporalio import workflow


class MyWorkflow:
    """Class without @workflow.defn decorator."""

    @workflow.run
    async def run(self, name: str) -> str:
        """Run method without workflow decorator on class."""
        return f"Hello {name}"
