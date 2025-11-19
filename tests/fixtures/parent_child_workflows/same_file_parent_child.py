"""Parent and child in same file."""

from temporalio import workflow


@workflow.defn
class SameFileChildWorkflow:
    """Child workflow in same file as parent."""

    @workflow.run
    async def run(self) -> str:
        """Run child workflow."""
        return "same_file_child"


@workflow.defn
class SameFileParentWorkflow:
    """Parent workflow that calls child in same file."""

    @workflow.run
    async def run(self) -> str:
        """Run parent workflow."""
        result = await workflow.execute_child_workflow(SameFileChildWorkflow)
        return f"same_file_parent: {result}"
