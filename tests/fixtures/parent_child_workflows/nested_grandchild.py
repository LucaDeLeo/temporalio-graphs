"""Nested workflow hierarchy with grandchild."""

from temporalio import workflow


@workflow.defn
class GrandchildWorkflow:
    """A grandchild workflow (depth 2)."""

    @workflow.run
    async def run(self) -> str:
        """Run the grandchild workflow."""
        return "grandchild_complete"


@workflow.defn
class ChildWithGrandchildWorkflow:
    """A child workflow that calls a grandchild."""

    @workflow.run
    async def run(self) -> str:
        """Run the child workflow."""
        result = await workflow.execute_child_workflow(GrandchildWorkflow)
        return f"child: {result}"


@workflow.defn
class ParentWithGrandchildWorkflow:
    """A parent workflow that calls a child with grandchild."""

    @workflow.run
    async def run(self) -> str:
        """Run the parent workflow."""
        result = await workflow.execute_child_workflow(ChildWithGrandchildWorkflow)
        return f"parent: {result}"
