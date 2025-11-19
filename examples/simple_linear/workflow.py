"""Simple linear workflow example for temporalio-graphs.

This example demonstrates a basic Temporal workflow with no decision points or
branching logic. The workflow executes a sequence of activities in order:

1. validate_input - Validate input data
2. process_data - Process the validated data
3. save_result - Save the processing result

This is the simplest form of a Temporal workflow, suitable for:
- Straightforward sequential processing
- Demonstrating temporalio-graphs capabilities
- Understanding how the library analyzes workflow structure
"""

from temporalio import workflow


@workflow.defn
class SimpleWorkflow:
    """A simple linear workflow with no decision points.

    This workflow executes three activities in a fixed sequence. There are no
    branches, decisions, or alternative paths - just a straightforward pipeline
    from start to end.

    Example usage (in actual Temporal client code):
        result = await client.execute_workflow(
            SimpleWorkflow.run,
            id="simple-workflow-1",
            task_queue="default",
        )
    """

    @workflow.run
    async def run(self) -> str:
        """Execute a sequence of activities in order.

        The run method is the entry point for the workflow. It defines the
        exact sequence of steps that will be executed.

        Returns:
            A completion message indicating success.
        """
        # Step 1: Validate the input
        await workflow.execute_activity(
            validate_input,
            start_to_close_timeout=None,
        )

        # Step 2: Process the data
        await workflow.execute_activity(
            process_data,
            start_to_close_timeout=None,
        )

        # Step 3: Save the result
        await workflow.execute_activity(
            save_result,
            start_to_close_timeout=None,
        )

        return "complete"


# Activity definitions (would normally be in a separate module)
# These are referenced in execute_activity() calls above


async def validate_input() -> bool:
    """Validate input data.

    This is a placeholder activity definition. In a real workflow, this would
    contain the actual business logic for validation.

    Returns:
        True if validation succeeds, False otherwise.
    """
    return True


async def process_data() -> dict:
    """Process the validated data.

    Another placeholder activity. Real implementation would process data
    according to business requirements.

    Returns:
        Dictionary containing processing results.
    """
    return {"status": "processed"}


async def save_result(result: dict) -> bool:
    """Save the processing result.

    Final placeholder activity for persisting results.

    Args:
        result: The result dictionary to save.

    Returns:
        True if save succeeds, False otherwise.
    """
    return True
