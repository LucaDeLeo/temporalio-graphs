"""Sender workflow that sends signals to a non-existent handler.

Test fixture for integration tests - demonstrates unresolved signal handling.
The target workflow "NonExistentWorkflow" does not have a matching signal handler.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class UnresolvedSenderWorkflow:
    """Workflow that sends signal to non-existent target."""

    @workflow.run
    async def run(self, order_id: str) -> str:
        """Execute unresolved sender workflow.

        Args:
            order_id: Unique order identifier

        Returns:
            Completion status message
        """
        # Activity: Prepare data
        await workflow.execute_activity(
            "prepare_data",
            args=[order_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # External signal: Send to non-existent workflow
        # This should result in an unresolved signal in the graph
        missing_handle = workflow.get_external_workflow_handle(
            "NonExistentWorkflow",
            workflow_id=f"missing-{order_id}",
        )
        await missing_handle.signal("missing_signal", order_id)

        return "sent"
