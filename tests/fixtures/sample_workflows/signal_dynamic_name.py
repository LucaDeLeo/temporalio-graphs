"""Workflow with dynamic signal name (variable instead of string literal) for testing."""

from datetime import timedelta
from temporalio import workflow


# Placeholder for wait_condition (will be implemented in Story 4.2)
async def wait_condition(condition, timeout, name):
    """Placeholder wait_condition for testing."""
    pass


async def submit_request():
    """Placeholder activity."""
    pass


async def process_result():
    """Placeholder activity."""
    pass


@workflow.defn
class DynamicSignalNameWorkflow:
    """Workflow with dynamic signal name for testing warning case."""

    def __init__(self) -> None:
        self.approved = False

    @workflow.run
    async def run(self, signal_name: str) -> str:
        """Run workflow with dynamic signal name."""
        # Submit request
        await workflow.execute_activity(
            submit_request, schedule_to_close_timeout=timedelta(seconds=30)
        )

        # Wait with dynamic name (should trigger warning and use "UnnamedSignal")
        result = await wait_condition(
            lambda: self.approved, timedelta(hours=24), signal_name
        )

        if result:
            await workflow.execute_activity(
                process_result, schedule_to_close_timeout=timedelta(seconds=30)
            )

        return "complete"
