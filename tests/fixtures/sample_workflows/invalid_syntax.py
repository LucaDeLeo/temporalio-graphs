"""Invalid Python syntax - should raise SyntaxError."""

from temporalio import workflow


@workflow.defn
class MyWorkflow:
    """Invalid syntax in workflow."""

    @workflow.run
    async def run(self, name: str) -> str:
        # Missing closing parenthesis - syntax error
        return f"Hello {name"
