"""Workflow missing @workflow.run method - should raise error."""

from temporalio import workflow


@workflow.defn
class MyWorkflow:
    """Workflow class without @workflow.run method."""

    async def some_other_method(self, name: str) -> str:
        """Some other method, not the run method."""
        return f"Hello {name}"
