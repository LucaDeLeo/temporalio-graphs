"""Workflow with multiple wait_condition() calls for signal detection testing."""

from datetime import timedelta
from temporalio import workflow


# Placeholder for wait_condition (will be implemented in Story 4.2)
async def wait_condition(condition, timeout, name):
    """Placeholder wait_condition for testing."""
    pass


async def submit_request():
    """Placeholder activity."""
    pass


async def process_first_approval():
    """Placeholder activity."""
    pass


async def process_second_approval():
    """Placeholder activity."""
    pass


async def finalize():
    """Placeholder activity."""
    pass


@workflow.defn
class MultipleSignalWorkflow:
    """Workflow with multiple signal points for testing."""

    def __init__(self) -> None:
        self.first_approved = False
        self.second_approved = False

    @workflow.run
    async def run(self) -> str:
        """Run workflow with multiple signal waits."""
        # Submit request
        await workflow.execute_activity(
            submit_request, schedule_to_close_timeout=timedelta(seconds=30)
        )

        # First approval wait
        first_result = await wait_condition(
            lambda: self.first_approved, timedelta(hours=12), "WaitForFirstApproval"
        )

        if first_result:
            await workflow.execute_activity(
                process_first_approval, schedule_to_close_timeout=timedelta(seconds=30)
            )

        # Second approval wait
        second_result = await wait_condition(
            lambda: self.second_approved, timedelta(hours=24), "WaitForSecondApproval"
        )

        if second_result:
            await workflow.execute_activity(
                process_second_approval, schedule_to_close_timeout=timedelta(seconds=30)
            )

        # Finalize
        await workflow.execute_activity(
            finalize, schedule_to_close_timeout=timedelta(seconds=30)
        )

        return "complete"
