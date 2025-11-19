"""Simple workflow with a single decision point."""

from temporalio import workflow, activity


@activity.defn
async def validate_amount(amount: int) -> bool:
    """Validate if amount is valid."""
    return amount > 0


@workflow.defn
class SingleDecisionWorkflow:
    """Workflow with one decision point."""

    @workflow.run
    async def run(self, amount: int = 100) -> str:
        """Run workflow with single decision."""
        await workflow.execute_activity(
            validate_amount, amount, schedule_to_close_timeout=600
        )

        if await to_decision(amount > 1000, "HighValue"):
            return "High value amount"
        else:
            return "Low value amount"


async def to_decision(condition: bool, name: str) -> bool:
    """Mark a decision point in workflow."""
    return condition
