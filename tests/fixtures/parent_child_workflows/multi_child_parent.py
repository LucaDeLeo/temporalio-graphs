"""Parent workflow that calls multiple children."""

from temporalio import workflow
from tests.fixtures.parent_child_workflows.simple_child import SimpleChildWorkflow


@workflow.defn
class ChildWorkflowA:
    """First child workflow."""

    @workflow.run
    async def run(self) -> str:
        """Run child A."""
        return "child_a_complete"


@workflow.defn
class ChildWorkflowB:
    """Second child workflow."""

    @workflow.run
    async def run(self) -> str:
        """Run child B."""
        return "child_b_complete"


@workflow.defn
class MultiChildParentWorkflow:
    """A parent workflow that calls multiple children."""

    @workflow.run
    async def run(self) -> str:
        """Run the parent workflow with multiple children."""
        # Call two different child workflows
        result_a = await workflow.execute_child_workflow(ChildWorkflowA)
        result_b = await workflow.execute_child_workflow(ChildWorkflowB)
        return f"parent: {result_a}, {result_b}"
