"""Workflow with a single activity call for testing."""

from temporalio import workflow


@workflow.defn
class SingleActivityWorkflow:
    """Workflow that calls a single activity."""

    @workflow.run
    async def run(self) -> str:
        """Run the workflow."""
        result = await workflow.execute_activity(
            my_activity,
            start_to_close_timeout=None,
        )
        return result
