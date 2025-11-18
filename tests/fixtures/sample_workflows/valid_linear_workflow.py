"""Valid linear workflow for testing analyzer."""

from temporalio import workflow


@workflow.defn
class MyWorkflow:
    """Simple workflow with run method."""

    @workflow.run
    async def run(self, name: str) -> str:
        """Run the workflow."""
        return f"Hello {name}"
