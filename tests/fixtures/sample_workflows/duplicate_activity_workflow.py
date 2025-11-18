"""Workflow with duplicate activity calls for testing."""

from temporalio import workflow


@workflow.defn
class DuplicateActivityWorkflow:
    """Workflow that calls the same activity multiple times."""

    @workflow.run
    async def run(self) -> str:
        """Run the workflow."""
        result1 = await workflow.execute_activity(
            my_activity,
            start_to_close_timeout=None,
        )
        result2 = await workflow.execute_activity(
            my_activity,
            start_to_close_timeout=None,
        )
        return f"{result1}-{result2}"
