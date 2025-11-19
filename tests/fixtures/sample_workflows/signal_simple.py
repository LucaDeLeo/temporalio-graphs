"""Simple workflow with single wait_condition() call for signal detection testing."""

from datetime import timedelta
from temporalio import workflow


# Placeholder for wait_condition (will be implemented in Story 4.2)
async def wait_condition(condition, timeout, name):
    """Placeholder wait_condition for testing."""
    pass


async def submit_request():
    """Placeholder activity."""
    pass


async def process_approved():
    """Placeholder activity."""
    pass


async def handle_timeout():
    """Placeholder activity."""
    pass


@workflow.defn
class SimpleSignalWorkflow:
    """Workflow with single signal point for testing."""

    def __init__(self) -> None:
        self.approved = False

    @workflow.run
    async def run(self) -> str:
        """Run workflow with signal wait."""
        # Submit approval request
        await workflow.execute_activity(
            submit_request, schedule_to_close_timeout=timedelta(seconds=30)
        )

        # Wait for approval signal (24 hour timeout)
        result = await wait_condition(
            lambda: self.approved, timedelta(hours=24), "WaitForApproval"
        )

        if result:
            await workflow.execute_activity(
                process_approved, schedule_to_close_timeout=timedelta(seconds=30)
            )
        else:
            await workflow.execute_activity(
                handle_timeout, schedule_to_close_timeout=timedelta(seconds=30)
            )

        return "complete"
