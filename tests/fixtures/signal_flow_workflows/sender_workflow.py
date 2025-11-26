"""Sender workflow that sends external signals to a receiver.

Test fixture for integration tests - demonstrates basic external signal sending.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class SenderWorkflow:
    """Workflow that sends external signal to another workflow."""

    @workflow.run
    async def run(self, order_id: str) -> str:
        """Execute sender workflow.

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

        # External signal: Notify receiver workflow
        receiver_handle = workflow.get_external_workflow_handle(
            "ReceiverWorkflow",
            workflow_id=f"receiver-{order_id}",
        )
        await receiver_handle.signal("process_item", order_id)

        return "sent"
