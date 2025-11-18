"""Workflow with multiple sequential activity calls for testing."""

from temporalio import workflow


@workflow.defn
class MultiActivityWorkflow:
    """Workflow that calls multiple activities in sequence."""

    @workflow.run
    async def run(self) -> str:
        """Run the workflow."""
        result1 = await workflow.execute_activity(
            activity_one,
            start_to_close_timeout=None,
        )
        result2 = await workflow.execute_activity(
            activity_two,
            start_to_close_timeout=None,
        )
        result3 = await workflow.execute_activity(
            activity_three,
            start_to_close_timeout=None,
        )
        return f"{result1}-{result2}-{result3}"
