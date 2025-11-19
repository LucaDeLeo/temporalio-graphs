"""Workflow with malformed to_decision() calls for error testing."""

from temporalio import workflow


@workflow.defn
class MalformedDecisionWorkflow:
    """Workflow with malformed decision calls."""

    @workflow.run
    async def run(self) -> str:
        """Run workflow with malformed decisions."""
        # This will be used for error testing - not valid Python when executed
        # but valid AST for parsing
        return "test"
