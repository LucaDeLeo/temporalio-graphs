"""Workflow with ternary operator wrapped in to_decision()."""

from temporalio import workflow, activity


@activity.defn
async def process(value: int) -> bool:
    """Process value."""
    return True


@workflow.defn
class TernaryWorkflow:
    """Workflow with ternary operator in decision."""

    @workflow.run
    async def run(self, amount: int = 100) -> str:
        """Run workflow with ternary operator."""
        result = await to_decision(
            amount if amount > 1000 else 0, "ConditionalAmount"
        )

        if result > 500:
            await workflow.execute_activity(process, result)
            return "High"
        else:
            return "Low"


async def to_decision(condition: int, name: str) -> int:
    """Mark a decision point in workflow."""
    return condition
