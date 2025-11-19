"""Workflow with elif chain - multiple decisions."""

from temporalio import workflow, activity


@activity.defn
async def process(value: int) -> bool:
    """Process value."""
    return True


@workflow.defn
class ElifChainWorkflow:
    """Workflow with elif chain creating multiple decision points."""

    @workflow.run
    async def run(self, value: int = 50) -> str:
        """Run workflow with elif chain."""
        if await to_decision(value < 100, "LowValue"):
            await workflow.execute_activity(process, value)
            return "Low"
        elif await to_decision(value < 500, "MediumValue"):
            await workflow.execute_activity(process, value)
            return "Medium"
        elif await to_decision(value < 1000, "HighValue"):
            await workflow.execute_activity(process, value)
            return "High"
        else:
            return "VeryHigh"


async def to_decision(condition: bool, name: str) -> bool:
    """Mark a decision point in workflow."""
    return condition
