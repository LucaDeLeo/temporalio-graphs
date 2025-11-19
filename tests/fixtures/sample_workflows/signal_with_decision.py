"""Workflow with both signal and decision nodes for testing."""

from datetime import timedelta
from temporalio import workflow


# Placeholder for wait_condition (will be implemented in Story 4.2)
async def wait_condition(condition, timeout, name):
    """Placeholder wait_condition for testing."""
    pass


# Placeholder for to_decision (implemented in Story 3.2)
async def to_decision(result, name):
    """Placeholder to_decision for testing."""
    return result


async def submit_request():
    """Placeholder activity."""
    pass


async def quick_process():
    """Placeholder activity."""
    pass


async def standard_process():
    """Placeholder activity."""
    pass


async def handle_timeout():
    """Placeholder activity."""
    pass


@workflow.defn
class SignalWithDecisionWorkflow:
    """Workflow with both signal and decision points for testing."""

    def __init__(self) -> None:
        self.approved = False
        self.amount = 0

    @workflow.run
    async def run(self, amount: int) -> str:
        """Run workflow with signal and decision."""
        self.amount = amount

        # Submit request
        await workflow.execute_activity(
            submit_request, schedule_to_close_timeout=timedelta(seconds=30)
        )

        # Wait for approval signal
        result = await wait_condition(
            lambda: self.approved, timedelta(hours=24), "WaitForApproval"
        )

        if result:
            # Decision based on amount
            if await to_decision(amount > 1000, "HighValue"):
                await workflow.execute_activity(
                    standard_process, schedule_to_close_timeout=timedelta(seconds=30)
                )
            else:
                await workflow.execute_activity(
                    quick_process, schedule_to_close_timeout=timedelta(seconds=30)
                )
        else:
            await workflow.execute_activity(
                handle_timeout, schedule_to_close_timeout=timedelta(seconds=30)
            )

        return "complete"
