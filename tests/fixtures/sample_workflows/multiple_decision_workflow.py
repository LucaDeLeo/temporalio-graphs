"""Workflow with multiple decision points."""

from temporalio import workflow, activity


@activity.defn
async def process_order(amount: int) -> bool:
    """Process order."""
    return True


@workflow.defn
class MultipleDecisionWorkflow:
    """Workflow with multiple decision points."""

    @workflow.run
    async def run(self, amount: int = 100, is_international: bool = False) -> str:
        """Run workflow with multiple decisions."""
        await workflow.execute_activity(process_order, amount)

        if await to_decision(amount > 1000, "HighValue"):
            await workflow.execute_activity(process_order, amount)

        if await to_decision(is_international, "InternationalOrder"):
            await workflow.execute_activity(process_order, amount)

        return "Order processed"


async def to_decision(condition: bool, name: str) -> bool:
    """Mark a decision point in workflow."""
    return condition
