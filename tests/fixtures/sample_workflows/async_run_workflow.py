"""Workflow with async run method."""

from temporalio import workflow


@workflow.defn
class AsyncWorkflow:
    """Workflow with async run method."""

    @workflow.run
    async def run(self, name: str) -> str:
        """Async run method."""
        return f"Hello async {name}"
