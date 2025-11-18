"""Workflow with activity calls using string literals for testing."""

from temporalio import workflow


@workflow.defn
class StringActivityWorkflow:
    """Workflow that calls activities using string names."""

    @workflow.run
    async def run(self) -> str:
        """Run the workflow."""
        result1 = await workflow.execute_activity(
            "validate_input",
            start_to_close_timeout=None,
        )
        result2 = await workflow.execute_activity(
            "process_data",
            start_to_close_timeout=None,
        )
        return f"{result1}-{result2}"
