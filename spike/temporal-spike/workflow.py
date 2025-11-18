"""Spike test workflow with branching logic."""
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import withdraw, approve, deposit


@workflow.defn
class SpikeTestWorkflow:
    """Test workflow with conditional branching."""

    @workflow.run
    async def run(self, amount: int) -> str:
        """Execute workflow with amount-based branching."""
        # Step 1: Withdraw
        await workflow.execute_activity(
            withdraw,
            args=[amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        # Step 2: Conditional approval
        needs_approval = amount > 1000
        if needs_approval:
            await workflow.execute_activity(
                approve,
                args=[amount],
                start_to_close_timeout=timedelta(seconds=10),
            )

        # Step 3: Deposit
        await workflow.execute_activity(
            deposit,
            args=[amount],
            start_to_close_timeout=timedelta(seconds=10),
        )

        return "complete"
