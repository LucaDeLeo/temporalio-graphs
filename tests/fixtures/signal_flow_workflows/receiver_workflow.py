"""Receiver workflow that handles signals from sender workflow.

Test fixture for integration tests - demonstrates basic signal handler.
"""

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class ReceiverWorkflow:
    """Workflow that receives signals and processes items."""

    def __init__(self) -> None:
        """Initialize workflow state."""
        self.should_process = False
        self.item_id: str | None = None

    @workflow.run
    async def run(self, receiver_id: str) -> str:
        """Execute receiver workflow.

        Args:
            receiver_id: Unique receiver identifier

        Returns:
            Processing completion status message
        """
        # Wait for process_item signal
        await workflow.wait_condition(
            lambda: self.should_process,
            timeout=timedelta(hours=24),
        )

        # Activity: Process item
        await workflow.execute_activity(
            "process_item_activity",
            args=[self.item_id],
            start_to_close_timeout=timedelta(minutes=5),
        )

        return "processed"

    @workflow.signal
    async def process_item(self, item_id: str) -> None:
        """Receive process_item signal from Sender workflow.

        Args:
            item_id: Item identifier to process
        """
        self.should_process = True
        self.item_id = item_id
